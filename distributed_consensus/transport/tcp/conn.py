import asyncio
import random
import typing
from binascii import b2a_hex
from logging import getLogger

from ...core.node import Node
from ...core.node_manager import NodeManager
from ...queue.manager import PacketQueue, QueueManager
from .protocol import TCPProtocolV1

L = getLogger(__name__)


class TCPConnectionHandler:
    local_node: Node
    node_manager: NodeManager
    queue_manager: QueueManager
    protocol_class: typing.Type[TCPProtocolV1]
    pending_nodes: typing.Set[Node]
    pending_connectors: typing.Set[asyncio.Task]
    # 信号量标志
    nodes_incoming: asyncio.Semaphore
    server: typing.Optional[asyncio.AbstractServer]

    loop: asyncio.BaseEventLoop
    def __init__(
        self,
        local_node: Node,
        node_manager: NodeManager,
        queue_manager: QueueManager,
        protocol_class: typing.Type[TCPProtocolV1],
        loop: asyncio.BaseEventLoop
    ):
        super().__init__()
        self.local_node = local_node
        self.node_manager = node_manager
        self.queue_manager = queue_manager
        self.protocol_class = protocol_class
        self.logger = L.getChild('TCPConnectionHandler').getChild(
            f'{local_node.id}'
        )
        self.pending_nodes = set()
        self.pending_connectors = set()
        self.nodes_incoming = asyncio.Semaphore(0)
        self.loop = loop
    async def send_handshake(
        self, writer: asyncio.StreamWriter, protocol: TCPProtocolV1,
    ):
        #回复握手
        writer.write(protocol.generate_handshake())
        # writer.drain就是等待sock把缓冲区的数据发送出去
        try:
            await asyncio.wait_for(writer.drain(), protocol.handshake_timeout)
        except asyncio.TimeoutError:
            self.logger.error(
                'sending handshake to remote %s timeout',
                writer.get_extra_info('peername'),
            )
            return False
        return True

    async def wait_handshake(
        self, reader: asyncio.StreamReader, protocol: TCPProtocolV1
    ) -> typing.Optional[Node]:
        bs = b''
        try:
            bs = await asyncio.wait_for(
                reader.readexactly(protocol.handshake_recv_len),
                timeout=protocol.handshake_timeout,
            )
        except asyncio.TimeoutError:
            self.logger.error('recv handshake from remote timeout',)
            return None
        except asyncio.IncompleteReadError as ex:
            self.logger.error(
                'recv handshake receive early EOF, got: %s',
                b2a_hex(ex.partial),
            )
            return None
        remote = protocol.parse_handshake(bs)
        return remote

    def is_remote_valid(self, remote: typing.Optional[Node]) -> bool:
        ok = True
        if remote is None:
            self.logger.warn(f'remote is None')
            ok = False
        elif remote.is_blacked:
            self.logger.warn(f'remote {remote.name} is blocked, disconnect')
            ok = False
        elif self.local_node.pure_normal and remote.pure_normal:
            self.logger.warn(
                f'both local and {remote.name} are pure normal node, disconnect'
            )
            ok = False
        return ok
    # client和server都是从该方法来处理socket数据的接收和发送
    # client会传输remote参数进来
    async def add_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        remote: typing.Optional[Node] = None,
    ):
        """ schedule a dispatching task for given connection

            remote(optional): the remote node. if None, wait for remote to
            initiate handshake procedure to know its identity. Otherwise use
            given remote node identity and initiate handshake from local side
        """
        ok: bool = False
        protocol = self.protocol_class(
            self.node_manager, self.local_node, remote
        )
        self.logger.info(
            'add connection from %s to %s (%s)',
            self.local_node.name,
            remote.name if remote is not None else 'unknown',
            writer.get_extra_info('peername'),
        )
        # add_connection 作为server回调的时候，remote是None的
        # 当在其他地方调用的时候，会传递remote过来，这时应该不是None的
        if remote is None:
            remote = await self.wait_handshake(reader, protocol)
            ok = self.is_remote_valid(remote)
        else:
            # assert 用于判断一个表达式，在表达式条件为 false 的时候触发异常。
            assert self.is_remote_valid(remote)  # should be a bug
            ok = await self.send_handshake(writer, protocol) # 发送
        if not ok:
            self.logger.warn('handshake failed or invalid remote, drop')
            writer.close()
            await writer.wait_closed()
        else:
            assert remote is not None
            if remote in self.pending_nodes:
                # pending_nodes存储的是未连接（等待）状态的节点
                # 当节点连接进来时，进行移除操作
                self.pending_nodes.remove(remote)
                # 释放信号量
                self.nodes_incoming.release()
            asyncio.create_task(
                self.dispatch(remote, reader, writer, protocol)
            )

    async def dispatch(
        self,
        remote: Node,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        protocol: TCPProtocolV1,
    ):
        ingress, egress = self.queue_manager.create_queue(remote)
        try:
            # 使用data_loop来读写socket
            # ingress 和egress都是来自QueueManager，在这个类对象里面缓存处理数据，需要发送的数据也是丢进egress中，然后在data_loop中获取发送。
            # data_loop里只是进行数据的收、发工作
            await self.data_loop(ingress, egress, reader, writer, protocol)
        except asyncio.CancelledError:
            self.logger.info(
                f'{remote.name} data loop exited due to initiative close'
            )
        except asyncio.IncompleteReadError:
            self.logger.warn(
                f'{remote.name} data loop exited due to disconnection'
            )
            if remote.is_delegate and remote > self.local_node:
                self.logger.info(
                    f'{remote.name} delegate disconnection, try reconnecting'
                )
                self.connect_in_background(remote)
            else:
                self.logger.info(
                    f'{remote.name} disconnection, expect incoming reconnection'
                )
        except:  # noqa
            self.logger.warn('data loop exited with exception', exc_info=True)
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            self.queue_manager.close(remote)

    async def data_loop(
        self,
        ingress: PacketQueue,
        egress: PacketQueue,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        protocol: TCPProtocolV1,
    ):
        def out_task():
            return asyncio.create_task(
                egress.get(), name=f'send-{protocol.remote.id}'
            )

        def in_task():
            return asyncio.create_task(
                reader.readexactly(protocol.num_to_read()),
                name=f'recv-{protocol.remote.name}',
            )

        def retrieve_exception_cb(task: asyncio.Task):
            """ retrieve potential result/exception from orphan tasks """
            try:
                result = task.result()
                self.logger.debug(
                    f'orphan task {task!r} done with {result}'
                )
            except:
                self.logger.debug(
                    f'orphan task {task!r} got exception', exc_info=True
                )

        outbound = out_task()
        inbound = in_task()
        closing = False
        while not closing:
            done, pending = await asyncio.wait(
                {outbound, inbound}, return_when=asyncio.FIRST_COMPLETED
            )
            if outbound in done:
                try:
                    to_send = outbound.result()
                except asyncio.CancelledError:
                    closing = True
                else:
                    to_send = protocol.encode(to_send)
                    writer.write(to_send)
                    # self.logger.debug(f'send {b2a_hex(to_send)!s}')
                    outbound = out_task()
            if inbound in done:
                try:
                    bs = inbound.result()
                except asyncio.IncompleteReadError as ex:
                    self.logger.info('remote closing connection.')
                    bs = ex.partial
                    closing = True
                # self.logger.debug(f'received {b2a_hex(bs)!s}')

                while True:
                    pkt,origin_id,verify = protocol.decode(bs)
                    bs = b''
                    if pkt is None and verify:
                        assert (
                            protocol.num_to_read() > 0
                        ), 'cannot consume buffer'
                        break
                    elif pkt is None and not verify:
                        # 接收到数据，但是数据签名验证异常
                        # 
                        self.closing(origin_id)
                        break
                    else:
                        await ingress.put(pkt)
                    # in case multiple packets received in one reading,
                    # parse as many packets as possible
                    if protocol.num_to_read() > 0:
                        break
                if not closing:
                    inbound = in_task()
        for t in [inbound, outbound]:
            if not t.done():
                # add callback to eliminate "exception not retrieve" error
                t.add_done_callback(retrieve_exception_cb)

    async def connect_to(self, node: Node, retry=None):
        wait = 1.0
        while True:
            try:
                reader, writer = await asyncio.open_connection(
                    node.ip, node.port
                )
                break
            except:  # noqa
                self.logger.warn(
                    f'connect to node {node.name} {node.ip}:{node.port} failed',
                    exc_info=True,
                )
            if retry is not None:
                if retry > 0:
                    retry -= 1
                else:
                    self.logger.error(
                        f'fail to connect {node.name} {node.ip}:{node.port}'
                    )
                    return
            if wait < 30:
                wait = int(wait) * 2 + random.random()
            else:
                wait = 30 + random.random()
            self.logger.info(
                f'retry connecting node {node.name} in {wait:.3f} seconds'
            )
            await asyncio.sleep(wait)

        await self.add_connection(reader, writer, node)

    def connect_in_background(self, node: Node) -> asyncio.Task:
        task = asyncio.create_task(self.connect_to(node))
        self.pending_connectors.add(task)
        return task

    async def listen_from(self, node: Node = None) -> asyncio.AbstractServer:
        node = self.local_node if node is None else node
        # add_connection为回调 start_server和其他语言的模式有点区别，并不会同一个连接多次触发回调。
        # add_connection回调只在连接的时候触发，后续读取和写入操作使用reader和writer来进行。
        server = await asyncio.start_server(
            self.add_connection, node.ip, node.port
        )
        self.server = server
        return server

    async def wait_micronet_up(self, event: asyncio.Event):
        while True:
            # 等待信号量
            await self.nodes_incoming.acquire()
            # 当数组为空时，数组/set 值被隐式地赋为False
            # not self.pending_nodes为true表示数组为空 
            # 也就是所有的节点都连接进来时，释放信号
            if not self.pending_nodes:
                event.set()
                break
        await self.clean_background_connector()

    async def setup_micronet(self) -> asyncio.Event:
        micronet_ok = asyncio.Event()
        self.nodes_incoming = asyncio.Semaphore(0)
        """if self.local_node.pure_normal():
            return micronet_ok
        """
        should_connect: bool = False
        # 开启服务
        await self.listen_from()

        all_nodes = [
            node
            for node in self.node_manager.nodes()
            if isinstance(node, Node)
        ]
        # 连接其他代表
        for node in sorted(all_nodes):
            if node is self.local_node:
                self.logger.debug(f'node {node.name} is local, continue')
                # meet local node in sorted node list, should connect to
                # following nodes
                # self.connect_in_background(node)
                # self.pending_nodes.add(node)
                should_connect = True
            elif self.local_node.pure_normal and node.pure_normal:
                self.logger.debug(
                    f'both local and {node.name} are pure normal node, continue'
                )
            elif should_connect:
                self.logger.debug(f'connect to node {node.id}')
                self.connect_in_background(node)
                self.pending_nodes.add(node)
            else:
                self.logger.debug(f'expect node {node.name} to connect')
                self.pending_nodes.add(node)
        # wait_micronet_up(micronet_ok)等待微网启动(连接进来)并释放信号
        asyncio.create_task(self.wait_micronet_up(micronet_ok))

        return micronet_ok

    async def setup_and_wait_micronet(self, timeout: float) -> bool:
        # 启动微网
        event = await self.setup_micronet()
        try:
            # event.wait() 等待信号
            return await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error('setup micronet timeout')
            await self.tear_down_micronet()
        return False

    async def clean_background_connector(self, cancel_all=False):
        self.logger.debug(f'background connector {self.pending_connectors}')
        if cancel_all:
            self.logger.debug(f'cancel all connectors')
            for task in self.pending_connectors:
                if not task.cancelled:
                    self.logger.debug(f'cancel task {task}')
                    task.cancel()

        done = {task for task in self.pending_connectors if task.done()}
        self.logger.debug(f'completed connector {done}')
        for task in done:
            self.pending_connectors.remove(task)
            if task.cancelled():
                self.logger.debug(f'task {task} already cancelled')
                continue
            elif task.done():
                try:
                    self.logger.debug(
                        f'task {task} done with result {task.result()}'
                    )
                except:  # noqa
                    self.logger.exception(f'task {task} encounters exception')
                continue

    async def tear_down_micronet(self):
        self.logger.debug('tear down micronet')
        if self.server:
            self.logger.debug('closing listening')
            self.server.close()
            await self.server.wait_closed()
            self.server = None

        await self.clean_background_connector(cancel_all=True)

        self.logger.debug('closing queue')
        for node in self.node_manager.nodes():
            if isinstance(node, Node):
                self.queue_manager.close(node)
   
    def closing(self, node_id:int):
        self.node_manager.block(node_id)
        evil_node = self.node_manager.get_node(node_id)
        if evil_node is not None and isinstance(evil_node, Node):
            self.loop.call_soon_threadsafe(self.queue_manager.close, evil_node)
            self.logger.warn(f'node {evil_node.name} has been blocked')

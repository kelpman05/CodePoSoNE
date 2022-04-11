import asyncio
import logging
import typing
from collections import deque
from typing import Set, Callable,Tuple

from ..core.node import Node
from ..core.node_manager import BaseNode, NodeManager
from .packet import QueuedPacket

L = logging.getLogger(__name__)

EOC = None


NodeFilter = Callable[[BaseNode], bool]

# 代表回复普通节点的数据获取回调
DataGetter = Callable[[int], bytes]
ForwardGetter = Callable[[int,int,bytes],Tuple]
def all_node(n: BaseNode) -> bool:
    return True


def delegate_only(n: BaseNode) -> bool:
    return n.is_delegate

def delegate_not_blacked(n:BaseNode)->bool:
    return n.is_delegate and not n.is_blacked

def normal_only(n: BaseNode) -> bool:
    return n.is_normal


def some_ids(ids: Set[int]) -> NodeFilter:
    ids = set(ids)

    def _filter_by_id(n: BaseNode) -> bool:
        return n.id in ids

    return _filter_by_id


def clean_queue(queue: asyncio.Queue):
    while not queue.empty():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    # cancel all coroutines waiting for pkt
    for getter in queue._getters:  # type: ignore
        getter.cancel()


if typing.TYPE_CHECKING:
    PacketQueue = asyncio.Queue[QueuedPacket]
    QueueDictionary = typing.Dict[
        int, typing.Tuple[PacketQueue, PacketQueue],
    ]
else:
    PacketQueue = typing.Any
    QueueDictionary = typing.Any


class QueueManager:
    local: Node
    _by_node: QueueDictionary # 字典 nodeid->(ingress,egress)
    _buffered: typing.Deque[QueuedPacket]
    logger: logging.Logger
    node_manager: NodeManager

    def __init__(self, local: Node, node_manager: NodeManager):
        super().__init__()
        self.local = local
        self._by_node = dict()
        self.logger = L.getChild(f'QueueManager-{local.name}')
        self._buffered = deque()
        self.node_manager = node_manager

    async def send_to(self, remote: Node, pkt: bytes):
        if remote.id not in self._by_node:
            self.logger.warn(
                f'remote {remote.name} not connected or already disconnected'
            )
            return

        _, egress = self._by_node[remote.id]
        self.logger.debug(f'put pkt to remote {remote.name}')

        to_queue = QueuedPacket(
            origin=self.local,
            send_to=remote,
            received_from=None,
            data=pkt,
            full_packet=None,
        )
        await egress.put(to_queue)
    # 广播 数据
    # pkt 数据，filter_过滤器，用来过滤发送的节点
    # 添加到egress 队列，data_loop会把数据发送到节点
    async def broadcast(self, pkt: bytes, filter_: NodeFilter = all_node):
        for node_id, (_, egress) in self._by_node.items():
            remote = self.node_manager.get_node(node_id)
            assert remote is not None
            if not filter_(remote):
                self.logger.debug(f'{remote} is filtered out by {filter!r}')
                continue

            self.logger.debug(f'broadcast pkt to remote {remote.name}')
            to_queue = QueuedPacket(
                origin=self.local,
                send_to=remote,
                received_from=None,
                data=pkt,
                full_packet=None,
            )
            await egress.put(to_queue)
    async def broadcast_adapt(self, getter: DataGetter, filter_: NodeFilter = all_node):
        for node_id, (_, egress) in self._by_node.items():
            remote = self.node_manager.get_node(node_id)
            assert remote is not None
            if not filter_(remote):
                self.logger.debug(f'{remote} is filtered out by {filter!r}')
                continue

            self.logger.debug(f'broadcast pkt to remote {remote.name}')
            pkt = getter(remote)
            if not pkt:
                continue
            to_queue = QueuedPacket(
                origin=self.local,
                send_to=remote,
                received_from=None,
                data=pkt,
                full_packet=None,
            )
            await egress.put(to_queue)
    # 广播转发
    async def broadcast_forward(
        self,
        to_forward: QueuedPacket,
        filter_: NodeFilter = all_node,
        loopback=False,
    ):
        for node_id, (_, egress) in self._by_node.items():
            remote = self.node_manager.get_node(node_id)
            assert remote is not None
            if not filter_(remote):
                self.logger.debug(f'{remote} is filtered out by {filter!r}')
                continue
            if not loopback and to_forward.origin == remote:
                self.logger.debug(f'{remote} is origin, no loopback')
                continue

            self.logger.debug(f'forward pkt to remote {remote.name}')
            to_queue = QueuedPacket(
                origin=to_forward.origin,
                send_to=remote,
                received_from=self.local,
                data=to_forward.data,
                full_packet=to_forward.full_packet,
            )
            await egress.put(to_queue)
    async def broadcast_forward_adpt(self,
        getter:ForwardGetter,
        to_forward: QueuedPacket,
        filter_: NodeFilter = all_node,
        loopback=False,
    ):
        for node_id, (_, egress) in self._by_node.items():
            remote = self.node_manager.get_node(node_id)
            assert remote is not None
            if not filter_(remote):
                self.logger.debug(f'{remote} is filtered out by {filter!r}')
                continue
            if not loopback and to_forward.origin == remote:
                self.logger.debug(f'{remote} is origin, no loopback')
                continue
            to_data = getter(to_forward.origin.id,node_id,to_forward.data)
            if not to_data:
                continue
            self.logger.debug(f'forward pkt to remote {remote.name}')
            to_queue = QueuedPacket(
                origin=to_forward.origin,
                send_to=remote,
                received_from=self.local,
                data=to_data,
                # full_packet=to_forward.full_packet if nochange else None,#to_forward.full_packet会包含所有的原始数据，当这个字段有数时，会直接发送这个字段的数据，不会重新打包，这导致修改后的数据没有发送过去
                full_packet=None
            )   
            await egress.put(to_queue)

    def receive_one_no_wait(self) -> typing.Optional[QueuedPacket]:
        if self._buffered:
            return self._buffered.popleft()
        return None
    def send2itselft_adapt(self,getter:DataGetter):
        pkt = getter(self.local)
        if not pkt:
            self.logger.warning(f'send2itselft_adapt waining {self.local.name} getter get none')
            return
        to_queue = QueuedPacket(
            origin=self.local,
            send_to=self.local,
            received_from=self.local,
            data=pkt,
            full_packet=None,
        )
        self._buffered.append(to_queue)
    async def _read(
        self, remote_id: int, ingress: PacketQueue,
    ):
        remote = self.node_manager.get_node(remote_id)
        try:
            pkt: QueuedPacket = await ingress.get()
            assert pkt is None or pkt.received_from == remote
        except asyncio.CancelledError:
            # in case the connection has been closed
            return EOC
        return pkt
    # receive_one_no_wait 会从_buffered中获取
    # 如果receive_one_no_wait获取不到，则从_by_node中循环获取，并把所有获取到的数据存储到_buffered中
    async def receive_one(
        self, timeout: typing.Optional[float] = None
    ) -> typing.Optional[QueuedPacket]:
        pkt = self.receive_one_no_wait()
        if pkt is not None:
            return pkt

        tasks: typing.Set[asyncio.Task] = {
            asyncio.create_task(  # type: ignore
                self._read(node_id, ingress), name=f'receiving {node_id}'
            )
            for node_id, (ingress, _) in self._by_node.items()
        }

        if not tasks:
            # 这个是_by_node 为空的情况
            self.logger.warn('no active queue, in closing or reconnecting')
            return None

        done: typing.Set[asyncio.Future]
        pending: typing.Set[asyncio.Future]
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.FIRST_COMPLETED, timeout=timeout
        )
        for task in pending:
            assert (
                not task.done() and not task.cancelled()
            ), f'unexpected task status {task._state}'
            task.cancel()

        for task in done:
            try:
                pkt = task.result()
                if pkt is not None:
                    self._buffered.append(pkt)
            except asyncio.TimeoutError:
                pass
            except:  # noqa
                self.logger.exception(f'exception occurred when in {task!r}')
        return self._buffered.popleft() if self._buffered else None

    def _check_dup_channel(self, remote: Node):
        if remote.id in self._by_node:
            raise RuntimeError(f'dup channel for remote node {remote.name}')

    def create_queue(
        self, remote: Node
    ) -> typing.Tuple[asyncio.Queue, asyncio.Queue]:
        self._check_dup_channel(remote)
        ingress: asyncio.Queue = asyncio.Queue()
        egress: asyncio.Queue = asyncio.Queue()
        pair = (ingress, egress)
        self._by_node[remote.id] = pair # 这里存储所有的连接的队列，广播是通过这里进行的，处理数据也是从这里读取的
        return pair

    def close(self, remote: Node):
        if remote.id not in self._by_node:
            return
        ingress, egress = self._by_node.pop(remote.id)

        # cancellation of ingress getters causes readers return EOC
        clean_queue(ingress)
        clean_queue(egress)
        del ingress
        del egress

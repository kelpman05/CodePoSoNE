import asyncio
import logging
import typing
from datetime import datetime, timedelta
from time import sleep

from ..core.node import Node
from ..queue.manager import NodeFilter,DataGetter, QueueManager, all_node
from ..queue.packet import QueuedPacket
from ..queue.manager import DataGetter,ForwardGetter
L = logging.getLogger(__name__)


class QueueManagerAdapter:
    manager: QueueManager
    loop: asyncio.BaseEventLoop

    def __init__(self, manager: QueueManager, loop: asyncio.BaseEventLoop):
        self.manager = manager
        self.loop = loop

    def wait_next_pkt(
        self,
        timeout: typing.Optional[float] = None,
        run_till: typing.Optional[datetime] = None,
    ) -> typing.Optional[QueuedPacket]:

        now = datetime.utcnow()
        if timeout is not None:
            if run_till is not None:
                L.warn('both run_till and timeout specified, ignore run_till')
            run_till = now + timedelta(seconds=timeout)
        elif run_till is None and timeout is None:
            raise ValueError('either run_till or timeout should be specified')

        while now < run_till:
            timeout = (run_till - now).total_seconds()
            recv = asyncio.run_coroutine_threadsafe(
                self.manager.receive_one(timeout=timeout), self.loop
            )
            try:
                pkt = recv.result()
                if pkt is not None:
                    return pkt  
            except asyncio.TimeoutError:
                break
            now = datetime.utcnow()
            if (run_till - now).total_seconds() > 0.5:
                # add a little sleep to avoid too much retrying if all other
                # nodes are reconnecting.
                # TODO use event or some other sync primitives
                sleep(0.5)
        return None

    def drop_node(self, node):
        #call_soon_threadsafe 调度来自不同OS线程的回调函数
        self.loop.call_soon_threadsafe(self.manager.close, node)
    
    def broadcast(self, data: bytes, filter_: NodeFilter = all_node):
        #run_coroutine_threadsafe 从不同的OS线程调度一个协程对象 manager.broadcast是个协程，含有async
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast(data, filter_), self.loop
        ).result()
    def broadcast_adapt(self, getter: DataGetter, filter_: NodeFilter = all_node):
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast_adapt(getter, filter_), self.loop
        ).result()
    def broadcast_forward(
        self, to_forward: QueuedPacket, filter_: NodeFilter = all_node
    ):
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast_forward(to_forward, filter_), self.loop
        ).result()
    def broadcast_forward_adpt(self,getter:ForwardGetter, to_forward: QueuedPacket, filter_: NodeFilter = all_node):
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast_forward_adpt(getter,to_forward, filter_), self.loop
        ).result()
    def send_to(self, remote: Node, data: bytes):
        asyncio.run_coroutine_threadsafe(
            self.manager.send_to(remote, data), self.loop
        ).result()
    def send2itselft_adpt(self,getter:DataGetter):
        self.manager.send2itselft_adapt(getter)

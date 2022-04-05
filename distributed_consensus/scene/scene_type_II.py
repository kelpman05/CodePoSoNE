import struct
import typing
from abc import abstractmethod
from datetime import datetime, timedelta
from time import sleep

from ..core.node import Node
from ..core.node_manager import NodeManager
from ..sync_adapter import QueuedPacket, QueueManagerAdapter, normal_only
from .scene import AbstractScene, DataType, NodeDataMap


class SceneTypeII(AbstractScene):
    step_id: int
    received_normal_data: NodeDataMap
    received_delegate_data: NodeDataMap
    done: bool

    def __init__(
        self,
        local: Node,
        node_manager: NodeManager,
        adapter: QueueManagerAdapter,
        done_cb: typing.Callable,
    ):
        super().__init__(local, node_manager, adapter, done_cb)
        self.step_id = 0
        self.received_normal_data = NodeDataMap('received_normal_data')
        self.received_delegate_data = NodeDataMap('received_delegate_data')

    def run(self):
        self.done = False
        self.step_id = 0
        self.received_delegate_data.clear()

        if self.local.is_normal:
            self.normal_send()

        if self.local.is_delegate:
            self.received_normal_data.preload(
                self.node_manager, normal_only, self.local
            )
            normal_end = datetime.utcnow() + timedelta(
                seconds=self.normal_phase_timeout()
            )

            while True:
                pkt = self.adapter.wait_next_pkt(run_till=normal_end)
                if pkt is None:
                    self.logger.info(
                        f'receive timeout, normal consensus phase over'
                    )
                    break
                if self.broadcast_for_consensus(pkt):
                    self.received_normal_data.add(pkt)

            self.received_normal_data.drop_evil_nodes(
                self.node_manager, self.adapter
            )
        else:
            assert self.local.pure_normal, 'invalid local node type'
            sleep(self.normal_phase_timeout())

        # wait for micronet to be quiet, especially test on same host with
        # loopback interface
        sleep(2)

        while not self.done:
            self.step()
            # same as above, in case quick leader sends packet before slow node
            # quit previous step receiving, in which case leader id verify may
            # fail
            sleep(2)
            self.step_id += 1

        self.done_cb()

    def step(self):
        step_end = datetime.utcnow() + timedelta(seconds=self.step_timeout())
        if self.leader() is self.local:
            self.solve()
            self.leader_send()
            # also send solved results to normal nodes
            self.delegate_send()
            self.done = True
            self.logger.info('solved the problem as leader, done')

        while not self.done:
            pkt = self.adapter.wait_next_pkt(run_till=step_end)
            if pkt is None:
                self.logger.info(f'receive timeout, step {self.step_id} over')
                break

            self.non_leader_delegate_action(pkt)
            self.normal_node_action(pkt)

    def non_leader_delegate_action(self, pkt: QueuedPacket):
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return
        if self.local is self.leader():
            self.logger.debug("local is leader, abort",)
            return
        if not self.is_delegate_packet(pkt, DataType.LeaderToDelegate):
            self.logger.debug(
                f"{pkt} not from leader to delegate, won't verify it",
            )
            return
        if pkt.origin != self.leader():
            self.logger.debug(
                f"{pkt} not from active leader, won't verify it",
            )
            return

        if self.verify(pkt.data):
            self.save_result(pkt.data)
            self.delegate_send()
            self.done = True
            self.logger.info('verified the result as delegate, done')

    def normal_node_action(self, pkt: QueuedPacket):
        if not self.local.is_normal:
            self.logger.debug("local is not normal node, abort",)
            return
        if not self.is_delegate_packet(pkt, DataType.DelegateToNormal):
            self.logger.debug(
                f"{pkt} not from delegate or leader, won't handle it",
            )
            return

        self.received_delegate_data.add(pkt)
        data = self.extract_majority(self.received_delegate_data)
        if data is not None:
            self.save_result(data)
            self.done = True
            self.logger.info('saved the result as normal node, done')

    @abstractmethod
    def leader(self) -> Node:
        raise NotImplementedError()

    @abstractmethod
    def normal_phase_timeout(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def step_timeout(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def solve(self):
        raise NotImplementedError()

    @abstractmethod
    def verify(self, data: bytes) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def save_result(self, data: bytes):
        raise NotImplementedError()


class SimpleSum(SceneTypeII):
    class _Data:
        data_type: DataType
        value: int

        # packet: data type 1B, value 4B
        pkt_fmt: str = '>BL'

        __slots__ = ['data_type', 'value']

        def __init__(self, data_type: DataType, value: int):
            self.data_type = data_type
            self.value = value

        def __repr__(self):
            return f'<{self.data_type.name} value={self.value}>'

        @classmethod
        def from_bytes(cls, bs: bytes) -> 'SimpleSum._Data':
            type_, value = struct.unpack(cls.pkt_fmt, bs)
            return cls(DataType(type_), value)

        def pack(self) -> bytes:
            return struct.pack(self.pkt_fmt, self.data_type.value, self.value,)

    delegates: typing.List[Node]
    normal_phase_timeout_sec: float
    step_timeout_sec: float
    normal_value: int
    solved_value: int
    final_result: int

    def __init__(
        self,
        step_timeout_sec: float,
        normal_phase_timeout_sec: float,
        *args,# 任意多个无名参数，类型为tuple
        **kwargs, # 关键字参数，为dict
    ):
        super().__init__(*args, **kwargs)
        self.delegates = sorted(self.node_manager.get_delegates())
        self.step_timeout_sec = step_timeout_sec
        self.normal_phase_timeout_sec = normal_phase_timeout_sec
        self.normal_value = 1
        self.solved_value = 0

    def leader(self) -> Node:
        return self.delegates[self.step_id % len(self.delegates)]

    def normal_phase_timeout(self) -> float:
        return self.normal_phase_timeout_sec

    def step_timeout(self) -> float:
        return self.step_timeout_sec

    def solve(self):
        result = self.normal_value if self.local.is_normal else 0
        for _, pkts in self.received_normal_data.all.items():
            pkt = self._Data.from_bytes(list(pkts)[0].data)
            result += pkt.value
        self.solved_value = result
        self.logger.info(f'calculated result={result}')

    def verify(self, data: bytes) -> bool:
        solved = self._Data.from_bytes(data).value
        self.logger.info(f'received solved={solved}')
        if self.local.is_normal:
            solved -= self.normal_value

        for _, pkts in self.received_normal_data.all.items():
            node_pkt = self._Data.from_bytes(list(pkts)[0].data)
            solved -= node_pkt.value
        self.logger.info(f'remaining solved={solved}')
        return solved == 0

    def normal_data(self) -> bytes:
        return self._Data(DataType.NormalToDelegate, self.normal_value).pack()

    def leader_data(self) -> bytes:
        return self._Data(
            DataType.LeaderToDelegate, self.solved_value
        ).pack()

    def data_type(self, pkt: QueuedPacket) -> DataType:
        return self._Data.from_bytes(pkt.data).data_type

    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        try:
            data = self._Data.from_bytes(pkt.data)
            self.logger.debug(
                'got scene data %r by %d via %s',
                data,
                pkt.origin.id,
                pkt.received_from.id if pkt.received_from else 'unknown',
            )
            return True
        except:
            self.logger.warn(f'cannot parse {pkt}', exc_info=True)
            return False

    def save_result(self, data):
        data = self._Data.from_bytes(data)
        assert not hasattr(self, 'final_result') or (
            self.final_result == data.value and self.local.dual_role
        ), 'multiple setting of final value'
        self.final_result = data.value
        self.logger.info(f'final solved result: {data.value}')

    def delegate_data(self):
        value: int
        if self.local is self.leader():
            value = self.solved_value
        else:
            value = self.final_result
        return self._Data(DataType.DelegateToNormal, value).pack()

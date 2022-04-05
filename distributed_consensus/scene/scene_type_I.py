import struct
import typing
from abc import abstractmethod
from datetime import datetime, timedelta
from time import sleep

from ..core.node import Node
from ..core.node_manager import NodeManager
from ..sync_adapter import QueuedPacket, QueueManagerAdapter, normal_only
from .scene import AbstractScene, DataType, NodeDataMap


class SceneTypeI(AbstractScene):
    round_id: int
    received_normal_data: NodeDataMap
    received_delegate_data: NodeDataMap

    normal_phase_done: bool
    scene_end: bool

    def __init__(
        self,
        local: Node,
        node_manager: NodeManager,
        adapter: QueueManagerAdapter,
        done_cb: typing.Callable,
    ):
        super().__init__(local, node_manager, adapter, done_cb)
        self.round_id = 0
        self.received_delegate_data = NodeDataMap('received_delegate_data')
        self.received_normal_data = NodeDataMap('received_normal_data')
        self.received_normal_data.preload(
            self.node_manager, normal_only, self.local
        )
        self.scene_end = False

    @abstractmethod
    def check_end(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def check_end_in_data(self, data: bytes) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delegate_update(self):
        raise NotImplementedError()

    @abstractmethod
    def normal_initiate(self):
        raise NotImplementedError()

    @abstractmethod
    def normal_update(self, data: bytes):
        raise NotImplementedError()

    @abstractmethod
    def round_timeout(self) -> float:
        raise NotImplementedError()

    def scene_complete(self):
        self.logger.info('scene completed.')

    def run(self):
        self.round_id = 1
        local_delegate_ending: bool = False
        self.seen.clear()

        if self.local.is_normal:
            # round 1 starts from step 3
            self.normal_initiate()
            self.normal_send()
        # delegate 代表
        while not self.scene_end and not local_delegate_ending:
            # step 1
            if self.round_id > 1 and self.local.is_delegate:
                self.received_normal_data.drop_evil_nodes(
                    self.node_manager, self.adapter
                )
                self.delegate_update()
                # does not set self.scene_end immediately to handle nodes with
                # both delegate and normal roles, in which case normal packet
                # receiving phase still need to run after local delegate
                # decides to exit
                local_delegate_ending = self.check_end()
                self.delegate_send()
                self.received_normal_data.preload(
                    self.node_manager, normal_only, self.local
                )

            # first round doesn't need normal data update
            self.normal_phase_done = self.round_id == 1
            self.received_delegate_data.clear()
            now = datetime.utcnow()
            round_end = now + timedelta(seconds=self.round_timeout())
            self.logger.info(
                f'round {self.round_id} begin, will end by {round_end}'
            )

            # step 2 ~ 5, wrapped by receiving loop
            self.round(round_end)

            # add a gap for possible timing error. otherwise quick nodes
            # will send packet for next round but slow nodes may drop them due
            # to invalid round id
            sleep(2)

            self.round_id += 1
        self.scene_complete()
        self.done_cb()
    # round 包含的逻辑：
    # 代表接收到普通节点发送的数据，转发给其他代表（包括普通节点）
    # 其他代表获取到数据，添加到缓存
    # 普通节点获取到数据，更新发送给所有代表，scene_end = true
    def round(self, round_end: datetime):
        while not self.scene_end:
            pkt = self.adapter.wait_next_pkt(run_till=round_end)
            if pkt is None:
                self.logger.info(
                    f'receive timeout, round {self.round_id} over'
                )
                break
            # 解压数据并且判断是否是当前一轮的数据
            if not self.is_packet_valid(pkt):
                self.logger.warn(f'drop invalid packet {pkt}')
                continue
            # step 2 & 3
            self.normal_node_action(pkt)
            # step 4 pkt包含了remote等信息，看看是否是根据这个来回传给普通节点
            self.delegate_node_action(pkt)
    # 普通节点处理，把来自代表的数据进行处理
    def normal_node_action(self, pkt: QueuedPacket):
        if self.normal_phase_done:
            self.logger.debug(
                f"normal data of round {self.round_id} has been finalized"
            )
            return
        if not self.local.is_normal:
            self.logger.debug("local is not normal node, abort",)
            return
        if not self.is_delegate_packet(pkt, DataType.DelegateToNormal):
            self.logger.debug(
                f"{pkt} not from delegate, normal node won't handle it",
            )
            return

        self.received_delegate_data.add(pkt)
        # 下面函数是用来判断
        # 如果接收到大部分的代表返回的数据，那么就更新数据再广播给代表
        data = self.extract_majority(self.received_delegate_data)
        if data is not None:
            self.normal_update(data)
            self.normal_phase_done = True
            self.normal_send()
            self.scene_end = self.check_end_in_data(data)
    # 代表节点处理，把来自普通节点的数据进行处理
    def delegate_node_action(self, pkt: QueuedPacket):
        # 共识
        if not self.broadcast_for_consensus(pkt):
            # implying pkt is a normal packet
            return
        if pkt.origin.id not in self.received_normal_data.all.keys():
            self.logger.warn(
                'pkt %r from unexpected normal node, expecting %s',
                pkt,
                tuple(self.received_normal_data.all.keys()),
            )
            return
        self.received_normal_data.add(pkt)


class SimpleAdd(SceneTypeI):
    final_round: int
    round_timeout_sec: float

    normal_value: int
    delegate_value: int

    class _Data:
        data_type: DataType
        round_id: int
        value: int
        is_end: bool

        # packet: data type 1B, round ID 4B, value 4B, end flag 1B
        pkt_fmt: str = '>BLLB'

        __slots__ = ['data_type', 'round_id', 'value', 'is_end']

        def __init__(
            self, data_type: DataType, round_id: int, value: int, is_end: bool
        ):
            self.data_type = data_type
            self.round_id = round_id
            self.value = value
            self.is_end = is_end

        def __repr__(self):
            return (
                f'<{self.data_type.name} round_id={self.round_id} '
                + f'value={self.value}{" end" if self.is_end else ""}>'
            )

        @classmethod
        def from_bytes(cls, bs: bytes) -> 'SimpleAdd._Data':
            type_, round_id, value, is_end = struct.unpack(cls.pkt_fmt, bs)
            return cls(DataType(type_), round_id, value, is_end > 0)
        
        def pack(self) -> bytes:
            return struct.pack(
                self.pkt_fmt,
                self.data_type.value,
                self.round_id,
                self.value,
                1 if self.is_end else 0,
            )

    def __init__(self, final_round, round_timeout_sec, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_round = final_round
        self.round_timeout_sec = round_timeout_sec
        self.normal_value = 0

    def check_end(self) -> bool:
        return self.round_id >= self.final_round

    def check_end_in_data(self, data: bytes) -> bool:
        try:
            return self._Data.from_bytes(data).is_end
        except:
            return False

    def delegate_update(self):
        if self.local.is_normal:
            # also take my own value into consideration since node won't
            # receive its own packet from micronet
            self.delegate_value = self.normal_value
        else:
            self.delegate_value = 0
        for _, pkts in self.received_normal_data.all.items():
            # this method is supposed to be called after clearup evil nodes
            pkt = list(pkts)[0]
            self.delegate_value += self._Data.from_bytes(pkt.data).value
        self.logger.info(f'update delegate value to {self.delegate_value}')

    def normal_initiate(self):
        self.normal_value = 1

    def normal_update(self, data: bytes):
        self.normal_value = self._Data.from_bytes(data).value + 1
        self.logger.info(f'update normal value to {self.normal_value}')

    def round_timeout(self) -> float:
        return self.round_timeout_sec

    def normal_data(self) -> bytes:
        return self._Data(
            DataType.NormalToDelegate, self.round_id, self.normal_value, False
        ).pack()

    def delegate_data(self) -> bytes:
        return self._Data(
            DataType.DelegateToNormal,
            self.round_id,
            self.delegate_value,
            self.check_end(),
        ).pack()

    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        try:
            data = self._Data.from_bytes(pkt.data)
            self.logger.debug(
                'got scene data %r by %d via %s',
                data,
                pkt.origin.id,
                pkt.received_from.id if pkt.received_from else 'unknown',
            )
            return data.round_id == self.round_id
        except:
            self.logger.warn(f'cannot parse {pkt}', exc_info=True)
            return False

    def data_type(self, pkt: QueuedPacket) -> DataType:
        return self._Data.from_bytes(pkt.data).data_type

    def scene_complete(self):
        self.logger.info('scene complete, final values:')
        if self.local.is_delegate:
            self.logger.info(f'delegate value: {self.delegate_value}')
        if self.local.is_normal:
            self.logger.info(f'normal value: {self.normal_value}')

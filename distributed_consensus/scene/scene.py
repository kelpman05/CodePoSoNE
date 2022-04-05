import logging
import typing
from abc import ABC, abstractmethod
from collections import Counter
from enum import Enum

from ..core.node import Node
from ..core.node_manager import BaseNode, NodeManager
from ..queue.manager import DataGetter,ForwardGetter
from ..sync_adapter import (
    QueuedPacket,
    QueueManagerAdapter,
    NodeFilter,
    all_node,
    delegate_only,
    delegate_not_blacked,
    normal_only,
)

L = logging.getLogger(__name__)


class NodeDataMap:
    # it seems keeping node_id-bytes map is sufficient but here I insist
    # storing the whole queued packet (with sender/forwarder) for better
    # debugging ability
    table: typing.Dict[int, typing.Set[QueuedPacket]]

    name: str
    logger: logging.Logger

    def __init__(self, name: str):
        super().__init__()
        self.table = dict()
        self.name = name
        self.logger = L.getChild(f'{self.__class__.__name__}-{self.name}')

    def add(self, pkt: QueuedPacket):
        """ add a received packet to table """
        self.table.setdefault(pkt.origin.id, set()).add(pkt)

    def preload(
        self,
        node_manager: NodeManager,
        filter_: NodeFilter,
        local: BaseNode,
        clear: bool = True,
    ):
        """ preload table with node IDs from which at least one packet is
        supposed to be received.

            local node and blacked nodes will be excluded from expecting list
            no matter filter keeps them or not
        """
        if clear:
            self.clear()
        for node in node_manager.nodes():
            if filter_(node) and node != local and not node.is_blacked:
                self.table[node.id] = set()

    def clear(self):
        self.table.clear()

    def extract_majority(
        self,
        initial: typing.Optional[typing.List[bytes]] = None,
        threshold: float = -1,
    ) -> typing.Optional[bytes]:
        counter: typing.Counter[bytes] = Counter()
        if initial is not None:
            counter.update({i: 1 for i in initial})
        counter.update(
            [
                list(pkts)[0].data
                for pkts in self.table.values()
                if len(pkts) == 1
            ]
        )
        if not counter:
            return None
        top, freq = counter.most_common(1)[0]
        return top if freq > threshold else None
    def extract_majority_adapt(self,threshold: float = -1):
        for pkts in self.table.values():
            pkt = list(pkts)[0]
            # self.logger.warning(f'{pkt}')
        counter: typing.Counter[bytes] = Counter()
        counter.update(
            [
                list(pkts)[0].data
                for pkts in self.table.values()
                if len(pkts) == 1
            ]
        )
        if not counter:
            return None
        top, freq = counter.most_common(1)[0] # 出现频率最高的一个单词
        self.logger.info(f' freq = {freq} threshold={threshold}')
        return top if freq >= threshold else None
    # 移除作恶节点
    def drop_evil_nodes(
        self,
        node_manager: typing.Optional[NodeManager],
        adapter: typing.Optional[QueueManagerAdapter],
    ):
        self.logger.debug(f'normal data before filtering {self.table}')
        # 统计data,如果没有发送数据或者有两个不同数据（给不同代表发送不同数据，代表间转发获取到两种及以上不同数据），那么节点是作恶节点
        # python中set是默认去重的，pkt_set这个set里的对象是一个QueuedPacket类型，所以没办法去重，
        # {pkt.data for pkt in pkt_set}这段代码是构造一个set，set里是byte类型，会直接去重，
        # 所以正常情况下，获取到的一个节点的所有数据，包括转发获取到的，经过去重后会只剩下一个，否则就是作恶节点
        node_recv_num = [
            (node_id, len({pkt.data for pkt in pkt_set}))
            for (node_id, pkt_set) in self.table.items()
        ]
        # 作恶的情况下，
        evil_node_ids = filter(lambda x: x[1] != 1, node_recv_num)

        for evil, pkt_num in evil_node_ids:
            self.logger.warn(f'remote node {evil} send {pkt_num} packets')
            self.logger.warn(f'all packets from node {evil} are dropped')
            del self.table[evil]
            if node_manager and adapter:
                node_manager.block(evil)
                evil_node = node_manager.get_node(evil)
                if evil_node is not None and isinstance(evil_node, Node):
                    adapter.drop_node(evil_node)
                self.logger.warn(f'node {evil} has been blocked')
        self.logger.debug(f'normal data after filtering {self.table}')

    def block_evil_leader(
        self,
        node_manager: typing.Optional[NodeManager],
        adapter: typing.Optional[QueueManagerAdapter],
    ):
        self.logger.debug(f'normal data before filtering {self.table}')
        # 统计data,如果没有发送数据或者有两个不同数据（给不同代表发送不同数据，代表间转发获取到两种及以上不同数据），那么节点是作恶节点
        # python中set是默认去重的，pkt_set这个set里的对象是一个QueuedPacket类型，所以没办法去重，
        # {pkt.data for pkt in pkt_set}这段代码是构造一个set，set里是byte类型，会直接去重，
        # 所以正常情况下，获取到的一个节点的所有数据，包括转发获取到的，经过去重后会只剩下一个，否则就是作恶节点
        node_recv_num = [
            (node_id, len({pkt.data for pkt in pkt_set}))
            for (node_id, pkt_set) in self.table.items()
        ]
        # 作恶的情况下，
        evil_node_ids = filter(lambda x: x[1] != 1, node_recv_num)

        for evil, pkt_num in evil_node_ids:
            self.logger.warn(f'remote node {evil} send {pkt_num} packets')
            self.logger.warn(f'all packets from node {evil} are dropped')
            del self.table[evil]
            if node_manager and adapter:
                node_manager.block(evil)
                evil_node = node_manager.get_node(evil)
                if evil_node is not None and isinstance(evil_node, Node):
                    adapter.drop_node(evil_node)
                self.logger.warn(f'node {evil} has been blocked')
        self.logger.debug(f'normal data after filtering {self.table}')

    @property
    def all(self) -> typing.Dict[int, typing.Set[QueuedPacket]]:
        return self.table

    def __repr__(self):
        return f'<{self.name} {self.all!r}>'


class DataType(Enum):
    Unknown = 0
    DelegateToNormal = 1
    NormalToDelegate = 2
    LeaderToDelegate = 3
    StateChange = 4


class AbstractScene(ABC):
    local: Node
    node_manager: NodeManager
    adapter: QueueManagerAdapter
    done_cb: typing.Callable
    seen: typing.Set[typing.Tuple[int, bytes]]
    local_delegate_data: typing.Optional[bytes]
    logger: logging.Logger

    def __init__(
        self,
        local: Node,
        node_manager: NodeManager,
        adapter: QueueManagerAdapter,
        done_cb: typing.Callable,
    ):
        self.seen = set()
        self.local = local
        self.adapter = adapter
        self.node_manager = node_manager
        self.done_cb = done_cb  # type: ignore  # mypy issue #708
        self.local_delegate_data = None
        self.logger = L.getChild(f'{self.__class__.__name__}-{self.local.id}')

    def normal_send(self):
        data = self.normal_data()
        # 广播消息 filter_相当于一个代理方法(表达式、回调)
        self.adapter.broadcast(data, filter_=delegate_only)
    def normal_send_adpt(self,getter: DataGetter):
        self.adapter.broadcast_adapt(getter, filter_=delegate_only)
    # 发送数据给自己，这个是当自己即是普通节点，又是代表节点时
    # 只是把数据添加到buffer中，不必真的做发送操作
    def send2itselft_adpt(self,getter:DataGetter):
        if self.local.is_normal and self.local.is_delegate:
            self.adapter.send2itselft_adpt(getter)
        
    def delegate_send(self):
        data = self.delegate_data()
        self.adapter.broadcast(data, filter_=normal_only)
        # no loopback forwarding so local node will not receive this data from
        # micronet. remember data for normal phase (if local node is also a
        # normal node)
        self.local_delegate_data = data
    def delegate_send_adapt(self,getter: DataGetter):
        self.adapter.broadcast_adapt(getter, filter_=normal_only)
        # self.local_delegate_data = data
    # 发送数据给自己，这个是当自己即是普通节点，又是代表节点时
    # 只是把数据添加到buffer中，不必真的做发送操作
    def delegate_send2itselft_adpt(self,getter: DataGetter):
        pass
    def leader_send(self):
        data = self.leader_data()
        self.adapter.broadcast(data, filter_=all_node)
        # no loopback forwarding so local node will not receive this data from
        # micronet. remember data for normal phase (if local node is also a
        # normal node)
        self.local_delegate_data = data
    # 广播运行状态信息 
    def state_send(self,state:bool,time_span:float):
        data = self.state_data(state=state,time_span=time_span)
        self.adapter.broadcast(data, filter_=all_node)
    # 代表转发 
    # seen 存储已经转发过的node，如果没有转发，则转发出去。（以此来避免数据在各个代表中循环转发）
    def delegate_forward(self, pkt: QueuedPacket, filter_: NodeFilter) -> bool:
        # seen?这个不用每轮清空吗?
        if (pkt.origin.id, pkt.data) not in self.seen: 
            self.seen.add((pkt.origin.id, pkt.data))
            self.adapter.broadcast_forward(pkt, filter_=filter_)
            return True
        return False
    def delegate_forward_adpt(self,getter:ForwardGetter,pkt: QueuedPacket, filter_: NodeFilter)->bool:
        # seen?这个不用每轮清空吗?
        if (pkt.origin.id, pkt.data) not in self.seen:
            self.seen.add((pkt.origin.id, pkt.data))
            self.adapter.broadcast_forward_adpt(getter,pkt, filter_=filter_)
            return True
        return False
    def extract_majority(self, received: NodeDataMap):
        # local_delegate_data 为本地代表发送的数据
        # received 为 received_delegate_data，从代表中接收到的数据
        initial: typing.Optional[typing.List[bytes]]
        self.logger.debug(f'trying to extract majority from {received}')
        if self.local.is_delegate and self.local_delegate_data is not None:
            initial = [self.local_delegate_data]
        else:
            initial = None
        return received.extract_majority(
            initial=initial, threshold=self.node_manager.delegate_num / 2,
        )
    def extract_majority_adapt(self,received: NodeDataMap):
        return received.extract_majority_adapt(
            threshold=self.node_manager.delegate_num / 2,
        )
    def is_delegate_packet(
        self, pkt: QueuedPacket, expected_data_type: typing.Optional[DataType]
    ) -> bool:
        assert expected_data_type in (
            None,
            DataType.LeaderToDelegate,
            DataType.DelegateToNormal,
        ), f'{expected_data_type} is not a valid delegate packet type'

        if pkt.received_from is None:
            self.logger.debug("receive_from is None, not from delegate",)
            return False
        if not pkt.received_from.is_delegate:
            self.logger.debug(
                "remote %s is not delegate", pkt.received_from.id,
            )
            return False
        if not pkt.origin.is_delegate:
            self.logger.debug(
                "origin %s is not delegate", pkt.origin.id,
            )
            return False
        data_type = self.data_type(pkt)
        if data_type in (DataType.NormalToDelegate, DataType.Unknown):
            self.logger.debug(f"data is of {data_type.name} type")
            return False
        if expected_data_type is not None and data_type != expected_data_type:
            self.logger.debug(f"data is not of {expected_data_type.name} type")
            return False
        return True

    def is_normal_packet(self, pkt: QueuedPacket) -> bool:
        if not pkt.origin.is_normal:
            self.logger.warning(
                "origin %s is not normal", pkt.origin.id,
            )
            return False
        if self.data_type(pkt) != DataType.NormalToDelegate:
            self.logger.debug("data is not in NormalToDelegate type")
            return False
        return True

    def is_state_packet(self,pkt:QueuedPacket) -> bool:
        if self.data_type(pkt) != DataType.StateChange:
            # self.logger.debug("data is not StateChange type")
            return False
        return True

    def broadcast_for_consensus(self, pkt: QueuedPacket) -> bool:
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return False
        if not self.is_normal_packet(pkt):
            self.logger.debug(f"{pkt} is not from normal node, ignore",)
            return False

        self.delegate_forward(pkt, delegate_only)
        return True
    def broadcast_for_consensus_adpt(self,getter:ForwardGetter,pkt: QueuedPacket)->bool:
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return False
        if not self.is_normal_packet(pkt):
            self.logger.debug(f"{pkt} is not from normal node, ignore",)
            return False
        self.delegate_forward_adpt(getter,pkt, delegate_only)
        return True
    # 广播状态变更
    def broadcast_for_state_adpt(self,getter:ForwardGetter,pkt: QueuedPacket)->bool:
        self.adapter.broadcast_forward_adpt(getter,pkt, filter_=all_node)

    @abstractmethod
    def run(self):
        raise NotImplementedError()
    
    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        raise NotImplementedError()

    def normal_data(self) -> bytes:
        raise NotImplementedError()

    def delegate_data(self) -> bytes:
        raise NotImplementedError()

    def leader_data(self) -> bytes:
        raise NotImplementedError()
    def state_data(self,state:bool,time_span:float) -> bytes:
        raise NotImplementedError()

    def data_type(self, pkt: QueuedPacket) -> DataType:
        raise NotImplementedError()
    def data_value(self,pkt: QueuedPacket):
        raise NotImplementedError()



class AbstractPooScene(ABC):
    local: Node
    node_manager: NodeManager
    adapter: QueueManagerAdapter
    done_cb: typing.Callable
    seen: typing.Set[typing.Tuple[int, bytes]]
    local_delegate_data: typing.Optional[bytes]
    logger: logging.Logger
    def __init__(
        self,
        local: Node,
        node_manager: NodeManager,
        adapter: QueueManagerAdapter,
        done_cb: typing.Callable,
    ):
        self.seen = set()
        self.local = local
        self.adapter = adapter
        self.node_manager = node_manager
        self.done_cb = done_cb  # type: ignore  # mypy issue #708
        self.local_delegate_data = None
        self.logger = L.getChild(f'{self.__class__.__name__}-{self.local.id}')
    # 判断是否是leader
    # 黑名单内的代表不能作为leader
    def is_leader(self,node_id):
        leader = self.get_leader()
        # self.logger.warning(f'leader node id {leader.id}')
        return False if leader==None else leader.id == node_id
    def get_leader(self)->Node:
        nodes = self.node_manager.get_delegates()
        active_nodes = [node for node in nodes if not node.is_blacked] 
        if len(active_nodes)==0:
            return None
        active_nodes.sort(key=lambda m:m.id)
        leader = active_nodes[0] 
        return leader 
    def solve_send_adapt(self,getter):
        self.adapter.broadcast_adapt(getter,filter_=delegate_not_blacked)
    def optimal_send_adapt(self,getter):
        self.adapter.broadcast_adapt(getter,filter_=all_node)
    # 发送数据给自己，这个是当自己即是普通节点，又是代表节点时
    # 只是把数据添加到buffer中，不必真的做发送操作
    def send2itselft_adpt(self,getter:DataGetter):
        if self.local.is_normal and self.local.is_delegate:
            self.adapter.send2itselft_adpt(getter)
    # 发送数据给自己，这个是当自己即是普通节点，又是代表节点时
    # 只是把数据添加到buffer中，不必真的做发送操作
    def delegate_send2itselft_adpt(self,getter: DataGetter):
        pass
    # 代表转发 
    # seen 存储已经转发过的node，如果没有转发，则转发出去。（以此来避免数据在各个代表中循环转发）
    def delegate_forward(self, pkt: QueuedPacket, filter_: NodeFilter) -> bool:
        # seen?这个不用每轮清空吗?
        if (pkt.origin.id, pkt.data) not in self.seen: 
            self.seen.add((pkt.origin.id, pkt.data))
            self.adapter.broadcast_forward(pkt, filter_=filter_)
            return True
        return False
    def delegate_forward_adpt(self,getter:ForwardGetter,pkt: QueuedPacket, filter_: NodeFilter)->bool:
        if self.solve_data_validate(pkt.data,pkt.origin.id,pkt.received_from.id):
            # seen?这个不用每轮清空吗?
            if (pkt.origin.id, pkt.data) not in self.seen:
                self.seen.add((pkt.origin.id, pkt.data))
                # 当数据是来源于local时，不需要转发
                if pkt.origin.id != self.local.id:
                    # 这里判断解是否异常
                    self.adapter.broadcast_forward_adpt(getter,pkt, filter_=filter_)
                else:
                    self.logger.info(f'data is from local,ignore forward')
                return True
            else:
                self.logger.info(f'has the same data from {pkt.origin.id}via{pkt.received_from.id},ignore forward')
        else:
            self.logger.info(f'data from {pkt.origin.id}via{pkt.received_from.id} is unvalidate,ignore forward')
        return False
    def extract_majority(self, received: NodeDataMap):
        # local_delegate_data 为本地代表发送的数据
        # received 为 received_delegate_data，从代表中接收到的数据
        initial: typing.Optional[typing.List[bytes]]
        self.logger.debug(f'trying to extract majority from {received}')
        if self.local.is_delegate and self.local_delegate_data is not None:
            initial = [self.local_delegate_data]
        else:
            initial = None
        return received.extract_majority(
            initial=initial, threshold=self.node_manager.delegate_num / 2,
        )
    def extract_majority_adapt(self,received: NodeDataMap):
        return received.extract_majority_adapt(
            threshold=self.node_manager.delegate_num / 2,
        )
    def is_leader_packet(self,pkt:QueuedPacket)->bool:
        if pkt.received_from is None:
            self.logger.debug("receive_from is None, not from delegate",)
            return False
        if not pkt.received_from.is_delegate:
            self.logger.debug(
                "remote %s is not delegate", pkt.received_from.id,
            )
            return False
        if not self.is_leader(pkt.origin.id):
            self.logger.debug(
                "remote %s is not leader", pkt.origin.id,
            )
            return False
        data_type = self.data_type(pkt)
        if data_type != DataType.LeaderToDelegate:
            self.logger.debug(f"data is not of LeaderToDelegate type")
            return False
        return True
    def is_delegate_packet(self,pkt:QueuedPacket)->bool:
        if pkt.received_from is None:
            self.logger.debug("receive_from is None, not from delegate",)
            return False
        if not pkt.received_from.is_delegate:
            self.logger.debug(
                "remote %s is not delegate", pkt.received_from.id,
            )
            return False
        if not pkt.origin.is_delegate:
            self.logger.debug(
                "origin %s is not delegate", pkt.origin.id,
            )
            return False
        data_type = self.data_type(pkt)
        if data_type != DataType.DelegateToNormal:
            self.logger.debug(f"data is not of DelegateToNormal type")
            return False
        return True
    def broadcast_for_consensus(self, pkt: QueuedPacket) -> bool:
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return False
        if not self.is_normal_packet(pkt):
            self.logger.debug(f"{pkt} is not from normal node, ignore",)
            return False

        self.delegate_forward(pkt, delegate_only)
        return True
    def broadcast_for_consensus_adpt(self,getter:ForwardGetter,pkt: QueuedPacket)->bool:
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return False
        if not self.is_normal_packet(pkt):
            self.logger.debug(f"{pkt} is not from normal node, ignore",)
            return False
        self.delegate_forward_adpt(getter,pkt, delegate_only)
        return True
    
    def broadcast_solve_adapt(self,getter:ForwardGetter,pkt:QueuedPacket)->bool:
        if not self.local.is_delegate:
            self.logger.debug("local is not delegate node, abort",)
            return False
        if not self.is_leader_packet(pkt):
            self.logger.debug("pkt is not from leader node, ignore",)
            return False
        return self.delegate_forward_adpt(getter,pkt,delegate_not_blacked)

    @abstractmethod
    def run(self):
        raise NotImplementedError()
    
    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        raise NotImplementedError()

    def data_type(self, pkt: QueuedPacket) -> DataType:
        raise NotImplementedError()
    def data_value(self,pkt: QueuedPacket):
        raise NotImplementedError()
    def solve_data_validate(self,data,origin_id,received_from_id):
        raise NotImplementedError()

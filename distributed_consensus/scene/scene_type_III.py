import copy
import typing
import struct 
import pandas as pd
import time
from abc import abstractmethod
from datetime import datetime, timedelta
from time import sleep
from ..app import socket_manager

from .scene_type_I import SceneTypeI
from ..global_config import GlobalConfig
from ..core.node import Node
from ..core.node_manager import NodeManager
from ..sync_adapter import QueuedPacket, QueueManagerAdapter, normal_only
from .scene import AbstractScene, DataType, NodeDataMap
from .consensus.nodeUpdate import NodeUpdate

# from .consensus.delegateCheckEnd import delegate_checkEnd
# from .consensus.delegateUpdate import delegate_update
# from .consensus.normalNodeUpdate import normal_node_update

# 场景3
class SceneTypeIII(AbstractScene):
    round_id: int
    received_normal_data: NodeDataMap
    received_delegate_data: NodeDataMap
    
    normal_phase_done: bool
    scene_end: bool
    running:bool
    running_mark:float
    global_config: GlobalConfig

    def __init__(
        self,
        local: Node,
        node_manager: NodeManager,
        adapter: QueueManagerAdapter,
        done_cb: typing.Callable,
        global_config: GlobalConfig,
    ):
        super().__init__(local, node_manager, adapter, done_cb)
        self.global_config = global_config
        self.global_config.state_send_invoke = self.state_send
        self.global_config.state_change_invoke = self.change_state
        self.global_config.get_state_invoke = self.get_state
        self.global_config.get_current_value_invoke = self.get_current_value
        self.round_id = 0
        self.received_delegate_data = NodeDataMap('received_delegate_data')
        self.received_normal_data = NodeDataMap('received_normal_data')
        self.received_normal_data.preload(
            self.node_manager, normal_only, self.local
        )
        self.scene_end = False
        self.running = True
        self.running_mark = time.time()
     
    @abstractmethod
    def get_current_value(self):
        raise NotImplementedError()

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
    def get_received_demands(self):
        raise NotImplementedError()
    @abstractmethod
    def normal_getter(self, int)-> bytes:
        raise NotImplementedError()
    @abstractmethod
    def delegate_getter(self, int)-> bytes:
        raise NotImplementedError()
    @abstractmethod
    def delegate_forward_getter(self,from_node,to_node,data:bytes)->bytes:
        raise NotImplementedError()
    @abstractmethod
    def state_forward_getter(self,from_node,to_node,data:bytes) -> bytes:
        raise NotImplementedError()
    @abstractmethod
    def normal_initiate(self):
        raise NotImplementedError()

    @abstractmethod
    def normal_update(self, data: bytes):
        raise NotImplementedError()
    @abstractmethod
    def get_received_prices(self):
        raise NotImplementedError()
    @abstractmethod
    def round_timeout(self) -> float:
        raise NotImplementedError()
    @abstractmethod
    def write_round_end_time(self,seconds):
        raise NotImplementedError()
    @abstractmethod
    def read_round_end_time(self):
        raise NotImplementedError()
    @abstractmethod
    def write_round_demand(self):
        raise NotImplementedError()
    def check_round_end(self):
        round_end = self.read_round_end_time()
        now = datetime.utcnow()
        while(now<round_end or not self.running):
            sleep(1)
            round_end = self.read_round_end_time()
            now = datetime.utcnow()
    def scene_complete(self):
        self.logger.info('scene completed.')

    def run(self):
        self.round_id = 1
        local_delegate_ending: bool = False 
        self.seen.clear()

        if self.local.is_normal:
            # round 1 starts from step 3
            self.normal_initiate()
            # 不用初始化数据，__init__方法里有初始化
            # 初始需求量发送
            # self.normal_send()
            self.send2itselft_adpt(self.normal_getter)
            self.normal_send_adpt(self.normal_getter)
        
        
        # delegate 代表
        while not self.scene_end and not local_delegate_ending:
            socket_manager.notice_round(round=self.round_id)
            socket_manager.notice_console(f'Iteration:{self.round_id} start')
            self.logger.info(
                f'round {self.round_id} begin'
            )
            # step 1
            if self.round_id > 1 and self.local.is_delegate:
                # 第二步是代表共识，排除作恶节点
                # 更新数据并发回给普通节点
                self.received_normal_data.drop_evil_nodes(
                    self.node_manager, self.adapter
                )
                black_nodes = self.node_manager.block_nodes()
                black_list = [
                  f'Community {node.id}'
                  for node in black_nodes
                ]
                black = "empty" if len(black_list)==0 else ",".join(black_list)
                socket_manager.notice_blacklist(black)
                self.delegate_update()
                # does not set self.scene_end immediately to handle nodes with
                # both delegate and normal roles, in which case normal packet
                # receiving phase still need to run after local delegate
                # decides to exit
                local_delegate_ending = self.check_end()
                # self.delegate_send()
                self.send2itselft_adpt(self.delegate_getter)
                self.delegate_send_adapt(self.delegate_getter)
                self.received_normal_data.preload(
                    self.node_manager, normal_only, self.local
                )

            # first round doesn't need normal data update

            # 第一轮
            
            
            self.normal_phase_done = self.round_id == 1
            self.received_delegate_data.clear()
            now = datetime.utcnow()
            round_end = now + timedelta(seconds=self.round_timeout())
            

            # step 2 ~ 5, wrapped by receiving loop

            # 获取数据

            # 第一步是代表接收转发 （直到超时跳出循环）
            # 第二步继续就是第三步，普通节点接收到代表的数据，更新再次发送

            self.round(round_end)
            
            # add a gap for possible timing error. otherwise quick nodes
            # will send packet for next round but slow nodes may drop them due
            # to invalid round id
            # 这里稍微等待久一点，能让所有的节点都完成了上一轮的操作，这样能避免出现roud_id不一致问题
            self.check_round_end()
            socket_manager.notice_console(f'wait for iteration end')
            self.round_id += 1
        self.scene_complete()
        self.done_cb()
    # round 包含的逻辑：
    # 代表接收到普通节点发送的数据，转发给其他代表（包括普通节点）
    # 其他代表获取到数据，添加到缓存
    # 普通节点获取到数据，更新发送给所有代表，scene_end = true
    def round(self, round_end: datetime):
        round_over = False
        while not self.scene_end:
            pkt = self.adapter.wait_next_pkt(run_till=round_end)
            if pkt is None:
                # 超时结束
                self.logger.info(
                    f'receive timeout, round {self.round_id} over'
                )
                round_over = True
                break
            # 如果是state数据，不用验证周期
            if self.state_msg_action(pkt):
                continue
            # 解压数据并且判断是否是当前一轮的数据
            if not self.is_packet_valid(pkt):
                # 如果不是当前一轮数据，或者数据不能unpack，弃包 继续循环
                self.logger.warn(f'drop invalid packet {pkt}')
                continue
            # step 2 & 3
            self.normal_node_action(pkt)
            # step 4 pkt包含了remote等信息，看看是否是根据这个来回传给普通节点
            self.delegate_node_action(pkt)
        if(round_over):
            self.write_round_demand()
            self.write_round_end_time(10)
            # 写入round_end时间
    # 处理state变更数据，用来控制程序的running状态
    def state_msg_action(self,pkt:QueuedPacket) -> bool:
        if not self.is_state_packet(pkt):
            return False
        # 判断是否是转发的，如果是转发过来的，不用再转发
        #socket_manager.notice_console('接收到state状态数据')
        if pkt.origin.id == pkt.received_from.id:
            #socket_manager.notice_console('转发变更数据')
            self.broadcast_for_state_adpt(self.state_forward_getter,pkt)
        # 变更状态
        # 转发状态
        # 使用running_mark作为转发标记，转换标记为时间戳(timeStamp),用来判断转发的状态是否是最新状态变更
        # 
        
        values = self.data_value(pkt)
        # socket_manager.notice_console(f'获取state状态数据{values}')
        # 如果转发过来的时间戳小于或者等于当前时间戳，那就不用进行状态变更操作
        socket_manager.notice_console('执行state变更操作')
        self.change_state(False if values[0]==0 else True,values[1])
        return True

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
        # data = self.extract_majority(self.received_delegate_data)
        # prices
        prices = self.get_received_prices()
        socket_manager.notice_prices(prices)
        data = self.extract_majority_adapt(self.received_delegate_data)
        if data is not None:
            self.normal_update(data)
            self.normal_phase_done = True
            self.send2itselft_adpt(self.normal_getter)
            self.normal_send_adpt(self.normal_getter)
            # self.normal_send()
            self.scene_end = self.check_end_in_data(data)
        else:
            # 当只有两个节点的情况下，这里是none的，普通节点不会再发送数据到代表，代表会把该节点判定为作恶节点，所以测试时候至少需要三个节点
            self.logger.warn(
                'extract majority is none'
            )
    # 代表节点处理，把来自普通节点的数据进行处理
    def delegate_node_action(self, pkt: QueuedPacket):
        # 广播 如果该节点已经进来过了，直接退出（无论是从代表转发或者是微网发送过来），来自代表节点也直接退出
        # 转发完成，把数据添加到received_normal_data中
        if not self.broadcast_for_consensus_adpt(self.delegate_forward_getter,pkt):
        #if not self.broadcast_for_consensus(pkt):
            # implying pkt is a normal packet
            return
        # 程序初始化时已经初始化received_normal_data了，所有普通节点的id都在里面了。
        if pkt.origin.id not in self.received_normal_data.all.keys():
            #当self.local.is_normal 并且pkt.origin.id= self.local.id时，这个数据是自己发送给自己的
            if pkt.origin.id != self.local.id or not self.local.is_normal:
                self.logger.warn(
                    'pkt %r from unexpected normal node, expecting %s',
                    pkt,
                    tuple(self.received_normal_data.all.keys()),
                )
                return
        # 数据添加到缓存map中
        # demands
        demands = self.get_received_demands()
        socket_manager.notice_demands(demands)
        self.received_normal_data.add(pkt)

    def change_state(self,state:bool,time_span:float):
      if self.running_mark and time_span <= self.running_mark:
        socket_manager.notice_console(f'time_span {time_span} running_mark {self.running_mark}')
        return
      self.running_mark = time_span
      self.running = state
      socket_manager.notice_state((self.running,self.running_mark))
      socket_manager.notice_console(f'状态表更为{state}')
      socket_manager.set_state(self.running)

    def get_state(self) -> bool: 
      return self.running

class MultiEnergyPark(SceneTypeIII):
    final_round: int
    round_timeout_sec: float
    round_end_cache: str

    normal_value: typing.List[float]
    
    delegate_value: () # 本轮的价格
    pre_delegate_value: () # 上一轮的价格
    
    round_end_time:datetime
    node_update: NodeUpdate
    # excel文档路径
    # first_demand: str
    # demand: str
    # price_ge: str
    # hub: str
    class _Data:
        data_type: DataType
        round_id: int
        value: typing.List[float]
        is_end: bool
        
        # packet: data type 1B, round ID 4B, value 4B, end flag 1B
        pkt_fmt: str = '>BLdddB'

        __slots__ = ['data_type', 'round_id', 'value', 'is_end']


        def __init__(
            self, data_type: DataType, round_id: int , value: typing.List[float], is_end: bool
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
        def from_bytes(cls, bs: bytes) -> 'MultiEnergyPark._Data':
            values = struct.unpack(cls.pkt_fmt, bs)
            type_ = values[0]
            round_id = values[1]
            value = values[2:5]
            is_end = values[5]
            return cls(DataType(type_), round_id, value, is_end > 0)

        def pack(self) -> bytes:    
            return struct.pack(
                self.pkt_fmt,
                self.data_type.value,
                self.round_id,
                *self.value,
                1 if self.is_end else 0,
            )
    def __init__(self, final_round, round_timeout_sec,first_demand,demand,price_ge,initial,round_end_cache="./tests/cache/round_end.txt", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_round = final_round
        self.round_timeout_sec = round_timeout_sec
        # self.normal_value = self.demand_value(first_demand)
        self.node_update = NodeUpdate(demand,price_ge,initial,self.local)
        self.delegate_value = self.node_update.init_price() # 初始价格
        self.round_end_cache = round_end_cache # 缓存位置
        # self.demand = demand
        # self.price_ge = price_ge
        # self.hub = hub
    
    # 这个可能需要改为nodeUpdate的checkend
    def check_end(self) -> bool:
        return self.node_update.delegate_checkEnd(*self.pre_delegate_value,*self.delegate_value) 
        # return self.round_id >= self.final_round

    # 这个不需要改
    def check_end_in_data(self, data: bytes) -> bool:
        try:
            return self._Data.from_bytes(data).is_end
        except:
            return False
    # 这个需要更改为nodeUpdate中的delegate_update
    def delegate_update(self):
        # if self.local.is_normal:
            # pass
            # also take my own value into consideration since node won't
            # receive its own packet from micronet
            # self.delegate_value = self.normal_value
        # else:
            # self.delegate_value = 0
        self.pre_delegate_value =copy.deepcopy(self.delegate_value) 
        gd = [0 for i in range(12)]
        ed = [0 for i in range(12)]
        hd = [0 for i in range(12)]
        items = self.received_normal_data.all.items()
        items = sorted(items)
        for _, pkts in items:
            # this method is supposed to be called after clearup evil nodes
            pkt = list(pkts)[0]
            values = self._Data.from_bytes(pkt.data).value
            gd[pkt.origin.id-1] = values[0]
            ed[pkt.origin.id-1] = values[1]
            hd[pkt.origin.id-1] = values[2]
            # self.delegate_value += self._Data.from_bytes(pkt.data).value
        # price = self.delegate_value
        # 这里delegate_update会在round_id的下一轮才执行，所以这里需要减1
        self.delegate_value = self.node_update.delegate_update(gd,ed,hd,*self.delegate_value,self.round_id-1)
        # Object of type int64 is not JSON serializable
        # 转成float
        # socket_manager.notice_price((float(self.delegate_value[0]),float(self.delegate_value[1]),
        # float(self.delegate_value[2][0]),float(self.delegate_value[2][1]),float(self.delegate_value[2][2])))
        self.logger.info(f'update delegate value to {self.delegate_value}')
        self.write_price()
    def get_received_demands(self):
        time_span = time.time()
        demands = []
        items = self.received_normal_data.all.items()
        items = sorted(items)
        for origin, pkts in items:
            datas = {pkt.data for pkt in pkts}
            for data in datas:
                demand = [
                    float(val)
                    for val in self._Data.from_bytes(data).value
                ]
                demands.append([origin,*demand])
        return (demands,time_span)
    def get_current_value(self): 
        current_price = None
        current_demand = None
        if self.delegate_value:
            heat_index = int((self.local.id-1)/4)
            current_price = [self.delegate_value[0],self.delegate_value[1],self.delegate_value[2][heat_index]]
        if self.normal_value:
            current_demand = self.normal_value
        return  {"price" : current_price,"demand":current_demand,"round":self.round_id,"running":self.running}
    def get_current_demand(self):
        return self.normal_value if self.normal_value else None
    def normal_initiate(self):
        # self.normal_value = self.demand_value(self.first_demand)
        self.normal_value = self.node_update.init_demand()
        # normal_data = self.local.normal_value(4,self.normal_value)
        # return normal_data
    def normal_getter(self,node_id: int):
        # 这里需要处理一下 normal_value
        normal_data = self.local.normal_value(node_id,self.normal_value)
        # socket_manager.notice_console(f'send to {node_id} value {normal_data}')
        if not normal_data:
            return None
        data = self._Data(
            DataType.NormalToDelegate, self.round_id, normal_data, False
        ).pack()
        # socket_manager.notice_console(self.local.normal_evil)
        # real = self._Data.from_bytes(data)
        return data
    def delegate_getter(self,node_id: int):
        values = self.delegate_value
        gp = values[0]
        ep = values[1]
        hp = values[2]
        index = (int)((node_id-1)/4)
        send = [gp,ep,hp[index]]
        delegate_data = self.local.delegate_value(node_id,send)
        if not delegate_data:
            return None
        return self._Data(
            DataType.DelegateToNormal,
            self.round_id,
            send,
            self.check_end(),
        ).pack()
    def delegate_forward_getter(self,from_node,to_node,data:bytes)->[bytes,bool]:
        delegate_data = self._Data.from_bytes(data)
        delegate_value = self.local.delegate_forward_value(from_node,to_node,delegate_data.value)
        if not delegate_value:
            return None
        send_data = self._Data(
            delegate_data.data_type,
            delegate_data.round_id,
            delegate_value,
            delegate_data.is_end,
        ).pack()
        return [send_data,delegate_value == delegate_data.value]
    def state_forward_getter(self,from_node,to_node,data:bytes)->[bytes,bool]:
        return [data,True]
    # 普通节点更新数据
    # 需要使用nodeUpdate来进行update
    def normal_update(self, data: bytes):
        value = self._Data.from_bytes(data).value
        # value就是从代表中获取的最新价格 
        socket_manager.notice_price((float(value[0]),float(value[1]),float(value[2])))  
        gd,ed,hd,cost_min = self.node_update.normal_node_update(*value)
        self.normal_value = [gd,ed,hd]
        socket_manager.notice_demand((float(gd),float(ed),float(hd)))
        # self.normal_value = self._Data.from_bytes(data).value + 1
        self.logger.info(f'update normal value to {self.normal_value}')
    def get_received_prices(self):
        time_span = time.time()
        prices = []
        items = self.received_delegate_data.all.items()
        items = sorted(items)
        for _, pkts in items:
            for pkt in list(pkts):
                price = [
                    float(val)
                    for val in self.data_value(pkt)
                ]
                socket_manager.notice_console(f'prices {price}')
                prices.append([pkt.origin.id,*price])
        return (prices,time_span)
    
    def round_timeout(self) -> float:
        return self.round_timeout_sec

    def normal_data(self) -> bytes:
        data = self._Data(
            DataType.NormalToDelegate, self.round_id, self.normal_value, False
        ).pack()
        # real = self._Data.from_bytes(data)
        return data

    def delegate_data(self) -> bytes:
        return self._Data(
            DataType.DelegateToNormal,
            self.round_id,
            self.delegate_value,
            self.check_end(),
        ).pack()
    
    def state_data(self,state:bool,time_span:float) -> bytes:
        return self._Data(  
          DataType.StateChange,
          self.round_id,
          (1 if state else 0,time_span,0),
          False,
        ).pack()
    # 判断数据是否能unpack，并且判断是否是当前一轮数据
    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        try:
            data = self._Data.from_bytes(pkt.data)
            self.logger.debug(
                'got scene data %r by %d via %s',
                data,
                pkt.origin.id,
                pkt.received_from.id if pkt.received_from else 'unknown',
            )
            # 这个如果是normal节点，那么就是normal接收到的价格信息
            socket_manager.notice_console("got scene data %r by %d via %s" % (data,pkt.origin.id,pkt.received_from.id if pkt.received_from else 'unknown'))
            socket_manager.notice_console("继续接收数据")
            self.logger.debug(f'current round_id {self.round_id},node round_id {data.round_id}')
            return data.round_id == self.round_id
        except:
            self.logger.warn(f'cannot parse {pkt}', exc_info=True)
            return False

    def data_type(self, pkt: QueuedPacket) -> DataType:
        return self._Data.from_bytes(pkt.data).data_type
    def data_value(self,pkt:QueuedPacket):
        return self._Data.from_bytes(pkt.data).value
    def scene_complete(self):
        self.logger.info('scene complete, final values:')
        if self.local.is_delegate:
            self.logger.info(f'delegate value: {self.delegate_value}')
        if self.local.is_normal:
            self.logger.info(f'normal value: {self.normal_value}')
    
    def demand_value(self,demand_route) -> typing.List[int]:
        demand = pd.read_excel(demand_route, 'Sheet1')
        gasdemand = demand.loc[0,self.local.id] # 气需求
        elecdemand = demand.loc[1,self.local.id] # 电需求
        heatdemand = demand.loc[2,self.local.id] # 热需求
        return [gasdemand,elecdemand,heatdemand]
    def write_round_end_time(self,seconds):
        now = datetime.utcnow()
        self.round_end_time = now + timedelta(seconds=seconds)
        timeStruct = self.round_end_time.strftime("%Y-%m-%d %H:%M:%S")
        file = open(self.round_end_cache,mode="w")
        file.writelines(timeStruct)
        file.close()
    def read_round_end_time(self):
        file = open(self.round_end_cache,mode="r")
        timeStruct = file.readline()
        file.close()
        try:
            round_end = datetime.strptime(timeStruct,"%Y-%m-%d %H:%M:%S")
        except Exception:
            round_end = self.round_end_time
        return round_end
    def write_round_demand(self):
        pass
        if self.local.pure_normal:
            return
        file = open(f'./tests/cache/price_{self.local.id}_{self.round_id}.csv',mode='w')
        items = self.received_normal_data.all.items()
        items = sorted(items)
        for _, pkts in items:
            # this method is supposed to be called after clearup evil nodes
            if not pkts or len(pkts)==0:
               continue
            for pkt in pkts:
                #pkt = list(pkts)[0]
                received_from = pkt.received_from.id
                values = self._Data.from_bytes(pkt.data).value
                demand = f'{_},{received_from},{values[0]},{values[1]},{values[2]}\n'
                file.writelines(demand)
        file.close()
    def write_price(self):
        price = f'{self.round_id},{self.delegate_value[1]},{self.delegate_value[0]},{self.delegate_value[2][0]},{self.delegate_value[2][1]},{self.delegate_value[2][2]}\n'
        file = open(f'./tests/cache/price{self.local.id}.csv',mode='a')
        file.writelines(price)
        file.close()

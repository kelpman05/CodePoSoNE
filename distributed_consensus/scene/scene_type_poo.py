import copy
import typing
import struct 
import pandas as pd
import time
import os,inspect
import shutil
import hashlib
from abc import abstractmethod
from datetime import datetime, timedelta
from time import sleep
from ..app import socket_manager

from ..global_config import GlobalConfig
from ..core.node import Node
from ..core.node_manager import NodeManager
from ..sync_adapter import QueuedPacket, QueueManagerAdapter, normal_only
from .scene import AbstractPooScene, DataType, NodeDataMap
from .consensus.nodeUpdate import NodeUpdate

from ..config.context import poo_solv

# 场景3
class SceneTypeFour(AbstractPooScene):
    round_id: int
    received_leader_data:NodeDataMap
    received_delegate_data: NodeDataMap
    
    scene_end: bool
    running:bool
    running_mark:float
    global_config: GlobalConfig
    normal_round_end: bool
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
        self.round_id = 0
        self.received_leader_data = NodeDataMap('received_leader_data')
        self.received_delegate_data = NodeDataMap('received_delegate_data')
        self.scene_end = False
        self.running = True
        self.running_mark = time.time()
        self.normal_round_end = False
    
    @abstractmethod
    def check_end(self) -> bool:
        raise NotImplementedError()
    
    @abstractmethod
    def check_end_in_data(self, data: bytes) -> bool:
        raise NotImplementedError()
    @abstractmethod
    def solve_initiate(self):
        raise NotImplementedError()
    @abstractmethod
    def solve_copy(self):
        raise NotImplementedError()
    @abstractmethod
    def solve_value(self):
        raise NotImplementedError()
    @abstractmethod
    def solve_getter(self, int)-> bytes:
        raise NotImplementedError()
    @abstractmethod
    def solve_forward_getter(self,from_node,to_node,data:bytes)->bytes:
        raise NotImplementedError()
    @abstractmethod
    def solve_validate(self)->bool:
        raise NotImplementedError()
    @abstractmethod
    def solve_save(self, pkt: QueuedPacket):
        raise NotImplementedError()
    @abstractmethod
    def optimal_getter(self, int)-> bytes:
        raise NotImplementedError()   
    @abstractmethod
    def round_timeout(self) -> float:
        raise NotImplementedError()
    @abstractmethod
    def normal_round_timeout(self)->float:
        raise NotImplementedError()
    @abstractmethod
    def write_round_end_time(self,seconds):
        raise NotImplementedError()
    @abstractmethod
    def read_round_end_time(self):
        raise NotImplementedError()
    @abstractmethod
    def writer_init_end(self,end:True):
        raise NotImplementedError()
    @abstractmethod
    def read_init_end(self):
        raise NotImplementedError()
    def check_round_end(self):
        round_end = self.read_round_end_time()
        now = datetime.utcnow()
        while(now<round_end or not self.running):
            sleep(1)
            round_end = self.read_round_end_time()
            now = datetime.utcnow()
    def wait_for_init(self):
        init_end = self.read_init_end()
        while not init_end:
            sleep(1)
            init_end = self.read_init_end()

    def scene_complete(self):
        self.logger.info('scene completed.')

    def run(self):
        self.round_id = 1
        local_delegate_ending: bool = False
        self.seen.clear()
        self.writer_init_end(False)
        # 获取主代表，这里通过简单的id判断主代表，添加个主代表的blacklist
        # self.solve_value()
        # 主代表时，计算导出最优解，发送到其他从代表
        if self.is_leader(self.local.id):
            # 初始化文件
            self.solve_initiate()
            self.solve_copy()
            self.send2itselft_adpt(self.solve_getter)
            # 发送文件
            self.solve_send_adapt(self.solve_getter)
            self.writer_init_end(True)
        
        # 代表节点参与到poo循环中，普通节点不用
        if self.local.is_delegate:
            while not self.scene_end:
                self.logger.info(
                    f'round {self.round_id} begin'
                )
                leader = self.get_leader()
                if leader:
                    self.logger.info(f'leader node id {leader.id}')
                # step 1
                if self.round_id > 1 and self.local.is_delegate and self.is_leader(self.local.id):
                    # 初始化文件
                    self.solve_initiate()
                    self.solve_copy()
                    # 发送文件
                    self.send2itselft_adpt(self.solve_getter)
                    self.solve_send_adapt(self.solve_getter)
                    self.writer_init_end(True)
                self.logger.info("wait for init")
                self.wait_for_init()
                self.logger.info("start receive")
                # 第一轮      
                self.received_leader_data.clear()
                self.seen.clear()
                now = datetime.utcnow()
                round_end = now + timedelta(seconds=self.round_timeout())
                
                self.round(round_end)
                self.writer_init_end(False)
                # 这里稍微等待久一点，能让所有的节点都完成了上一轮的操作，这样能避免出现roud_id不一致问题
                self.check_round_end()
                # 验证结果，结果正确就把结果发送到normal节点，结束流程
                # 如果结果验证不通过，就block节点
                if self.solve_validate():
                    # self.send2itselft_adpt()
                    self.send2itselft_adpt(self.optimal_getter)
                    self.optimal_send_adapt(self.optimal_getter)
                    self.scene_end = True
                self.round_id += 1
        
        # 普通节点就一直等待结果,代表们也是普通节点
        now = datetime.utcnow()
        round_end = now + timedelta(seconds=self.normal_round_timeout())
        self.normal_round(round_end)
        
        self.scene_complete()
        self.done_cb()
    
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
            # 解压数据并且判断是否是当前一轮的数据
            if not self.is_packet_valid(pkt):
                # 如果不是当前一轮数据，或者数据不能unpack，弃包 继续循环
                self.logger.warn(f'drop invalid packet ')
                continue
            # self.normal_node_action(pkt)
            # step 2 & 3
            # self.normal_node_action(pkt)
            # step 4 pkt包含了remote等信息，看看是否是根据这个来回传给普通节点
            self.delegate_node_action(pkt)
        if(round_over):
            self.write_round_end_time(10)
            # 写入round_end时间
    # 代表节点处理，普通节点的对来自代表的数据进行处理
    def normal_round(self,round_end:datetime):
        round_over = False
        while not self.normal_round_end:
            pkt = self.adapter.wait_next_pkt(run_till=round_end)
            if pkt is None:
                # 超时结束
                self.logger.info(
                    f'receive timeout, round {self.round_id} over'
                )
                round_over = True
                break
            # 如果是state数据，不用验证周期
            # if self.state_msg_action(pkt):
            #    continue
            # 解压数据并且判断是否是当前一轮的数据
            if not self.is_packet_valid(pkt):
                # 如果不是当前一轮数据，或者数据不能unpack，弃包 继续循环
                self.logger.warn(f'drop invalid packet')
                continue
            # step 2 & 3
            # self.normal_node_action(pkt)
            # step 4 pkt包含了remote等信息，看看是否是根据这个来回传给普通节点
            self.normal_node_action(pkt)
    def delegate_node_action(self, pkt: QueuedPacket):
        # 广播解,只有leader发送过来的才会广播 
        # 如果该节点已经进来过了，直接退出（无论是从代表转发或者是微网发送过来），来自代表节点也直接退出
        # 转发完成，把数据添加到received_leader_data中
        if not self.broadcast_solve_adapt(self.solve_forward_getter,pkt):
            return
        # 数据添加到缓存map中,目前received_leader_data没啥用
        self.received_leader_data.add(pkt)
    def normal_node_action(self,pkt:QueuedPacket):
        if not self.is_delegate_packet(pkt):
            return
        self.received_delegate_data.add(pkt)
        data = self.extract_majority_adapt(self.received_delegate_data)
        if data is not None:
            self.logger.info('extract majority')
        # 判断是否接受到了大多数数据
        # self.normal_round_end = True
        self.solve_save(pkt)
    # 处理state变更数据，用来控制程序的running状态
    def get_state(self) -> bool: 
        return self.running

class MultiEnergyPoo(SceneTypeFour):
    final_round: int
    round_timeout_sec: float
    normal_round_timeout_sec:float
    round_end_cache: str
    init_end_cache: str
    ptry:str
    # 最优解
    dual_filename:str
    opt_filename:str
    # 可行解
    dual_feasible_filename:str
    opt_feasible_filename:str
    # 异常解
    dual_error_filename:str
    opt_error_filename:str
    # 接收到的解
    dual_rev_filename:str
    opt_rev_filename:str
    round_end_time:datetime
    fixed:bool# 锁定解，在作恶情况下，会判断leader直接传送过来的解为最优解，以此字段锁定，后续就不用再比较max_obj
    max_obj:float# 存储最大解，每次验证解就跟这个值比较，把最大解存储到这里，也就是最优解
    # excel文档路径
    # first_demand: str
    # demand: str
    # price_ge: str
    # hub: str
    class _Data:
        data_type: DataType
        round_id: int
        dual: bytes
        optimization:bytes
        is_end: bool
        # packet: data type 1B, value 4B, end flag 1B 总共6B
        pkt_fmt: str = '>BLBQ'
        # 类似于private功能，设置了__slots__后，只有__slots__里的属性能够被访问到
        __slots__ = ['data_type', 'round_id','dual','optimization', 'is_end']

        def __init__(
            self, data_type: DataType, round_id: int , dual: bytes,optimization:bytes,is_end: bool
        ):
            self.data_type = data_type
            self.round_id = round_id
            self.dual = dual
            self.optimization =optimization
            self.is_end = is_end
        def __repr__(self):
            return (
                f'<{self.data_type.name} round_id={self.round_id} '
                + f'{" end" if self.is_end else ""}>'
            )
        @classmethod
        def from_bytes(cls, bs: bytes) -> 'MultiEnergyPoo._Data':
            head_length = struct.calcsize(cls.pkt_fmt)
            head = bs[0:head_length]
            values = struct.unpack(cls.pkt_fmt, head)
            type_ = values[0]
            round_id = values[1]
            is_end = values[2]
            dual_length = values[3]
            value = bs[head_length:]
            #split_index = value.index(b'\x31')
            dual= value[:dual_length]
            opt=value[dual_length:]
            return cls(DataType(type_), round_id,dual, opt, is_end > 0)

        def pack(self) -> bytes:    
            base_info = struct.pack(
                self.pkt_fmt,
                self.data_type.value,
                self.round_id,
                1 if self.is_end else 0,
                len(self.dual)
            )
            #split_index = self.dual.index(b'\x1F\x1F')
            #split_index1 = self.optimization.index(b'\x1F\x1F')
            return base_info + self.dual + self.optimization
        
        @staticmethod
        def encode_value(values:typing.List[float]):
            value_fmt ='>' + 'd' * len(values)
            return struct.pack(value_fmt,*values)

        def decode_value(self):
            len1 = struct.calcsize('>d') 
            len2 = len(self.value)/len1
            value_fmt ='>' +  'd' * int(len2)
            return struct.unpack(value_fmt,self.value)

        def get_value(self):
            if self.data_type == DataType.GamsFileData:
                return self.value
            else:
                return self.decode_value()
    def __init__(self, final_round, round_timeout_sec,normal_round_timeout_sec,ptry,round_end_cache="./tests/cache/round_end.txt",init_end_cache="./tests/cache/init_end.txt", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_round = final_round
        self.round_timeout_sec = round_timeout_sec
        self.normal_round_timeout_sec = normal_round_timeout_sec
        self.round_end_cache = round_end_cache # 缓存位置
        self.init_end_cache = init_end_cache # 
        self.ptry =os.path.abspath(ptry) 
        self.max_obj = 0
        self.fixed = False
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
    def solve_value(self):
        # self.dual_filename ,self.opt_filename ,self.dual_feasible_filename,self.opt_feasible_filename,self.dual_error_filename,self.opt_error_filename  = self.get_init_filename()
        self.solve_initiate()
        ies_file = self.get_ies_filename()
        result,obj = poo_solv.validate_optimization(self.dual_error_filename,self.opt_error_filename,ies_file)
        dual = open(self.dual_filename,'rb')
        opt = open(self.opt_filename,'rb')
        dual_data = dual.read()
        opt_data = opt.read()
        dual.close()
        opt.close()
        pack = self._Data(
          DataType.LeaderToDelegate,
          self.round_id,
          dual_data,
          opt_data,
          False).pack()
        data = self._Data.from_bytes(pack)
        return data
    
    def solve_initiate(self):
        self.dual_filename ,self.opt_filename ,self.dual_feasible_filename,self.opt_feasible_filename,self.dual_error_filename,self.opt_error_filename = self.get_init_filename()
        poo_solv.solve_optimization(self.dual_filename,self.opt_filename)# 可行解（最优）
        poo_solv.solve_feasible_optimization(self.dual_feasible_filename,self.opt_feasible_filename)# 可行解（不是最优）
        poo_solv.solve_error_optimization(self.dual_error_filename,self.opt_error_filename)# 错误解
        # ies_filename = os.path.join(self.ptry,'IES_data.xls')
    def solve_copy(self):
        delegates = { delegate for delegate in self.node_manager.get_delegates() if delegate.id != self.local.id } 
        for node in delegates:
            dual_filename,opt_filename,dual_feasible_filename,opt_feasible_filename,dual_error_filename,opt_error_filename = self.get_node_init_filename(node.id)
            shutil.copy(self.dual_filename,dual_filename)
            shutil.copy(self.opt_filename,opt_filename)
            shutil.copy(self.dual_feasible_filename,dual_feasible_filename)
            shutil.copy(self.opt_feasible_filename,opt_feasible_filename)
            shutil.copy(self.dual_error_filename,dual_error_filename)
            shutil.copy(self.opt_error_filename,opt_error_filename)
            
    def solve_getter(self, node_id)-> bytes:
        dual_file = self.dual_filename
        opt_file = self.opt_filename
        if self.local.leader_evil:
            if self.local.leader_evil.follower_ignore and node_id in self.local.leader_evil.follower_ignore:
                return None
            if self.local.leader_evil.follower_feasible and node_id in self.local.leader_evil.follower_feasible:
                dual_file = self.dual_feasible_filename
                opt_file = self.opt_feasible_filename
            if self.local.leader_evil.follower_error and node_id in self.local.leader_evil.follower_error:
                dual_file = self.dual_error_filename
                opt_file = self.opt_error_filename
        self.logger.info(f'send to node {node_id},{dual_file},{opt_file}')
        dual = open(dual_file,'rb')
        opt = open(opt_file,'rb')
        dual_data = dual.read()
        opt_data = opt.read()
        dual.close()
        opt.close()
        return self._Data(
          DataType.LeaderToDelegate,
          self.round_id,
          dual_data,
          opt_data,
          False).pack()

    def get_error_solve(self)->bytes:
        self.dual_filename ,self.opt_filename ,self.dual_feasible_filename,self.opt_feasible_filename,self.dual_error_filename,self.opt_error_filename = self.get_init_filename()
        dual_file = self.dual_error_filename
        opt_file = self.opt_error_filename
        dual = open(dual_file,'rb')
        opt = open(opt_file,'rb')
        dual_data = dual.read()
        opt_data = opt.read()
        dual.close()
        opt.close()
        return self._Data(
          DataType.LeaderToDelegate,
          self.round_id,
          dual_data,
          opt_data,
          False).pack()

    def solve_forward_getter(self,from_node,to_node,data:bytes)->[bytes,bool]:
        # leader 发送给自己的节点进行转发时，使用solve_getter，会出现异常，当leader配置忽略发送时，new_data是null
        #if from_node == self.local.id:
        #    new_data = self.solve_getter(to_node)
            # self.logger.warning(f'from_node {from_node} to_node {to_node} equest {new_data == data}')
        #    return [new_data,new_data == data]
        if self.local.leader_evil and self.local.leader_evil.follower_trick_ignore and to_node in self.local.leader_evil.follower_trick_ignore:
            return [None,True]
        if self.local.leader_evil and self.local.leader_evil.follower_trick_error and to_node in self.local.leader_evil.follower_trick_error:
            new_data = self.get_error_solve()
            return [new_data,new_data == data] 
        
        return [data,True]
    
    # 判断最优解
    def solve_validate(self)->bool:
        # validate = True if self.local.leader_evil and self.local.leader_evil.follower_trick_error else self.max_obj>0
        validate = self.max_obj>0
        if not validate:
            leader = self.get_leader() 
            if leader:
                self.node_manager.block(leader.id)
        # 重置最优解和解锁定状态
        self.max_obj =0
        self.fixed = False
        return validate
    
    # 判定解，
    # 能转发就为true，不能转发就false，作恶情况下会转发错误解
    def solve_data_validate(self,data,origin_id,received_from_id):
        leader = self.get_leader()
        ies_file = self.get_ies_filename()
        _data = self._Data.from_bytes(data)
        # 这里容易发生异常，当节点有多个不同解过来时，容易导致文件覆盖
        # 计算md5值来处理文件名
        dual_md5 = hashlib.md5(_data.dual).hexdigest()
        opt_md5 = hashlib.md5(_data.optimization).hexdigest()
        dual_file,opt_file = self.get_filename(_data.data_type,origin_id,received_from_id,dual_md5,opt_md5)
        dual_writer = open(dual_file,'wb')
        dual_writer.write(_data.dual)
        dual_writer.close()
        opt_writer = open(opt_file,'wb')
        opt_writer.write(_data.optimization)
        opt_writer.close()
        result,obj = poo_solv.validate_optimization(dual_file,opt_file,ies_file)
        self.logger.info(f'solve validate {origin_id}via{received_from_id} result：{result}，obj：{obj}')

        if self.local.leader_evil and self.local.leader_evil.follower_trick_error:
            self.logger.info(f'local node is tricker,solve from anywhere always be true')
            self.max_obj = obj
            self.dual_rev_filename = dual_file
            self.opt_rev_filename = opt_file
            # 串谋情况下，把直接从leader收到的数据作为最优解
            self.fixed = True 
            return True
        # 判断串谋，存在串谋时把串谋的leader发送过来的数据(只判断直接发送过来的，转发过来的不判断)判定为最优解
        if  self.local.leader_evil and self.local.leader_evil.follower_collusion:
            # 和leader串谋时候
            if  origin_id in self.local.leader_evil.follower_collusion and origin_id == received_from_id:
                self.logger.info(f'local node is conspirator,solve from leader always be true')
                self.max_obj = obj
                self.dual_rev_filename = dual_file
                self.opt_rev_filename = opt_file
                # 串谋情况下，把直接从leader收到的数据作为最优解
                self.fixed = True 
                return True
            else :
                return False

        #if leader.id == self.local.id:
        #self.logger.info(f'local node is leader,solve validate always be true')
        #return True
        if origin_id == self.local.id:
            self.logger.info(f'local node is leader,solve validate always be true')
            self.max_obj = obj
            self.fixed = True # 锁定解
            self.dual_rev_filename = dual_file
            self.opt_rev_filename = opt_file
            return True



        # 正常判断流程，当解没锁定时，比较max_obj值，确定最优解
        # 当解锁定时，不修改max_obj值和最优解
        # result == 1时为正确解，返回true
        if not self.fixed and result ==1 and obj>self.max_obj:
            max_obj = obj
            self.dual_rev_filename = dual_file
            self.opt_rev_filename = opt_file
        
        return result == 1
    
    def solve_save(self, pkt: QueuedPacket):
        data = self._Data.from_bytes(pkt.data)
        dual_file,opt_file = self.get_pkt_filename(pkt)
        dual_writer = open(dual_file,'wb')
        dual_writer.write(data.dual)
        dual_writer.close()
        opt_writer = open(opt_file,'wb')
        opt_writer.write(data.optimization)
        opt_writer.close()
        # 解保存，这个是在normal节点中，获取到就马上保存，这个不需要用来进行其他用途
        ies_file = self.get_ies_filename()
        result,obj = poo_solv.validate_optimization(dual_file,opt_file,ies_file)
        self.logger.info(f'solve validate {pkt.origin.id}via{pkt.received_from.id}  result：{result}，obj：{obj}')
    
    def optimal_getter(self, node_id)-> bytes:
        if self.local.leader_evil and self.local.leader_evil.follower_trick_error and node_id in self.local.leader_evil.follower_trick_error:
            self.dual_rev_filename = self.dual_error_filename
            self.opt_rev_filename = self.opt_error_filename
        dual = open(self.dual_rev_filename,'rb')
        opt = open(self.opt_rev_filename,'rb')
        dual_data = dual.read()
        opt_data = opt.read()
        return self._Data(
          DataType.DelegateToNormal,
          self.round_id,
          dual_data,
          opt_data,
          False).pack()
    
    def round_timeout(self) -> float:
        return self.round_timeout_sec
    def normal_round_timeout(self)->float:
        return self.normal_round_timeout_sec
    # 判断数据是否能unpack，并且判断是否是当前一轮数据
    def is_packet_valid(self, pkt: QueuedPacket) -> bool:
        try:
            if self.node_manager.is_block(pkt.origin.id):
                self.logger.debug(f'pkt from blacklist node {pkt.origin.id}')
            data = self._Data.from_bytes(pkt.data)
            self.logger.debug(
                'got scene data %r by %d via %s',
                data,
                pkt.origin.id,
                pkt.received_from.id if pkt.received_from else 'unknown',
            )
            self.logger.debug(f'current round_id {self.round_id},node round_id {data.round_id}')
            return True if data.data_type == DataType.DelegateToNormal else data.round_id == self.round_id 
        except:
            self.logger.warn(f'cannot parse {pkt}', exc_info=True)
            return False

    def data_type(self, pkt: QueuedPacket) -> DataType:
        return self._Data.from_bytes(pkt.data).data_type
    
    def data_value(self,pkt:QueuedPacket):
        return self._Data.from_bytes(pkt.data).get_value()
    
    def scene_complete(self):
        self.logger.info('scene complete')

    def get_init_filename(self):
        return self.get_node_init_filename(self.local.id)
    def get_node_init_filename(self,node_id):
        dual_file =os.path.join(self.ptry,'init' ,f'dual_data_Node{node_id}.gdx') 
        opt_file = os.path.join(self.ptry, 'init',f'Optimization_data_Node{node_id}.gdx')
        dual_feasible_file = os.path.join(self.ptry,'init',f'dual_feasible_data_Node{node_id}.gdx') 
        opt_feasible_file = os.path.join(self.ptry,'init',f'Optimization_feasible_data_Node{node_id}.gdx')
        dual_error_file = os.path.join(self.ptry,'init',f'dual_error_data_Node{node_id}.gdx') 
        opt_error_file = os.path.join(self.ptry,'init',f'Optimization_error_data_Node{node_id}.gdx')
        return (dual_file,opt_file,dual_feasible_file,opt_feasible_file,dual_error_file,opt_error_file)
    def get_pkt_filename(self,pkt:QueuedPacket):
        data = self._Data.from_bytes(pkt.data)
        dual_md5 = hashlib.md5(data.dual).hexdigest()
        opt_md5 = hashlib.md5(data.optimization).hexdigest()
        return self.get_filename(data.data_type,pkt.origin.id,pkt.received_from.id,dual_md5,opt_md5)
    def get_filename(self,data_type:DataType,origin_id:int,received_from_id:int,dual_md5:str,opt_md5:str):
        prefix = 'delegate' if data_type == DataType.LeaderToDelegate else 'normal'
        dual_file =os.path.join(self.ptry,prefix ,f'dual_data_Node{self.local.id}_{origin_id}via{received_from_id}_{dual_md5}.gdx') 
        opt_file = os.path.join(self.ptry, prefix,f'Optimization_data_Node{self.local.id}_{origin_id}via{received_from_id}_{opt_md5}.gdx')
        return (dual_file,opt_file)
    def get_ies_filename(self):
        return os.path.join(self.ptry,'IES_data.xls')
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
    def writer_init_end(self,end:True):
        file = open(self.init_end_cache,mode="w")
        file.writelines(str(end))
        file.close()
    def read_init_end(self):
        file = open(self.init_end_cache,mode="r")
        end = file.readline()
        file.close()
        return end == "True"


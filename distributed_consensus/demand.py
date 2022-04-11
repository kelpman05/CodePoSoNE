import logging
import asyncio
import threading
import struct
import typing
import copy
from time import sleep

from .config import Config, config
from .transport.tcp.conn import TCPConnectionHandler, TCPProtocolV1
from .queue import QueueManager
from .sync_adapter import QueueManagerAdapter
from .scene.consensus.nodeUpdate import NodeUpdate
from .core.node import Node
from .core.node_manager import NodeManager, BaseNode ,default_manager

L = logging.getLogger(__name__)
class Demand:
    delegate_value: () # 本轮的价格
    pre_delegate_value: () # 上一轮的价格
    round_id:int
    node_updates:typing.List[NodeUpdate]
    node_demands:[]
    logger:logging.Logger
    def __init__(self):
        self.logger = L.getChild(f'{self.__class__.__name__}')
        self.node_updates = list()
        self.node_demands = []

    def test_demand(self,c:Config,final_round, round_timeout_sec,round_end_cache,first_demand,demand,price_ge,initial):
        # 初始化nodeupdate
        for i in range(12):
            node = c.node_manager.get_node(i+1)
            node_update=NodeUpdate(demand,price_ge,initial,node)
            self.node_updates.append(node_update)
            self.node_demands.append(None)
        # 初始化demand
        
        threads = []
        for node in c.node_manager.nodes():
            t = threading.Thread(target=self.init_demand, args=[node],name=f'init_demand {node.name}')
            threads.append(t)
            t.start()
        # asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
        for t in threads:
            t.join()
        self.delegate_value = self.node_updates[0].init_price()
        self.round_id = 1
        end = False
        while(not end and self.round_id<1000):
            self.delegate_update(self.node_demands)
            end = self.node_updates[0].delegate_checkEnd(*self.pre_delegate_value,*self.delegate_value) 
            if end:
                break
            values = self.delegate_value
            gp = values[0]
            ep = values[1]
            hp = values[2]
            update_threads=[]
            for i in range(12):
                t = threading.Thread(target=self.normal_update, args=[i,gp,ep,hp],name=f'normal_update {node.name}')
                update_threads.append(t)
                t.start()
            self.wait_for_thread(update_threads)
            self.logger.debug(f'第{self.round_id}轮结束')
            self.round_id +=1
        self.logger.debug(f'结束')
        sleep(1000)

    def delegate_update(self,node_demands):
        self.pre_delegate_value =copy.deepcopy(self.delegate_value) 
        gd = []
        ed = []
        hd = []
        for demand in node_demands:
            gd.append(demand[0])
            ed.append(demand[1])
            hd.append(demand[2])
        self.delegate_value = self.node_updates[0].delegate_update(gd,ed,hd,*self.delegate_value,self.round_id)
    def wait_for_thread(self,threads):
        for t in threads:
            t.join()
    def init_demand(self,node:Node):
        demand = self.node_updates[node.id-1].init_demand()
        self.node_demands[node.id-1] = demand
    def normal_update(self,i:int,gp,ep,hp):
        index = (int)((i)/4)
        self.node_demands[i] =self.node_updates[i].normal_node_update(gp,ep,hp[index]) 

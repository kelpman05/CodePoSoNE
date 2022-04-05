from .config import Config, config, GlobalConfig,global_config
from .transport.tcp.conn import TCPConnectionHandler, TCPProtocolV1
from .queue import QueueManager
from .sync_adapter import QueueManagerAdapter
from .scene.consensus.nodeUpdate import NodeUpdate
from distributed_consensus.demand import Demand
from time import sleep
from .app import socketio,socket_manager

import logging
import asyncio
import threading
import struct
import random

L = logging.getLogger(__name__)


async def async_main():
    """round = 0
    while True:
      round = round+1
      c: Config = config.get()
      socket_manager.notice_client('console',"接收到数据")
      socket_manager.notice_client('demand',(random.uniform(1.1,5.4),random.uniform(1.1,5.4),random.uniform(1.1,5.4)))
      socket_manager.notice_client('price',(random.uniform(1.1,5.4),random.uniform(1.1,5.4),random.uniform(1.1,5.4),random.uniform(1.1,5.4),random.uniform(1.1,5.4)))
      socket_manager.notice_client('round',round)
      # socketio.emit('demand','demand value')
      sleep(3)
    """
    # 测试
    """data_type = 1
    round_id = 1
    values = [3,4,5]
    is_end = 0
    fmt = '>BL'+'L'*len(values)+'B'
    pck = struct.pack(fmt,data_type,round_id,*values,is_end)
    t = struct.unpack(fmt,pck)
    data_type = t[0]
    round_id = t[1]
    values = t[2:5]
    is_end = t[5]"""
    
    # 获取配置
    c: Config = config.get()
    g: GlobalConfig = global_config.get()
    L.debug('using config: %r', c)
    L.info(f'local node is normal: {c.local_node.is_normal}')
    L.info(f'local node is delegate: {c.local_node.is_delegate}')

    queue = QueueManager(c.local_node, c.node_manager)

    loop = asyncio.get_running_loop()
    adapter = QueueManagerAdapter(queue, loop)
    # demandtest = Demand()
    # demandtest.test_demand(c,**c.scene_parameters)
    conn = TCPConnectionHandler(
        c.local_node, c.node_manager, queue, TCPProtocolV1,loop
    )
     # 异步方法 获取EventLoop
    
    # asyncio.Event() 用来协同工作
    done = asyncio.Event()
    # 启动代表 启动监听（代表）、连接其他代表，目前貌似不论是否是代表，都会启动监听。
    if await conn.setup_and_wait_micronet(
        timeout=c.transport_parameters['tcpv1']['micronet_init_sec']
    ):
    #if True :
        # 普通节点发送数据
        L.info('micronet established')
        scene = c.scene_class(
            local=c.local_node,
            node_manager=c.node_manager,
            adapter=adapter,
            done_cb=lambda: loop.call_soon_threadsafe(done.set),
            global_config = g,
            **c.scene_parameters
        )
        # 开启新线程，设置为守护线程，当主线程退出时，子线程也会退出
        t = threading.Thread(target=scene.run, daemon=True)
        t.start() 
        # asyncio.Event() 用来协同工作，让多个协程同步执行
        # done.wait()会一直等待，直到done.set为止，在另外的线程里使用done.set时，需要使用loop.call_soon_threadsafe来调用
        # 如上面的scene 的done_cb回调函数
        await done.wait()


def bootstrap():
    asyncio.run(async_main())

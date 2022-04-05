import contextvars
import logging
import multiprocessing
import click
import threading

import coloredlogs

from ..bootstrap import bootstrap
from ..config import Config, config,GlobalConfig,global_config
from .root import root
from ..app import app,socketio,socket_manager
from ..app.app_config import AppConfig
L = logging.getLogger(__name__)
local = threading.local()



@root.command()
@click.option(
    '-c',
    '--config-file',
    help='path to configuration file',
    type=click.File(mode='rb'),
    default='./config.yaml',
)
@click.option(
  '-h',
  '--host',
  help="web server host,--with-ui must be true",
  type=str,
  default="127.0.0.1"
)
@click.option(
  '-p',
  '--port',
  help="web server port,--with-ui must be true",
  type=int,
  default=5000
)

@click.argument('LOCAL_NODE_ID', required=True, nargs=1, type=int)
def run(config_file,host,port,local_node_id):

    coloredlogs.install(level=logging.INFO)
    L.info(f'loading config {config_file.name}')
    # 加载配置
    config_obj = Config.from_yaml(local_node_id, config_file)
    
    if config_obj.scene_class.__name__ == "SimpleSum" :
        run_simple_sum(config_obj)
    elif config_obj.scene_class.__name__ == "MultiEnergyPark":
        run_multi_energy_park(config_obj,host,port)
    elif config_obj.scene_class.__name__ == "MultiEnergyPoo" :
        run_multi_energy_poo(config_obj)
    else:
        raise Exception(f'scene type {config_obj.scene_class.__name__} is not available')
    # appThread.join()
    print("启动完毕")

def run_simple_sum(config_obj):
    coloredlogs.install(level=config_obj.log_level, reconfigure=True)
    # 设置上下文变量  
    g_config = GlobalConfig()
    bootstrapProcess(config_obj,g_config)

def run_multi_energy_park(config_obj,host,port):
    # coloredlogs.install(level=config_obj.log_level, reconfigure=True)
    # coloredlogs.install(level=logging.INFO)
    coloredlogs.install(level=config_obj.log_level, reconfigure=True)
    # 设置上下文变量  

    g_config = GlobalConfig()

    appThread = threading.Thread(target=appProcess, daemon=True,args=(config_obj,g_config,host,port))
    appThread.start()

    bootstrapThread = threading.Thread(target=bootstrapProcess,daemon=True,args=(config_obj,g_config))
    bootstrapThread.start()

    bootstrapThread.join()
def run_multi_energy_poo(config_obj):
    coloredlogs.install(level=config_obj.log_level, reconfigure=True)
    # 设置上下文变量  
    g_config = GlobalConfig()
    bootstrapProcess(config_obj,g_config)
# 多能仿真
def bootstrapProcess(config_obj,g_config):
    config.set(config_obj)
    global_config.set(g_config)
    # 拷贝上下文
    ctx = contextvars.copy_context()
    # 以获取到的上下文来执行方法
    ctx.run(bootstrap)

# 页面站点
def appProcess(config_obj,g_config,host,port):
    print("接收数据：",config_obj.log_level)
    # config.set(config_obj)
    # config_obj = Config.from_yaml(local_node_id, config_file)
    # app_config:AppConfig = AppConfig(config_obj)
    # local.config = config_obj
    app.config['NODE'] = config_obj
    app.config['GLOBAL'] = g_config
    socketio.start_background_task(target=socket_manager.run)
    socketio.start_background_task(target=socket_manager.run_state)
    socketio.run(app=app,host=host,port=port)
    
    # app.run(host=host,port=port)



# app的上下文变量，用来存储管道对象和websocket对象

from ..config import Config,GlobalConfig
from flask import current_app
from werkzeug.local import LocalProxy
from functools import partial

def get_config():
  return current_app.config.get('NODE')
def get_global_config():
  return current_app.config.get('GLOBAL')
# LocalProxy 作用：使用的时候才获取，每次使用都获取最新值
config:Config = LocalProxy(partial(get_config))
global_config:GlobalConfig= LocalProxy(partial(get_global_config))
from collections import deque
from flask_socketio import SocketIO

import typing
import eventlet 


class WebSocketMessage():
  even:str
  message:object
  def __init__(self,even:str,message:object):
    super().__init__()
    self.even = even
    self.message = message

class WebSocketManage():
  messages: typing.Deque[WebSocketMessage]
  state_message: typing.Deque[WebSocketMessage]
  switch = False 
  completed = False
  socketio:SocketIO
  # webSocket 集合
  def __init__(self,socketio:SocketIO):
    super().__init__()
    self.socketio = socketio
    self.switch = True
    self.completed = False
    self.messages = deque()
    self.state_message = deque()
  # websocket 注入
  def register(self):
    pass
  # 通知客户端
  def notice_client(self,even:str,massage:object):
    self.messages.append(WebSocketMessage(even=even,message=massage))
  def notice_round(self,round:int):
    self.messages.append(WebSocketMessage(even="round",message=round))
  def notice_demand(self,demand):
    self.messages.append(WebSocketMessage(even="demand",message=demand))
  def notice_demands(self,demands):
    self.messages.append(WebSocketMessage(even="demands",message=demands))
  def notice_price(self,price):
    self.messages.append(WebSocketMessage(even="price",message=price))
  def notice_prices(self,prices):
    self.messages.append(WebSocketMessage(even="prices",message=prices))
  def notice_console(self,message):
    self.messages.append(WebSocketMessage(even="console",message=message))
  def notice_blacklist(self,blacklist):
    self.messages.append(WebSocketMessage(even="blacklist",message=blacklist))
  def notice_state(self,data):
    # self.messages.append(WebSocketMessage(even="state",message=data))
    self.state_message.append(WebSocketMessage(even="state",message=data))
  def run(self):
    while not self.completed:
      while len(self.messages)>0 and self.switch:
        message = self.messages.pop()
        self.socketio.emit(message.even,message.message)
      #eventlet.sleep(0.5)
      self.socketio.sleep(0.5)
  def run_state(self):
    while not self.completed:
      while len(self.state_message)>0:
        message = self.state_message.pop()
        self.socketio.emit(message.even,message.message)
      self.socketio.sleep(0.5)

  def stop(self):
    self.switch = False
  def start(self):
    self.switch = True
  def set_state(self,switch:bool):
    self.switch = switch
  def completed(self):
    self.completed = True



  
import typing
from typing import Dict,Set,Callable
EvilGetter = Callable[[float,float,float], typing.List[float]]

class NormalEvil():
    # 发送需求时，忽略代表
    demand_ignore:typing.List[int]
    # 发送需求时作恶目标(代表)
    demand_target:typing.List[int]
    # 发送需求时，作恶数据倍率
    demand_rate:float
    def __init__(self,demand_ignore:typing.List[int],demand_target:typing.List[int],demand_rate:float = None):
        self.demand_ignore = demand_ignore
        self.demand_target = demand_target
        self.demand_rate = demand_rate

    def evil_value(self,node_id:int,values: typing.List[float]):
        #if self.ignore_all:
        #    return None
        if self.demand_ignore and node_id in self.demand_ignore:
            return None

        if self.demand_target and node_id in self.demand_target and self.demand_rate:
            return (values[0]*self.demand_rate,values[1]*self.demand_rate,values[2]*self.demand_rate)
        #getter =None if not self.diffrence else self.diffrence.get(node_id)
        #if getter:
        #    return getter(values[0],values[1],values[2])
        else:
            return values

class DelegateEvil():
    # 发送价格时忽略微网
    price_ignore:typing.List[int]
    # 发送价格时作恶目标(微网)
    price_target:typing.List[int]
    # 发送价格时作恶数据倍率
    price_rate:float
    # 转发时忽略代表
    broadcast_ignore:typing.List[int]
    # 转发时串谋微网
    broadcast_collusion:typing.List[int]
    # 转发时作恶目标(代表)
    broadcast_target:typing.List[int]
    # 转发时作恶数据倍率
    broadcast_rate:float
    def __init__(self,price_ignore:typing.List[int],price_target:typing.List[int],price_rate:float,
    broadcast_ignore:typing.List[int],broadcast_collusion:typing.List[int],broadcast_target:typing.List[int],broadcast_rate:float = None):
        self.price_ignore = price_ignore
        self.price_target = price_target
        self.price_rate = price_rate
        self.broadcast_ignore = broadcast_ignore
        self.broadcast_collusion = broadcast_collusion
        self.broadcast_target = broadcast_target
        self.broadcast_rate = broadcast_rate
    def evil_value(self,node_id:int,values: typing.List[float]):
        if self.price_ignore and node_id in self.price_ignore:
            return None
        if self.price_target and node_id in self.price_target and self.price_rate:
            return (values[0]*self.price_rate,values[1]*self.price_rate,values[2]*self.price_rate)
        return values
    def forward_evil_value(self,from_node_id:int,to_node_id:int,values: typing.List[float]):
        if self.broadcast_ignore and to_node_id in self.broadcast_ignore:
            return None
        if self.broadcast_collusion and from_node_id in self.broadcast_collusion and self.broadcast_target and to_node_id in self.broadcast_target and self.broadcast_rate:
            return (values[0]*self.broadcast_rate,values[1]*self.broadcast_rate,values[2]*self.broadcast_rate) 
        return values
    
class LeaderEvil():
    follower_ignore: typing.List[int]
    follower_error: typing.List[int]
    follower_feasible: typing.List[int]
    follower_collusion: typing.List[int]
    follower_trick_error: typing.List[int]
    follower_trick_ignore: typing.List[int]
    def __init__(self,follower_ignore:typing.List[int],follower_error:typing.List[int],follower_feasible:typing.List[int],follower_collusion:typing.List[int],follower_trick_error:typing.List[int],follower_trick_ignore: typing.List[int]):
        self.follower_ignore = follower_ignore
        self.follower_error = follower_error
        self.follower_collusion = follower_collusion
        self.follower_feasible = follower_feasible
        self.follower_trick_error = follower_trick_error
        self.follower_trick_ignore = follower_trick_ignore
    

import typing

from .node_manager import AutoRegisterNode
from OpenSSL.crypto import PKey
from pprint import pformat
from ipaddress import ip_address
from .node_evil import NormalEvil,DelegateEvil,LeaderEvil

class Node(AutoRegisterNode):
    ip: str
    port: int
    public_key: typing.Union[str, PKey]
    private_key: typing.Union[str, PKey, None]
    hub: str
    normal_evil: NormalEvil
    delegate_evil: DelegateEvil
    leader_evil: LeaderEvil
    def __init__(
        self,
        id,
        name,
        ip,
        port,
        public_key,
        normal_evil:NormalEvil,
        deledate_evil:DelegateEvil,
        leader_evil: LeaderEvil,
        private_key=None,
        hub= None,
        manager=None,
        is_delegate=False,
        is_normal=False,
        is_blacked=False
    ):
        super().__init__(
            id,
            manager=manager,
            name = name,
            is_delegate=is_delegate,
            is_normal=is_normal,
            is_blacked=is_blacked,
        )
        self.ip = ip
        self.port = port
        self.public_key = public_key
        self.private_key = private_key
        self.hub = hub
        self.normal_evil = normal_evil
        self.delegate_evil = deledate_evil
        self.leader_evil = leader_evil

    def normal_value(self,send_node_id:int,values:typing.List[float]):
        if self.normal_evil:
            return self.normal_evil.evil_value(send_node_id,values)
        return values
    def delegate_value(self,send_node_id:int,values:typing.List[float]):
        if self.delegate_evil:
            return self.delegate_evil.evil_value(send_node_id,values)
        return values
    def delegate_forward_value(self,from_node_id:int, send_node_id:int,values:typing.List[float]):
        if self.delegate_evil:
            return self.delegate_evil.forward_evil_value(from_node_id,send_node_id,values)
        return values
        
    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            'id': self.id,
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
            'public_key': self.public_key,
            'private_key': self.private_key,
            'is_delegate': self.is_delegate,
            'is_normal': self.is_normal,
            'is_blacked': self.is_blacked,
        }

    def __repr__(self):
        dict_str = (
            pformat(self.to_dict(), width=10000, compact=True)
            .strip("{}")
            .replace(', ', ' ')
            .replace(': ', ':')
        )
        return f'<Node {dict_str}>'

    def sort_key(self) -> int:
        return (int(ip_address(self.ip)) << 16) | self.port

    def __lt__(self, value):
        return self.sort_key() < value.sort_key()

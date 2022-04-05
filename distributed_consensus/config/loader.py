import importlib
import logging
import typing
from pathlib import Path
from pprint import pformat

import yaml

from ..core.node import Node
from ..core.node_manager import NodeManager, default_manager
from ..crypto import _extract_certificate, _load_private_key, _load_public_key
from ..crypto.util import read_all_str
from ..core.node_evil import EvilGetter,NormalEvil,DelegateEvil,LeaderEvil
L = logging.getLogger(__name__)


class Config:
    local_node: typing.Optional[Node]
    nodes: typing.List[Node]
    node_manager: NodeManager
    log_level: int
    scene_class: typing.Type
    scene_parameters: typing.Dict[str, typing.Any]
    cwd: Path
    transport_parameters: typing.Dict[str, typing.Dict[str, typing.Any]]
    # 作恶
    evil_type: str
    
    __slots__ = [
        'local_node',
        'nodes',
        'node_manager',
        'log_level',
        'scene_class',
        'scene_parameters',
        'transport_parameters',
        'cwd',
    ]

    def __init__(
        self,
        cwd: typing.Union[Path, str],
        node_manager: typing.Optional[NodeManager] = None,
    ):
        super().__init__()
        if node_manager is None:
            node_manager = default_manager()
        self.node_manager = node_manager
        self.nodes = list()
        self.log_level = logging.INFO
        self.cwd = Path(cwd).expanduser().absolute()
        self.local_node = None
        self.transport_parameters = {}

    def create_node(
        self,
        node_id: int,
        ip: str,
        port: int,
        private_key_file: str,
        public_key_file: str,
        hub: str,
        is_delegate: bool,
        is_normal: bool,
        is_local: bool,
        transport: str,
        normal_evil = None,
        delegate_evil = None,
        leader_evil = None
    ):
        if transport != 'tcpv1':
            L.fatal(f'unsupported transport {transport}')
            raise RuntimeError(f'unsupported transport {transport}')
        private_key_path = self.cwd / private_key_file
        public_key_path = self.cwd / public_key_file

        if is_local:
            if not private_key_path.is_file():
                L.fatal(f'cannot open private key {private_key_file!s}')
                raise FileNotFoundError(str(private_key_path))
            try:
                private_key = _load_private_key(
                    _extract_certificate(read_all_str(private_key_path))
                )
            except:  # noqa
                L.fatal(f'invalid private key {private_key_file!s}')
                raise
        else:
            private_key = None

        if not public_key_path.is_file():
            L.fatal(f'cannot open public key {public_key_path!s}')
            raise FileNotFoundError(str(public_key_path))
        try:
            public_key = _load_public_key(
                _extract_certificate(read_all_str(public_key_path))
            )
        except:  # noqa
            L.fatal(f'invalid public key {public_key_path!s}')
            raise

        if node_id < 0 or node_id > 0xFFFFFFFF:
            raise ValueError(f'invalid node id {node_id}')
        
        normal = None
        if normal_evil:
            #diffrence = normal_evil.get('diffrence')
            #if diffrence:
            #    diffrence = dict({
            #        dif['node']:eval(dif['data'])
            #        for dif in diffrence
            #    }) 
            #else:
            #    diffrence = None
            demand_ignore = normal_evil.get('demand_ignore')
            demand_target = normal_evil.get('demand_target')
            demand_rate = normal_evil.get('demand_rate')
            #normal = NormalEvil(ignore,ignore_all,diffrence) 
            normal = NormalEvil(demand_ignore = demand_ignore,demand_target= demand_target,demand_rate= demand_rate)
        delegate = None
        if delegate_evil:
            price_ignore = delegate_evil.get('price_ignore')
            price_target = delegate_evil.get('price_target')
            price_rate = delegate_evil.get('price_rate')
            broadcast_ignore = delegate_evil.get('broadcast_ignore')
            broadcast_collusion = delegate_evil.get('broadcast_collusion')
            broadcast_target = delegate_evil.get('broadcast_target')
            broadcast_rate = delegate_evil.get('broadcast_rate')
            #broadcast = delegate_evil.get('broadcast')
            #diffrence =None if broadcast is None else broadcast.get('diffrence')
            #if diffrence:
            #    diffrence = dict({
            #        dif['node']:eval(dif['data'])
            #        for dif in diffrence
            #    }) 
            #else:
            #    diffrence = None
            #from_nodes = None if broadcast is None else broadcast.get('from')
            #delegate = DelegateEvil(ignore,ignore_all,from_nodes,diffrence)
            delegate = DelegateEvil(price_ignore = price_ignore,price_target= price_target,price_rate= price_rate,
            broadcast_ignore= broadcast_ignore,broadcast_collusion= broadcast_collusion,broadcast_target= broadcast_target,broadcast_rate= broadcast_rate)
        leader = None
        if leader_evil:
            follower_ignore = leader_evil.get('follower_ignore')
            follower_error = leader_evil.get('follower_error')
            follower_feasible = leader_evil.get('follower_feasible')   
            follower_collusion = leader_evil.get('follower_collusion')
            follower_trick_error = leader_evil.get('follower_trick_error')
            follower_trick_ignore = leader_evil.get('follower_trick_ignore')
            leader = LeaderEvil(follower_ignore,follower_error,follower_feasible,follower_collusion,follower_trick_error,follower_trick_ignore)
        node = Node(
            node_id,
            ip,
            port,
            public_key,
            normal,
            delegate,
            leader,
            private_key,
            is_delegate=is_delegate,
            is_normal=is_normal,
            manager=self.node_manager,
            hub=hub,
        )
        self.nodes.append(node)
        if is_local:
            if self.local_node is not None:
                L.fatal(
                    f'multiple local nodes, {self.local_node!r} and {node!r}'
                )
                raise RuntimeError('multiple local nodes')
            self.local_node = node

    @staticmethod
    def parse_log_level(name: str) -> int:
        level = logging.getLevelName(name.upper())
        if isinstance(level, int):
            return level
        raise ValueError(f'{name} is not a valid log level')

    @classmethod
    def from_yaml(
        cls,
        local_node_id: int,
        yaml_file: typing.Union[str, Path, typing.BinaryIO],
    ):
        if isinstance(yaml_file, str):
            yaml_file = Path(yaml_file)
        if isinstance(yaml_file, Path):
            yaml_file = open(yaml_file, 'rb')

        obj = yaml.safe_load(yaml_file)
        # classmethod标志的方法不需要实例化就能够调用，但是必须要cls作为第一个参数
        # 在这里通过cls实例化对象
        ins = cls(Path(yaml_file.name).parent)
        for node_id, node in obj.get('nodes', {}).items():
            # create_node 会创建Node，Node对象的父类构造函数会把Node添加到NodeManager
            ins.create_node(node_id, is_local=local_node_id == node_id, **node)
        # 可以直接通过NodeManager获取到Node对象
        if ins.node_manager.get_node(local_node_id) is None:
            L.fatal(f'local node {local_node_id} not defined in nodes section')
            raise RuntimeError(
                f'local node {local_node_id} not defined in nodes section'
            )

        ins.log_level = cls.parse_log_level(obj.get('log_level', 'info'))
        if 'scene' not in obj or 'class' not in obj['scene']:
            L.fatal(f'cannot find scene.class section in {yaml_file.name}')
            raise KeyError('scene.class')

        ins.transport_parameters = obj.get('transport', {})

        scene = obj['scene']
        ins.scene_parameters = scene.get('params', {})
        try:
            mod, clas = scene['class'].rsplit('.', 1)
            scene_module = importlib.import_module(mod)
            ins.scene_class = getattr(scene_module, clas)
        except:  # noqa
            L.fatal(f'{scene["class"]} is not a valid class path')
            raise

        return ins

    def __repr__(self):
        conf = (
            pformat(
                {
                    k: getattr(self, k)
                    for k in self.__dir__()
                    if not k.startswith('__')
                    and not callable(getattr(self, k))
                },
                width=10000,
                compact=True,
            )
            .replace(', ', ' ')
            .replace(': ', ':')
        )
        return f'<Config {conf}>'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    config = Config.from_yaml(1, 'config.sample.yaml')
    print(config)

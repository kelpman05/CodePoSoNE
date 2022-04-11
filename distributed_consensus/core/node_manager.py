from typing import TYPE_CHECKING, Any, Optional, Set
from weakref import WeakSet, WeakValueDictionary


class BaseNode:
    id: int
    name: str
    is_delegate: bool
    is_blacked: bool
    is_normal: bool

    def __init__(
        self, id,name, is_delegate=False, is_normal=True, is_blacked=False,
    ):
        super().__init__()
        self.id = id
        self.name = name
        self.is_delegate = is_delegate
        self.is_normal = is_normal
        self.is_blacked = is_blacked
    # 只是普通节点
    @property
    def pure_normal(self) -> bool:
        return self.is_normal and not self.is_delegate
    # 只是代表节点
    @property
    def pure_delegate(self) -> bool:
        return self.is_delegate and not self.is_normal

    @property
    def dual_role(self) -> bool:
        return self.is_delegate and self.is_normal


if TYPE_CHECKING:
    WeakNodeSet = WeakSet[BaseNode]
    WeakNodeDictionary = WeakValueDictionary[int, BaseNode]
else:
    WeakNodeSet = Any
    WeakNodeDictionary = Any


class NodeManager:
    _all: WeakNodeSet
    _by_id: WeakNodeDictionary
    _all_num: int
    _delegate_num: int

    def __init__(self):
        super().__init__()
        self._all = WeakSet()
        self._by_id = WeakValueDictionary()
        self._all_num = 0
        self._delegate_num = 0

    def register(self, node: BaseNode):
        assert node not in self._all, f'duplicate node {node!r}'
        assert node not in self._by_id, f'duplicate node ID {node.id!r}'
        self._all.add(node)
        self._by_id[node.id] = node
        self._all_num += 1
        if node.is_delegate:
            self._delegate_num += 1

    def get_node(
        self, id: int, default: Optional[BaseNode] = None
    ) -> Optional[BaseNode]:
        return self._by_id.get(id, default=default)

    def get_delegates(self):
        return {node for node in self._all if node.is_delegate}
    
    def block(self, id: int):
        node = self.get_node(id)
        if node:
            node.is_blacked = True
    def is_block(self,id:int):
        node = self.get_node(id)
        if node:
            return node.is_blacked
        return True
    def block_nodes(self)->Set[BaseNode]:
        nodes = {
          node
          for node in self._all
          if node.is_blacked
        }
        return nodes
    
    def nodes(self) -> Set[BaseNode]:
        return set(self._all)

    @property
    def delegate_num(self) -> int:
        return self._delegate_num

    @property
    def all_num(self) -> int:
        return self._all_num

    def __len__(self) -> int:
        return self._all_num


__node_manager_singleton = NodeManager()


def replace_default_manager(manager: NodeManager):
    global __node_manager_singleton
    prev = __node_manager_singleton
    __node_manager_singleton = manager
    return prev


def default_manager() -> NodeManager:
    # 若想在函数内部对函数外的变量进行操作，就需要在函数内部声明其为global
    # 这里的方法是在模块内，不是在类内部，调用外部变量时需要使用global来标志变量
    global __node_manager_singleton
    return __node_manager_singleton


class AutoRegisterNode(BaseNode):
    def __init__(self, id: int, manager: NodeManager = None, *args, **kwargs):
        super().__init__(id, *args, **kwargs)
        manager = default_manager() if manager is None else manager
        manager.register(self)

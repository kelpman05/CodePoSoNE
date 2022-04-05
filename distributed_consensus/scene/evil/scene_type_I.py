from ...core.node import Node
from ..scene import DataType
from ..scene_type_I import SimpleAdd
from .evil_base import EvilNormalMixIn


class SimpleAddEvilNormal(EvilNormalMixIn, SimpleAdd):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        assert self.local.is_normal, "local node must have normal role"

    def normal_data(self) -> bytes:
        return self._Data(
            DataType.NormalToDelegate, self.round_id, self.normal_value, False
        ).pack()

    def evil_data(self, delegate: Node, normal_data: bytes) -> bytes:
        """ send 0 to some delegates

        A simple evil data example, override to create complex behaviours """
        return self._Data(
            DataType.NormalToDelegate, self.round_id, 0, False
        ).pack()

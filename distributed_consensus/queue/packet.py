import typing
from binascii import b2a_hex

from ..core.node_manager import BaseNode


class QueuedPacket(typing.NamedTuple):
    origin: BaseNode
    received_from: typing.Optional[BaseNode]
    send_to: BaseNode
    data: bytes
    full_packet: typing.Optional[bytes]

    @property
    def is_forwarding(self) -> bool:
        return (
            self.received_from is not None
            and self.origin != self.received_from
        )

    def __repr__(self):
        forward = f'{self.received_from.name if self.is_forwarding else "-"}'
        path = f'{self.origin.name}={forward}=>{self.send_to.name}'

        return f'<QueuedPacket {path} data="{b2a_hex(self.data)!s}">'

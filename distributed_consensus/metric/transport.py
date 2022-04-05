from .timestamp import TimestampMixin
from datetime import datetime
from typing import Optional


class Transport(TimestampMixin):
    ts: datetime
    local_ip: Optional[str]
    local_port: Optional[int]
    remote_ip: Optional[str]
    remote_port: Optional[int]
    status: str

    def __init__(self, local_ip, local_port, remote_ip, remote_port, status):
        super().__init__()
        self.register_timestamp('ts', reset=True)
        self.ts = datetime.utcnow()
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.status = status

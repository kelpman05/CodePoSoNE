import struct
import typing
from binascii import b2a_hex
from datetime import datetime
from logging import getLogger

from ...core.bytes_buffer import BytesBuffer
from ...core.node import Node
from ...core.node_manager import NodeManager
from ...crypto import SHA256, sign, verify
from ...queue.packet import QueuedPacket

L = getLogger(__name__)

# 该类主要用来解析消息
class TCPProtocolV1:
    version: int = 1

    digest: str = SHA256

    # version 1B, timestamp 8B, node ID 4B, 4096bits RSA sign 512B
    handshake_struct: str = '>BQL512s'

    handshake_timeout: int = 5

    # original node ID 4B + data len 4B
    packet_header_struct: str = '>LL'

    # instance properties
    local: Node
    remote: typing.Optional[Node]
    handshake_recv_len: int
    header_recv_len: int
    signature_len: int
    buf: BytesBuffer
    node_manager: NodeManager

    def __init__(
        self,
        node_manager: NodeManager,
        local: Node,
        remote: typing.Optional[Node] = None,
    ):
        super().__init__()
        self.node_manager = node_manager
        self.local = local
        self.remote = remote
        self.handshake_recv_len = struct.calcsize(self.handshake_struct)
        self.header_recv_len = struct.calcsize(self.packet_header_struct)
        self.signature_len = 4096 // 8
        self.version = 1
        self.buf = BytesBuffer()
        if remote:
            # local is client
            self.logger = L.getChild('TCPProtocolV1').getChild(
                f'{local.id}->{remote.id}'
            )
        else:
            # local is server, need handshake
            self.logger = L.getChild('TCPProtocolV1').getChild(
                f'{local.id}<-UNKNOWN'
            )

    def peek_header(self) -> typing.Optional[typing.Tuple]:
        buf_len = len(self.buf)
        if buf_len < self.header_recv_len:
            return None

        header = struct.unpack(
            self.packet_header_struct, self.buf.peek(self.header_recv_len),
        )
        return header

    def feed_buffer(self, bs: bytes):
        self.logger.debug('feeding %d', len(bs))
        self.buf.write(bs)

    # 返回包、origin_node_id、是否解析成功
    def decode(self, bs: bytes) -> [typing.Optional[QueuedPacket],int,bool]:
        assert self.remote is not None, 'handshake incomplete'
        if bs:
            self.feed_buffer(bs)

        header = self.peek_header()
        if header is None:
            # insufficient data
            return [None,None,True]

        original_id, pkt_len = header
        full_len = self.header_recv_len + pkt_len + self.signature_len
        if len(self.buf) < full_len:
            return [None,original_id,True]

        original_node = self.node_manager.get_node(original_id)
        if original_node is None:
            self.logger.warn(f'cannot find original node {original_id}, drop')
            return [None,original_id,False]
        assert isinstance(original_node, Node)

        # drop header which has been peeked
        header_bs = self.buf.read(self.header_recv_len)
        pkt = self.buf.read(header[1])
        signature = self.buf.read(self.signature_len)
        if not verify(
            original_node.public_key, signature, header_bs + pkt, self.digest
        ):
            self.logger.warn(
                'pkt signature corrupted, drop %d bytes', len(pkt)
            )
            return [None,original_id,False]

        # self.logger.debug('pkt parsed & verified %s', b2a_hex(pkt))
        self.logger.debug('pkt parsed & verified %d', len(pkt))

        recieve = QueuedPacket(
            origin=original_node,
            received_from=self.remote,
            send_to=self.local,
            data=pkt,
            full_packet=header_bs + pkt + signature,
        )
        return [recieve,original_id,True]

    def encode(self, pkt: QueuedPacket) -> bytes: 
        if pkt.origin != self.local and pkt.full_packet is not None:
            return pkt.full_packet
        original_node = self.node_manager.get_node(pkt.origin.id)
        data: bytes = pkt.data
        #self.logger.debug('pkt to encode %s', b2a_hex(data))
        self.logger.debug('pkt to encode %d', len(data))
        header = struct.pack(
            self.packet_header_struct, original_node.id, len(data)
        )
        self.logger.debug('header: %s', b2a_hex(header))
        bs = header + data
        # 只能用本地私钥进行加密
        # 可能local之外的node没有private_key
        # signature = sign(self.local.private_key, bs, self.digest)
        signature = sign(self.local.private_key, bs, self.digest)
        # self.logger.debug('encoded: %s', b2a_hex(bs))
        return bs + signature
    # 还需要再读取 num_to_read 个字节才能解析header或者完整的包
    def num_to_read(self) -> int:
        """ return minimal number of bytes needed to parse next packet """
        buf_len = len(self.buf)
        self.logger.debug('buf length %d', buf_len)

        header = self.peek_header()
        if header is None:
            self.logger.debug('shorter than header %d', self.header_recv_len)
            return self.header_recv_len - buf_len

        original_id, pkt_len = header
        body_len = self.header_recv_len + pkt_len + self.signature_len
        self.logger.debug('expected body length %d', body_len)

        return body_len - buf_len if buf_len < body_len else 0

    def generate_handshake(self):
        timestamp = int(datetime.utcnow().timestamp())
        bs = struct.pack(
            self.handshake_struct,
            self.version,
            timestamp,
            self.local.id,
            b'',  # occupier for signature 占位
        )[: -self.signature_len]
        bs = bs + sign(self.local.private_key, bs, self.digest)
        self.logger.debug('handshake to send: %s', b2a_hex(bs))
        return bs

    def parse_handshake(self, bs: bytes) -> typing.Optional[Node]:
        assert self.remote is None, 'double handshake'
        assert len(bs) == self.handshake_recv_len, 'invalid handshake bs'

        local_timestamp = datetime.utcnow().timestamp()
        self.logger.debug('handshake received: %s', b2a_hex(bs))
        # fmt 大端模式，byte转换
        version, timestamp, node_id, signature = struct.unpack(
            self.handshake_struct, bs
        )

        if version != self.version:
            self.logger.warn('invalid version %d', version)
            return None
        if abs(timestamp - local_timestamp) > self.handshake_timeout:
            self.logger.warn(
                'time difference exceeds tolerance: R:%s/%s L:%s/%s',
                timestamp,
                datetime.utcfromtimestamp(timestamp),
                local_timestamp,
                datetime.utcfromtimestamp(local_timestamp),
            )
            return None
        node = self.node_manager.get_node(node_id)
        if node is None:
            self.logger.warn('unconfigured node ID %d', node_id)
            return None

        assert isinstance(node, Node)
        # 数组操作 从开头到倒数第self.signature_len个。倒数第self.signature_len个到最后
        data, signature = bs[: -self.signature_len], bs[-self.signature_len :]
        if not verify(node.public_key, signature, data, self.digest):
            self.logger.warn('corrupted handshake packet')
            return None
        self.remote = node
        self.logger = L.getChild('TCPProtocolV1').getChild(
            f'{self.local.id}<-{self.remote.id}'
        )
        self.logger.info('handshake done')
        return node

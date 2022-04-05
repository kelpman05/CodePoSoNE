import unittest
from datetime import datetime
from unittest.mock import patch

from distributed_consensus.core.node import Node
from distributed_consensus.core.node_manager import NodeManager
from distributed_consensus.crypto import sign, verify
from distributed_consensus.crypto.util import read_all_str
from distributed_consensus.queue.packet import QueuedPacket
from distributed_consensus.transport.tcp.protocol import TCPProtocolV1


class TestTCPProtocolV1(unittest.TestCase):
    def setUp(self):
        self.manager = NodeManager()
        self.protocol = TCPProtocolV1(
            self.manager,
            Node(
                1,
                '1.1.1.1',
                1111,
                read_all_str('./tests/test_keys/node1.pub'),
                read_all_str('./tests/test_keys/node1.key'),
                self.manager,
            ),
            Node(
                2,
                '2.2.2.2',
                2222,
                read_all_str('./tests/test_keys/node2.pub'),
                '',
                self.manager,
            ),
        )

    def tearDown(self):
        self.protocol = None

    @patch('distributed_consensus.transport.tcp.protocol.datetime')
    def test_handshake_generation(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2020, 4, 1, 18, 0, 0, 0)
        bs = self.protocol.generate_handshake()
        assert mock_datetime.utcnow.called
        assert len(bs) == 525
        assert bs[:13] == bytes.fromhex('01 000000005e846620 00000001')
        assert verify(
            self.protocol.local.public_key, bs[13:], bs[:13], 'SHA256',
        )
        remote_protocol = TCPProtocolV1(
            self.manager,
            Node(
                2,
                '2.2.2.2',
                2222,
                read_all_str('./tests/test_keys/node2.pub'),
                read_all_str('./tests/test_keys/node2.key'),
                self.manager,
            ),
        )
        node1 = remote_protocol.parse_handshake(bs)
        assert node1 is self.manager.get_node(1)

    def test_normal_encode_decode(self):
        pkt = QueuedPacket(
            origin=None,
            received_from=None,
            send_to=None,
            full_packet=None,
            data=b'\x01\x02\x03\x04',
        )
        bs = self.protocol.encode(pkt)
        assert len(bs) == 4 + 4 + 4 + 512
        assert bs[:12] == bytes.fromhex('00000001 00000004 01020304')
        assert verify(
            self.protocol.local.public_key, bs[12:], bs[:12], 'SHA256',
        )
        remote_protocol = TCPProtocolV1(
            self.manager,
            Node(
                2,
                '2.2.2.2',
                2222,
                read_all_str('./tests/test_keys/node2.pub'),
                read_all_str('./tests/test_keys/node2.key'),
                self.manager,
            ),
            Node(
                1,
                '1.1.1.1',
                1111,
                read_all_str('./tests/test_keys/node1.pub'),
                None,
                self.manager,
            ),
        )
        decoded = remote_protocol.decode(bs)
        assert decoded.data == bytes.fromhex('01020304')
        assert not decoded.is_forwarding
        assert decoded.full_packet == bs
        assert decoded.received_from is self.manager.get_node(1)
        assert decoded.send_to is self.manager.get_node(2)
        assert decoded.origin is self.manager.get_node(1)
        assert remote_protocol.num_to_read() == 8

    def test_forwarding_encode_decode(self):
        # 1 origin --> 3 forwarder --> 2 receiver
        origin = self.manager.get_node(1)
        assert isinstance(origin, Node)

        forwarder = Node(
            3,
            '3.3.3.3',
            3333,
            # key not installed on purpose, forwarder's key shouldn't be used
            None,
            None,
            self.manager,
        )
        data = b'\x01\x02\x03\x04'
        unsigned = bytes.fromhex(f'{origin.id:08x} {len(data):08x}') + data
        pkt = QueuedPacket(
            origin=origin,
            received_from=forwarder,
            send_to=self.manager.get_node(2),
            full_packet=unsigned + sign(origin.private_key, unsigned),
            data=data,
        )
        bs = self.protocol.encode(pkt)
        assert len(bs) == 4 + 4 + 4 + 512
        assert bs == pkt.full_packet
        remote_protocol = TCPProtocolV1(
            self.manager,
            Node(
                2,
                '2.2.2.2',
                2222,
                read_all_str('./tests/test_keys/node2.pub'),
                read_all_str('./tests/test_keys/node2.key'),
                self.manager,
            ),
            forwarder,
        )
        decoded = remote_protocol.decode(bs)
        assert decoded.data == bytes.fromhex('01020304')
        assert decoded.is_forwarding
        assert decoded.full_packet == bs
        assert decoded.received_from is forwarder
        assert decoded.send_to is self.manager.get_node(2)
        assert decoded.origin is self.manager.get_node(1)
        assert remote_protocol.num_to_read() == 8

    def test_num_to_read(self):
        assert self.protocol.num_to_read() == 8
        assert self.protocol.decode(b'') is None
        assert self.protocol.num_to_read() == 8
        assert self.protocol.decode(b'\x00\x00') is None
        assert self.protocol.num_to_read() == 6
        assert self.protocol.decode(b'\x00\x01\x00\x00\x00\x0a') is None
        assert self.protocol.num_to_read() == 522
        assert self.protocol.decode(b'\x00' * 500) is None
        assert self.protocol.num_to_read() == 22

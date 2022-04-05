import unittest
from distributed_consensus.core.bytes_buffer import BytesBuffer


class TestBytesBuffer(unittest.TestCase):
    def test_init_blank(self):
        x = BytesBuffer()
        assert x.buf == []
        assert len(x) == 0
        assert x.read(1) == b''
        assert x.read() == b''

    def test_initial_value(self):
        x = BytesBuffer(b'1234')
        assert x.buf == [
            b'1234',
        ]
        assert len(x) == 4
        assert x.read(1) == b'1'
        assert x.read() == b'234'
        assert x.read() == b''

    def test_peek(self):
        x = BytesBuffer(b'1234')
        assert len(x) == 4
        assert x.peek(1) == b'1'
        assert x.peek(4) == b'1234'
        assert x.peek(100) == b'1234'
        assert x.read() == b'1234'
        assert x.read() == b''
        assert x.read() == b''

    def test_write(self):
        x = BytesBuffer()
        x.write(b'12')
        x.write(b'3')
        x.write(b'456789')
        assert len(x) == 9
        assert x.peek(1) == b'1'
        assert x.peek(4) == b'1234'
        assert x.peek(100) == b'123456789'
        assert x.read(4) == b'1234'
        assert x.read() == b'56789'
        assert x.read() == b''
        assert x.read() == b''

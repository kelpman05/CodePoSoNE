
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory as TempDir

from distributed_consensus.crypto import generate_key, sign, verify
from distributed_consensus.crypto.util import read_all_str


class TestSignVerify(unittest.TestCase):
    def test_sign_verify(self):
        with TempDir('pyut') as d:
            generate_key('test', d)
            pub = read_all_str(Path(d) / 'test.pub')
            pvt = read_all_str(Path(d) / 'test.key')
            data = b'012345678901234567'
            signature = sign(pvt, data)
            assert verify(pub, signature, data)
            assert not verify(pub, signature, b'0987654321')

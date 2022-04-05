import typing


class BytesBuffer:
    buf: typing.List[bytes]

    def __init__(self, initial: bytes = None):
        self.buf = []
        if initial:
            self.buf.append(initial)

    def __len__(self):
        return sum(map(len, self.buf))

    def _read(self, n: int) -> bytes:
        expected = n
        ans = bytearray()
        while n > 0 and self.buf:
            a = self.buf.pop(0)
            if len(a) > n:
                a, rest = a[:n], a[n:]
                self.buf.insert(0, rest)
            ans.extend(a)
            n -= len(a)
        assert len(ans) == expected or (
            len(ans) < expected and len(self.buf) == 0
        )
        return bytes(ans)

    def peek(self, n: int = 1) -> bytes:
        bs = self._read(n)
        self.buf.insert(0, bs)
        return bs

    def read(self, n: int = -1) -> bytes:
        if n < 0 or n is None:
            ans = b''.join(self.buf)
            self.buf.clear()
            return ans
        return self._read(n)

    def write(self, n: bytes):
        if n:
            self.buf.append(n)

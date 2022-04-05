import typing
from pathlib import Path

from OpenSSL import crypto


def generate_key(
    prefix: str,
    path: typing.Union[str, Path],
    type: str = crypto.TYPE_RSA,
    bits: int = 4096,
):
    if not isinstance(path, Path):
        path = Path(path).resolve().expanduser()

    assert (
        path.exists() and path.is_dir()
    ), f'invalid key storage path {path!s}'

    pubfile = path / f'{prefix}.pub'
    keyfile = path / f'{prefix}.key'

    if pubfile.exists():
        raise FileExistsError(f'{pubfile!s}')
    if keyfile.exists():
        raise FileExistsError(f'{keyfile!s}')

    key = crypto.PKey()
    key.generate_key(type, bits)
    with open(keyfile, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    with open(pubfile, 'wb') as f:
        f.write(crypto.dump_publickey(crypto.FILETYPE_PEM, key))


if __name__ == "__main__":
    generate_key('test', '~/Desktop/')

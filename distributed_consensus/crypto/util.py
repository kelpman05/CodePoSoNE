import typing
from pathlib import Path


def read_all_str(file: typing.Union[str, Path]):
    with open(file, 'r') as f:
        return f.read(-1)

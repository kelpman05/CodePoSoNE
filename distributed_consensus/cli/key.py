import click

from OpenSSL.crypto import TYPE_DSA, TYPE_RSA
from ..crypto.keygen import generate_key
from .root import root


@root.group()
def key():
    pass


@key.command()
@click.option(
    '-d',
    '--directory',
    help='output directory',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
@click.option('-b', '--bits', help='bit length of key', type=int, default=4096)
@click.option(
    '-t',
    '--type',
    help='type of key',
    type=click.Choice(['rsa', 'dsa']),
    default='rsa',
)
@click.argument('NAME', nargs=1, required=True)
def generate(directory, bits, type, name):
    key_type = {'rsa': TYPE_RSA, 'dsa': TYPE_DSA}[type]
    try:
        generate_key(name, directory, key_type, bits)
    except FileExistsError as ex:
        click.echo(f'file {ex.args[0]!s} exists!', err=True)

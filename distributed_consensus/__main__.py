from .cli.root import root

if __name__ == "__main__":
    from .cli import key, run  # noqa
    
    root(prog_name='distributed_consensus')

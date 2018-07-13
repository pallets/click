import click

CONTEXT_SETTINGS = dict(
    default_map={
        'broker_addr':'tcp://127.0.0.1:5552',
        'worker':{
            'addr':'tcp://127.0.0.1:5553',
            'algorithm':{
                'max_array_size':10,
            }
        }
    }
)


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

@cli.command()
@click.option('--broker-addr',default='tcp://127.0.0.1:5551')
@click.option('--worker-addr',default='tcp://127.0.0.1:5552',default_path=['worker','addr'])
@click.option('--max-array-size',default=20,default_path='worker.algorithm.max_array_size')
def test_my_algorithm(broker_addr,worker_addr,max_array_size):
    """Just one simple test subcommand using the global configuration"""
    print('Using broker_addr: %s'%broker_addr)
    print('Using worker_addr: %s'%worker_addr)
    print('Using max_array_size: %s'%max_array_size)

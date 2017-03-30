import click
import os
from netifaces import interfaces, ifaddresses, AF_INET

@click.group()
def cli():
    pass

def get_env_vars(ctx, args, incomplete):
    return os.environ.keys()

@cli.command()
@click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
def cmd1(envvar):
    click.echo('Environment variable: %s' % envvar)
    click.echo('Value: %s' % os.environ[envvar])

@cli.command()
def cmd3():
    pass

@click.group()
def group():
    pass

def ip4_addresses():
    ip_list = []
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET]:
            ip_list.append(link['addr'])
    return ip_list

@group.command()
@click.argument("ip", type=click.STRING, autocompletion=ip4_addresses)
def subcmd(ip):
    click.echo('Chosen IP is %s' % color)

cli.add_command(group)

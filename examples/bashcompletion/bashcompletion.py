import click
import os

@click.group()
def cli():
    pass

@cli.command()
@click.argument("name", type=click.STRING, autocompletion=["John", "Simon", "Doe"])
def cmd1(name):
    click.echo('Name: %s' % name)

def get_env_vars(ctx, incomplete, cwords, cword):
    return os.environ.keys()

@cli.command()
@click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
def cmd2(envvar):
    click.echo('Environment variable: %s' % envvar)
    click.echo('Value: %s' % os.environ[envvar])

@cli.command()
def cmd3():
    pass


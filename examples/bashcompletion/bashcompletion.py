import click
import os

@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', '--count', type=click.INT, default=1)
@click.argument("first", type=click.STRING, autocompletion=["John", "Bob", "Fred"])
@click.argument("last", type=click.STRING, autocompletion=["Smith", "Simon", "Doe"])
def cmd1(count, first, last):
    for c in range(count):
        click.echo('Name: %s %s' % (first, last))

def get_env_vars(ctx, args, incomplete):
    return os.environ.keys()

@cli.command()
@click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
def cmd2(envvar):
    click.echo('Environment variable: %s' % envvar)
    click.echo('Value: %s' % os.environ[envvar])

@cli.command()
def cmd3():
    pass

@click.group()
def group():
    pass

@group.command()
@click.argument("color", type=click.STRING, autocompletion=['red', 'green', 'blue'])
def subcmd(color):
    click.echo('Color is: %s' % color)

cli.add_command(group)

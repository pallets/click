import click
import os

@click.group()
def cli():
    pass

def get_env_vars(ctx, args, incomplete):
    return [key + ' ' for key in os.environ.keys()]

@cli.command()
@click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
def cmd1(envvar):
    click.echo('Environment variable: %s' % envvar)
    click.echo('Value: %s' % os.environ[envvar])

@click.group()
def group():
    pass

def list_users(ctx, args, incomplete):
    # Here you can generate completions dynamically
    users = ['bob ', 'alice ']
    return users

@group.command()
@click.argument("user", type=click.STRING, autocompletion=list_users)
def subcmd(user):
    click.echo('Chosen user is %s' % user)

cli.add_command(group)

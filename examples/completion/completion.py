import os

import click
from click.shell_completion import CompletionItem


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dir", type=click.Path(file_okay=False))
def ls(dir):
    click.echo("\n".join(os.listdir(dir)))


def get_env_vars(ctx, param, args, incomplete):
    # Returning a list of values is a shortcut to returning a list of
    # CompletionItem(value).
    return [k for k in os.environ if incomplete in k]


@cli.command(help="A command to print environment variables")
@click.argument("envvar", shell_complete=get_env_vars)
def show_env(envvar):
    click.echo(f"Environment variable: {envvar}")
    click.echo(f"Value: {os.environ[envvar]}")


@cli.group(help="A group that holds a subcommand")
def group():
    pass


def list_users(ctx, args, incomplete):
    # You can generate completions with help strings by returning a list
    # of CompletionItem. You can match on whatever you want, including
    # the help.
    items = [("bob", "butcher"), ("alice", "baker"), ("jerry", "candlestick maker")]

    for value, help in items:
        if incomplete in value or incomplete in help:
            yield CompletionItem(value, help=help)


@group.command(help="Choose a user")
@click.argument("user", type=click.STRING, autocompletion=list_users)
def select_user(user):
    click.echo(f"Chosen user is {user}")


cli.add_command(group)

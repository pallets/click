import os

import click


@click.group()
def cli():
    pass


def get_env_vars(ctx, args, incomplete):
    # Completions returned as strings do not have a description displayed.
    for key in os.environ.keys():
        if incomplete in key:
            yield key


@cli.command(help="A command to print environment variables")
@click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
def cmd1(envvar):
    click.echo("Environment variable: {}".format(envvar))
    click.echo("Value: {}".format(os.environ[envvar]))


@click.group(help="A group that holds a subcommand")
def group():
    pass


def list_users(ctx, args, incomplete):
    # You can generate completions with descriptions by returning
    # tuples in the form (completion, description).
    users = [("bob", "butcher"), ("alice", "baker"), ("jerry", "candlestick maker")]
    # Ths will allow completion matches based on matches within the
    # description string too!
    return [user for user in users if incomplete in user[0] or incomplete in user[1]]


@group.command(help="Choose a user")
@click.argument("user", type=click.STRING, autocompletion=list_users)
def subcmd(user):
    click.echo("Chosen user is {}".format(user))


cli.add_command(group)

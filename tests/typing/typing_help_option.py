from typing_extensions import assert_type

import click


@click.command()
@click.help_option("-h", "--help")
def hello() -> None:
    """Simple program that greets NAME for a total of COUNT times."""
    click.echo("Hello!")


assert_type(hello, click.Command)

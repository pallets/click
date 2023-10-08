"""
From https://click.palletsprojects.com/en/8.1.x/options/#callbacks-and-eager-options.
"""
from typing_extensions import assert_type

import click


@click.command()
@click.version_option("0.1")
def hello() -> None:
    click.echo("Hello World!")


assert_type(hello, click.Command)

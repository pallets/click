"""From https://click.palletsprojects.com/en/stable/quickstart/#adding-parameters"""

from typing_extensions import assert_type

import click


@click.command()
@click.option("--count", default=1, help="number of greetings")
@click.argument("name")
def hello(count: int, name: str) -> None:
    for _ in range(count):
        click.echo(f"Hello {name}!")


assert_type(hello, click.Command)

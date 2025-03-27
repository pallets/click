"""From https://click.palletsprojects.com/en/stable/options/#yes-parameters"""

from typing_extensions import assert_type

import click


@click.command()
@click.confirmation_option(prompt="Are you sure you want to drop the db?")
def dropdb() -> None:
    click.echo("Dropped all tables!")


assert_type(dropdb, click.Command)

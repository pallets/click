from typing_extensions import assert_type

import click


@click.group(context_settings={})
def hello() -> None:
    pass


assert_type(hello, click.Group)

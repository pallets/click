import pathlib

from typing_extensions import assert_type

import click

# Default path_type is str.
str_type = click.Path(file_okay=False)
assert_type(str_type, click.Path[str])
assert_type(str_type.convert("tmp", None, None), str)
assert_type(str_type("tmp"), str)
assert_type(click.prompt("Enter a name", type=str_type), str)

# path_type selects the converted value type for convert and prompt.
path_type = click.Path(file_okay=False, path_type=pathlib.Path)
assert_type(path_type, click.Path[pathlib.Path])
assert_type(path_type.convert("tmp", None, None), pathlib.Path)
assert_type(path_type("tmp"), pathlib.Path)
assert_type(click.prompt("Enter a name", type=path_type), pathlib.Path)

bytes_type = click.Path(path_type=bytes)
assert_type(bytes_type.convert("tmp", None, None), bytes)
assert_type(click.prompt("Enter a name", type=bytes_type), bytes)

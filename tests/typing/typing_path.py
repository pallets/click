import os
import pathlib

from typing_extensions import assert_type

import click

# Without ``path_type``, the default path value type is returned.
assert_type(click.Path()("foo"), str | bytes | os.PathLike[str])
assert_type(click.Path()(None), None)

# The return type is narrowed by the ``path_type`` argument.
assert_type(click.Path(path_type=str)("foo"), str)
assert_type(click.Path(path_type=bytes)("foo"), bytes)
assert_type(click.Path(path_type=pathlib.Path)("foo"), pathlib.Path)

my_path = click.Path(file_okay=False, path_type=pathlib.Path)
assert_type(my_path, click.Path[pathlib.Path])
assert_type(click.prompt("Enter a name", type=my_path), pathlib.Path)

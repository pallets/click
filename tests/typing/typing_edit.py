from pathlib import Path

from typing_extensions import assert_type

import click

# ``filename`` accepts a path or an iterable of paths.
assert_type(click.edit(filename="f.txt"), None)
assert_type(click.edit(filename=Path("f.txt")), None)
assert_type(click.edit(filename=["f.txt", Path("g.txt")]), None)

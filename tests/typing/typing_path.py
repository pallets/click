import os
import pathlib

from typing_extensions import assert_type

import click

# Without ``path_type``, ``convert`` returns the value it was given.
assert_type(click.Path().convert("a/b.txt", None, None), str | bytes | os.PathLike[str])
assert_type(click.prompt("File", type=click.Path()), str | bytes | os.PathLike[str])

# ``path_type`` narrows the converted value's type for ``convert`` and ``prompt``.
assert_type(click.Path(path_type=str).convert("a/b.txt", None, None), str)
assert_type(click.Path(path_type=bytes).convert("a/b.txt", None, None), bytes)
assert_type(
    click.Path(path_type=pathlib.Path).convert("a/b.txt", None, None), pathlib.Path
)
assert_type(click.prompt("File", type=click.Path(path_type=str)), str)
assert_type(click.prompt("File", type=click.Path(path_type=pathlib.Path)), pathlib.Path)

assert_type(click.Path(path_type=pathlib.Path)("a/b.txt"), pathlib.Path)
assert_type(click.Path(path_type=pathlib.Path)(None), None)

# The class can be parameterized explicitly.
param_type: click.Path[pathlib.Path] = click.Path(exists=True, path_type=pathlib.Path)
assert_type(param_type.convert("a/b.txt", None, None), pathlib.Path)
assert_type(param_type.coerce_path_result("a/b.txt"), pathlib.Path)

general: click.ParamType[str | bytes | os.PathLike[str]] = click.Path()
specific: click.ParamType[pathlib.Path] = click.Path(path_type=pathlib.Path)

assert_type(
    click.Path(path_type=pathlib.Path)(pathlib.PurePosixPath("a/b.txt")), pathlib.Path
)

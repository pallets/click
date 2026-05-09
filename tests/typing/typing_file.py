from __future__ import annotations

import typing as t

from typing_extensions import assert_type

import click


text_file = click.File()
assert_type(text_file, click.File[str])

explicit_text_file = click.File("r")
assert_type(explicit_text_file, click.File[str])

binary_file = click.File("rb")
assert_type(binary_file, click.File[bytes])


with click.open_file("test.txt") as text_stream:
    assert_type(text_stream, t.IO[str])

with click.open_file("test.txt", "r") as explicit_text_stream:
    assert_type(explicit_text_stream, t.IO[str])

with click.open_file("test.bin", "rb") as binary_stream:
    assert_type(binary_stream, t.IO[bytes])

with click.open_file("test.txt", lazy=True) as lazy_text_stream:
    assert_type(lazy_text_stream, t.IO[str])

with click.open_file("test.bin", "wb", atomic=True) as atomic_binary_stream:
    assert_type(atomic_binary_stream, t.IO[bytes])

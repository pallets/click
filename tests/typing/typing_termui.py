from pathlib import Path

import click

path = Path("example.txt")
click.edit(filename=path)
click.edit(filename=[path, "other.txt"])

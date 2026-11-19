import pytest

import click
from click.shell_completion import split_arg_string


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("cli a b c", ["cli", "a", "b", "c"]),
        ("cli 'my file", ["cli", "my file"]),
        ("cli 'my file'", ["cli", "my file"]),
        ("cli my\\", ["cli", "my"]),
        ("cli my\\ file", ["cli", "my file"]),
    ],
)
def test_split_arg_string(value, expect):
    assert split_arg_string(value) == expect


def test_command_default_prefixes():
    ctx = click.Command("cli").make_context("cli", [])
    assert ctx._opt_prefixes == {"-", "--"}


def test_command_collects_prefixes():
    @click.command()
    @click.option("+p", is_flag=True)
    @click.option("!e", is_flag=True)
    def cli(p, e):
        pass

    ctx = cli.make_context("cli", [])
    assert ctx._opt_prefixes == {"-", "--", "+", "!"}

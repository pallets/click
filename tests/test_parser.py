import pytest

import click
from click.parser import _OptionParser
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


def test_parser_default_prefixes():
    parser = _OptionParser()
    assert parser._opt_prefixes == {"-", "--"}


def test_parser_collects_prefixes():
    ctx = click.Context(click.Command("test"))
    parser = _OptionParser(ctx)
    p = click.Option("+p", is_flag=True)
    e = click.Option("!e", is_flag=True)
    parser.add_option(obj=p, opts=p.opts, dest=p.name, action="store_const")
    parser.add_option(obj=e, opts=e.opts, dest=e.name, action="store_const")
    assert parser._opt_prefixes == {"-", "--", "+", "!"}


def test_command_collects_prefixes():
    @click.command()
    @click.option("+p", is_flag=True)
    @click.option("!e", is_flag=True)
    def cli(p, e):
        pass

    ctx = cli.make_context("cli", [])
    assert ctx._opt_prefixes == {"-", "--", "+", "!"}

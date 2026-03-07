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
    click.Option("+p", is_flag=True).add_to_parser(parser, ctx)
    click.Option("!e", is_flag=True).add_to_parser(parser, ctx)
    assert parser._opt_prefixes == {"-", "--", "+", "!"}


def test_multichar_short_option_error_message():
    """A multicharacter short option that isn't found should report the
    full option name in the error, not just the first character. See #2779."""

    @click.command()
    @click.option("-dbg", is_flag=True)
    def cli(dbg):
        pass

    runner = click.testing.CliRunner()

    # Passing the registered option should work.
    result = runner.invoke(cli, ["-dbg"])
    assert result.exit_code == 0

    # Passing an unrecognized variant should report the full option name,
    # not just the first character of the option.
    result = runner.invoke(cli, ["-dbgwrong"])
    assert result.exit_code != 0
    assert "No such option: -dbgwrong" in result.output
    # The error should NOT be truncated to just the first character "-d".
    assert result.output.rstrip().endswith("No such option: -dbgwrong")

"""Tests for merging defaults with user-provided values for
``multiple=True`` options.

See https://github.com/pallets/click/issues/117
"""

import click
from click.testing import CliRunner


def test_multiple_default_used_when_no_cli_values(runner):
    """Default is used when no values are provided on the CLI.

    This is the existing behavior and should not change.
    """

    @click.command()
    @click.option("--name", multiple=True, default=("alice", "bob"))
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output.strip() == "alice, bob"


def test_multiple_default_merged_with_cli_values(runner):
    """Default values are prepended to user-provided values.

    When ``multiple=True`` and a ``default`` tuple is set, the default
    values should be merged with (prepended before) any user-provided
    values from the command line, rather than being discarded entirely.
    """

    @click.command()
    @click.option("--name", multiple=True, default=("alice", "bob"))
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "carol"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice, bob, carol"


def test_multiple_default_merged_with_multiple_cli_values(runner):
    """Multiple user-provided values are appended after defaults."""

    @click.command()
    @click.option("--name", multiple=True, default=("alice",))
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "bob", "--name", "carol"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice, bob, carol"


def test_multiple_no_default(runner):
    """Without a default, only user-provided values are used."""

    @click.command()
    @click.option("--name", multiple=True)
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "alice", "--name", "bob"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice, bob"


def test_multiple_empty_default(runner):
    """An empty default tuple is a no-op (no values to prepend)."""

    @click.command()
    @click.option("--name", multiple=True, default=())
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "alice"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice"


def test_multiple_default_with_type_coercion(runner):
    """Default values and user values are both type-coerced."""

    @click.command()
    @click.option(
        "--val", multiple=True, default=(1, 2), type=click.INT
    )
    def cli(val):
        for v in val:
            assert isinstance(v, int)
            click.echo(v)

    result = runner.invoke(cli, ["--val", "3"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["1", "2", "3"]


def test_multiple_default_with_choice(runner):
    """Defaults and user values are both validated against choices."""

    @click.command()
    @click.option(
        "--color",
        multiple=True,
        default=("red",),
        type=click.Choice(["red", "green", "blue"]),
    )
    def cli(color):
        click.echo(", ".join(color))

    result = runner.invoke(cli, ["--color", "blue"])
    assert result.exit_code == 0
    assert result.output.strip() == "red, blue"


def test_multiple_default_none(runner):
    """``default=None`` means no default to merge."""

    @click.command()
    @click.option("--name", multiple=True, default=None)
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "alice"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice"


def test_multiple_default_list(runner):
    ""``default`` given as a list is also merged."""

    @click.command()
    @click.option("--name", multiple=True, default=["alice", "bob"])
    def cli(name):
        click.echo(", ".join(name))

    result = runner.invoke(cli, ["--name", "carol"])
    assert result.exit_code == 0
    assert result.output.strip() == "alice, bob, carol"

import pytest

import click


def test_command_no_parens(runner):
    @click.command
    def cli():
        click.echo("hello")

    result = runner.invoke(cli)
    assert result.exception is None
    assert result.output == "hello\n"


def test_custom_command_no_parens(runner):
    class CustomCommand(click.Command):
        pass

    class CustomGroup(click.Group):
        command_class = CustomCommand

    @click.group(cls=CustomGroup)
    def grp():
        pass

    @grp.command
    def cli():
        click.echo("hello custom command class")

    result = runner.invoke(cli)
    assert result.exception is None
    assert result.output == "hello custom command class\n"


def test_group_no_parens(runner):
    @click.group
    def grp():
        click.echo("grp1")

    @grp.command
    def cmd1():
        click.echo("cmd1")

    @grp.group
    def grp2():
        click.echo("grp2")

    @grp2.command
    def cmd2():
        click.echo("cmd2")

    result = runner.invoke(grp, ["cmd1"])
    assert result.exception is None
    assert result.output == "grp1\ncmd1\n"

    result = runner.invoke(grp, ["grp2", "cmd2"])
    assert result.exception is None
    assert result.output == "grp1\ngrp2\ncmd2\n"


def test_params_argument(runner):
    opt = click.Argument(["a"])

    @click.command(params=[opt])
    @click.argument("b")
    def cli(a, b):
        click.echo(f"{a} {b}")

    assert cli.params[0].name == "a"
    assert cli.params[1].name == "b"
    result = runner.invoke(cli, ["1", "2"])
    assert result.output == "1 2\n"


@pytest.mark.parametrize(
    "name",
    [
        "init_data",
        "init_data_command",
        "init_data_cmd",
        "init_data_group",
        "init_data_grp",
    ],
)
def test_generate_name(name: str) -> None:
    def f():
        pass

    f.__name__ = name
    f = click.command(f)
    assert f.name == "init-data"

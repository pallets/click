import click


def test_command_no_parens(runner):
    @click.command
    def cli():
        click.echo("hello")

    result = runner.invoke(cli)
    assert result.exception is None
    assert result.output == "hello\n"


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

from __future__ import annotations

import asyncio

import pytest

import click
from click.testing import CliRunner


def test_async_command_callback(runner: CliRunner) -> None:
    @click.command()
    async def cli() -> None:
        await asyncio.sleep(0)
        click.echo("done")

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "done\n"


def test_async_command_with_pass_context(runner: CliRunner) -> None:
    @click.command()
    @click.pass_context
    async def cli(ctx: click.Context) -> None:
        assert ctx.info_name == "cli"
        click.echo("ok")

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "ok\n"


def test_async_subcommand(runner: CliRunner) -> None:
    @click.group()
    def grp() -> None:
        pass

    @grp.command()
    async def sub() -> None:
        click.echo("sub")

    result = runner.invoke(grp, ["sub"])
    assert result.exit_code == 0
    assert result.output == "sub\n"


def test_async_command_return_value(runner: CliRunner) -> None:
    @click.command()
    async def cli() -> int:
        await asyncio.sleep(0)
        return 42

    result = runner.invoke(cli, [], standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == 42


def test_context_invoke_async_callback(runner: CliRunner) -> None:
    @click.command()
    @click.pass_context
    def cli(ctx: click.Context) -> int:
        async def helper() -> int:
            return 99

        rv = ctx.invoke(helper)
        assert isinstance(rv, int)
        return rv

    result = runner.invoke(cli, [], standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == 99


def test_async_group_callback(runner: CliRunner) -> None:
    @click.group()
    @click.pass_context
    async def grp(ctx: click.Context) -> None:
        click.echo("grp")

    @grp.command()
    def sub() -> None:
        click.echo("sub")

    result = runner.invoke(grp, ["sub"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["grp", "sub"]


def test_async_command_rejects_when_loop_already_running(
    runner: CliRunner,
) -> None:
    @click.command()
    async def cli() -> None:
        pass

    async def invoke_inside_loop() -> None:
        runner.invoke(cli, catch_exceptions=False)

    with pytest.raises(RuntimeError, match="asyncio event loop"):
        asyncio.run(invoke_inside_loop())

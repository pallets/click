import pytest

import click


def test_command_pre_hook_basic(runner):
    events = []

    @click.command()
    @click.option("--name", default="World")
    def cli(name):
        events.append(f"command: {name}")
        click.echo(f"Hello, {name}!")

    @cli.pre_hook()
    def log_before(ctx):
        events.append(f"pre_hook: {ctx.info_name}")

    result = runner.invoke(cli, ["--name", "Click"])
    assert result.exit_code == 0
    assert "Hello, Click!" in result.output
    assert events == ["pre_hook: cli", "command: Click"]


def test_command_post_hook_basic(runner):
    events = []

    @click.command()
    @click.option("--name", default="World")
    def cli(name):
        events.append(f"command: {name}")
        return f"Hello, {name}!"

    @cli.post_hook()
    def log_after(ctx, rv):
        events.append(f"post_hook: {ctx.info_name}, result={rv}")
        return rv.upper()

    result = runner.invoke(cli, ["--name", "Click"], standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == "HELLO, CLICK!"
    assert events == [
        "command: Click",
        "post_hook: cli, result=Hello, Click!",
    ]


def test_command_multiple_hooks(runner):
    events = []

    @click.command()
    def cli():
        events.append("command")
        return "original"

    @cli.pre_hook()
    def pre1(ctx):
        events.append("pre1")

    @cli.pre_hook()
    def pre2(ctx):
        events.append("pre2")

    @cli.post_hook()
    def post1(ctx, rv):
        events.append(f"post1: {rv}")
        return "modified1"

    @cli.post_hook()
    def post2(ctx, rv):
        events.append(f"post2: {rv}")
        return "modified2"

    result = runner.invoke(cli, standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == "modified2"
    assert events == ["pre1", "pre2", "command", "post1: original", "post2: modified1"]


def test_group_pre_subcommand_hook_basic(runner):
    events = []

    @click.group()
    def cli():
        events.append("group_callback")

    @cli.command()
    @click.option("--name", default="World")
    def hello(name):
        events.append(f"hello: {name}")
        click.echo(f"Hello, {name}!")

    @cli.pre_subcommand_hook()
    def log_before_subcommand(ctx, cmd_name, cmd):
        events.append(f"pre_subcommand: {cmd_name}")

    result = runner.invoke(cli, ["hello", "--name", "Click"])
    assert result.exit_code == 0
    assert "Hello, Click!" in result.output
    assert events == [
        "group_callback",
        "pre_subcommand: hello",
        "hello: Click",
    ]


def test_group_post_subcommand_hook_basic(runner):
    events = []

    @click.group()
    def cli():
        events.append("group_callback")

    @cli.command()
    @click.option("--name", default="World")
    def hello(name):
        events.append(f"hello: {name}")
        return f"Hello, {name}!"

    @cli.post_subcommand_hook()
    def log_after_subcommand(ctx, cmd_name, cmd, rv):
        events.append(f"post_subcommand: {cmd_name}, result={rv}")
        return rv.upper()

    result = runner.invoke(cli, ["hello", "--name", "Click"], standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == "HELLO, CLICK!"
    assert events == [
        "group_callback",
        "hello: Click",
        "post_subcommand: hello, result=Hello, Click!",
    ]


def test_group_subcommand_hooks_with_chain(runner):
    events = []

    @click.group(chain=True)
    def cli():
        events.append("group_callback")

    @cli.command()
    def first():
        events.append("first")
        return "first_result"

    @cli.command()
    def second():
        events.append("second")
        return "second_result"

    @cli.pre_subcommand_hook()
    def pre(ctx, cmd_name, cmd):
        events.append(f"pre: {cmd_name}")

    @cli.post_subcommand_hook()
    def post(ctx, cmd_name, cmd, rv):
        events.append(f"post: {cmd_name}")
        return f"{rv}_modified"

    result = runner.invoke(cli, ["first", "second"], standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == ["first_result_modified", "second_result_modified"]
    assert events == [
        "group_callback",
        "pre: first",
        "first",
        "post: first",
        "pre: second",
        "second",
        "post: second",
    ]


def test_group_own_hooks_with_subcommand(runner):
    events = []

    @click.group()
    def cli():
        events.append("group_callback")

    @cli.command()
    def sub():
        events.append("sub")

    @cli.pre_hook()
    def group_pre(ctx):
        events.append("group_pre")

    @cli.post_hook()
    def group_post(ctx, rv):
        events.append("group_post")
        return rv

    @cli.pre_subcommand_hook()
    def sub_pre(ctx, cmd_name, cmd):
        events.append(f"sub_pre: {cmd_name}")

    @cli.post_subcommand_hook()
    def sub_post(ctx, cmd_name, cmd, rv):
        events.append(f"sub_post: {cmd_name}")
        return rv

    result = runner.invoke(cli, ["sub"])
    assert result.exit_code == 0
    assert events == [
        "group_pre",
        "group_callback",
        "sub_pre: sub",
        "sub",
        "sub_post: sub",
        "group_post",
    ]


def test_group_invoke_without_command_hooks(runner):
    events = []

    @click.group(invoke_without_command=True)
    def cli():
        events.append("group_callback")
        return "group_result"

    @cli.pre_hook()
    def pre(ctx):
        events.append("pre")

    @cli.post_hook()
    def post(ctx, rv):
        events.append(f"post: {rv}")
        return "modified"

    result = runner.invoke(cli, standalone_mode=False)
    assert result.exit_code == 0
    assert result.return_value == "modified"
    assert events == ["pre", "group_callback", "post: group_result"]


def test_hooks_for_performance_monitoring(runner):
    import time

    timings = []

    @click.group()
    def cli():
        pass

    @cli.command(name="slowcmd")
    def slow_cmd():
        time.sleep(0.01)
        return "done"

    @cli.pre_subcommand_hook()
    def start_timer(ctx, cmd_name, cmd):
        timings.append(("start", cmd_name, time.time()))

    @cli.post_subcommand_hook()
    def end_timer(ctx, cmd_name, cmd, rv):
        timings.append(("end", cmd_name, time.time()))
        return rv

    result = runner.invoke(cli, ["slowcmd"])
    assert result.exit_code == 0
    assert len(timings) == 2
    assert timings[0][0] == "start"
    assert timings[1][0] == "end"
    assert timings[0][1] == "slowcmd"
    assert timings[1][1] == "slowcmd"
    assert timings[1][2] - timings[0][2] >= 0.01


def test_hooks_for_logging(runner):
    log_entries = []

    @click.group()
    @click.option("--verbose", is_flag=True)
    def cli(verbose):
        pass

    @cli.command()
    @click.argument("message")
    def say(message):
        return message

    @cli.pre_subcommand_hook()
    def log_entry(ctx, cmd_name, cmd):
        log_entries.append(
            {
                "command": cmd_name,
                "params": ctx.params,
            }
        )

    result = runner.invoke(cli, ["--verbose", "say", "Hello"])
    assert result.exit_code == 0
    assert len(log_entries) == 1
    assert log_entries[0]["command"] == "say"
    assert log_entries[0]["params"]["verbose"] is True


def test_subcommand_hooks_not_called_without_subcommand(runner):
    events = []

    @click.group(invoke_without_command=True)
    def cli():
        events.append("group")

    @cli.pre_subcommand_hook()
    def pre(ctx, cmd_name, cmd):
        events.append("pre_subcommand")

    @cli.post_subcommand_hook()
    def post(ctx, cmd_name, cmd, rv):
        events.append("post_subcommand")
        return rv

    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert events == ["group"]
    assert "pre_subcommand" not in events
    assert "post_subcommand" not in events


def test_nested_group_hooks(runner):
    events = []

    @click.group()
    def cli():
        events.append("root_group")

    @cli.group(name="subgroup")
    def subgroup():
        events.append("sub_group")

    @subgroup.command(name="cmd")
    def cmd():
        events.append("cmd")

    @cli.pre_subcommand_hook()
    def root_pre(ctx, cmd_name, cmd):
        events.append(f"root_pre: {cmd_name}")

    @subgroup.pre_subcommand_hook()
    def sub_pre(ctx, cmd_name, cmd):
        events.append(f"sub_pre: {cmd_name}")

    result = runner.invoke(cli, ["subgroup", "cmd"])
    assert result.exit_code == 0
    assert events == [
        "root_group",
        "root_pre: subgroup",
        "sub_group",
        "sub_pre: cmd",
        "cmd",
    ]

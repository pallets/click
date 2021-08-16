import re

import click


def test_other_command_invoke(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd, arg=42)

    @click.command()
    @click.argument("arg", type=click.INT)
    def other_cmd(arg):
        click.echo(arg)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "42\n"


def test_other_command_forward(runner):
    cli = click.Group()

    @cli.command()
    @click.option("--count", default=1)
    def test(count):
        click.echo(f"Count: {count:d}")

    @cli.command()
    @click.option("--count", default=1)
    @click.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

    result = runner.invoke(cli, ["dist"])
    assert not result.exception
    assert result.output == "Count: 1\nCount: 42\n"


def test_forwarded_params_consistency(runner):
    cli = click.Group()

    @cli.command()
    @click.option("-a")
    @click.pass_context
    def first(ctx, **kwargs):
        click.echo(f"{ctx.params}")

    @cli.command()
    @click.option("-a")
    @click.option("-b")
    @click.pass_context
    def second(ctx, **kwargs):
        click.echo(f"{ctx.params}")
        ctx.forward(first)

    result = runner.invoke(cli, ["second", "-a", "foo", "-b", "bar"])
    assert not result.exception
    assert result.output == "{'a': 'foo', 'b': 'bar'}\n{'a': 'foo', 'b': 'bar'}\n"


def test_auto_shorthelp(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def short():
        """This is a short text."""

    @cli.command()
    def special_chars():
        """Login and store the token in ~/.netrc."""

    @cli.command()
    def long():
        """This is a long text that is too long to show as short help
        and will be truncated instead."""

    result = runner.invoke(cli, ["--help"])
    assert (
        re.search(
            r"Commands:\n\s+"
            r"long\s+This is a long text that is too long to show as short help"
            r"\.\.\.\n\s+"
            r"short\s+This is a short text\.\n\s+"
            r"special-chars\s+Login and store the token in ~/.netrc\.\s*",
            result.output,
        )
        is not None
    )


def test_no_args_is_help(runner):
    @click.command(no_args_is_help=True)
    def cli():
        pass

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


def test_default_maps(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name", default="normal")
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": "changed"}})

    assert not result.exception
    assert result.output == "changed\n"


def test_group_with_args(runner):
    @click.group()
    @click.argument("obj")
    def cli(obj):
        click.echo(f"obj={obj}")

    @cli.command()
    def move():
        click.echo("move")

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output

    result = runner.invoke(cli, ["obj1"])
    assert result.exit_code == 2
    assert "Error: Missing command." in result.output

    result = runner.invoke(cli, ["obj1", "--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output

    result = runner.invoke(cli, ["obj1", "move"])
    assert result.exit_code == 0
    assert result.output == "obj=obj1\nmove\n"


def test_base_command(runner):
    import optparse

    @click.group()
    def cli():
        pass

    class OptParseCommand(click.BaseCommand):
        def __init__(self, name, parser, callback):
            super().__init__(name)
            self.parser = parser
            self.callback = callback

        def parse_args(self, ctx, args):
            try:
                opts, args = parser.parse_args(args)
            except Exception as e:
                ctx.fail(str(e))
            ctx.args = args
            ctx.params = vars(opts)

        def get_usage(self, ctx):
            return self.parser.get_usage()

        def get_help(self, ctx):
            return self.parser.format_help()

        def invoke(self, ctx):
            ctx.invoke(self.callback, ctx.args, **ctx.params)

    parser = optparse.OptionParser(usage="Usage: foo test [OPTIONS]")
    parser.add_option(
        "-f", "--file", dest="filename", help="write report to FILE", metavar="FILE"
    )
    parser.add_option(
        "-q",
        "--quiet",
        action="store_false",
        dest="verbose",
        default=True,
        help="don't print status messages to stdout",
    )

    def test_callback(args, filename, verbose):
        click.echo(" ".join(args))
        click.echo(filename)
        click.echo(verbose)

    cli.add_command(OptParseCommand("test", parser, test_callback))

    result = runner.invoke(
        cli, ["test", "-f", "test.txt", "-q", "whatever.txt", "whateverelse.txt"]
    )
    assert not result.exception
    assert result.output.splitlines() == [
        "whatever.txt whateverelse.txt",
        "test.txt",
        "False",
    ]

    result = runner.invoke(cli, ["test", "--help"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo test [OPTIONS]",
        "",
        "Options:",
        "  -h, --help            show this help message and exit",
        "  -f FILE, --file=FILE  write report to FILE",
        "  -q, --quiet           don't print status messages to stdout",
    ]


def test_object_propagation(runner):
    for chain in False, True:

        @click.group(chain=chain)
        @click.option("--debug/--no-debug", default=False)
        @click.pass_context
        def cli(ctx, debug):
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj["DEBUG"] = debug

        @cli.command()
        @click.pass_context
        def sync(ctx):
            click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")

        result = runner.invoke(cli, ["sync"])
        assert result.exception is None
        assert result.output == "Debug is off\n"


def test_other_command_invoke_with_defaults(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd)

    @click.command()
    @click.option("--foo", type=click.INT, default=42)
    @click.pass_context
    def other_cmd(ctx, foo):
        assert ctx.info_name == "other-cmd"
        click.echo(foo)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "42\n"


def test_invoked_subcommand(runner):
    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo("no subcommand, use default")
            ctx.invoke(sync)
        else:
            click.echo("invoke subcommand")

    @cli.command()
    def sync():
        click.echo("in subcommand")

    result = runner.invoke(cli, ["sync"])
    assert not result.exception
    assert result.output == "invoke subcommand\nin subcommand\n"

    result = runner.invoke(cli)
    assert not result.exception
    assert result.output == "no subcommand, use default\nin subcommand\n"


def test_aliased_command_canonical_name(runner):
    class AliasedGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            return push

        def resolve_command(self, ctx, args):
            _, command, args = super().resolve_command(ctx, args)
            return command.name, command, args

    cli = AliasedGroup()

    @cli.command()
    def push():
        click.echo("push command")

    result = runner.invoke(cli, ["pu", "--help"])
    assert not result.exception
    assert result.output.startswith("Usage: root push [OPTIONS]")


def test_group_add_command_name(runner):
    cli = click.Group("cli")
    cmd = click.Command("a", params=[click.Option(["-x"], required=True)])
    cli.add_command(cmd, "b")
    # Check that the command is accessed through the registered name,
    # not the original name.
    result = runner.invoke(cli, ["b"], default_map={"b": {"x": 3}})
    assert result.exit_code == 0


def test_unprocessed_options(runner):
    @click.command(context_settings=dict(ignore_unknown_options=True))
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    @click.option("--verbose", "-v", count=True)
    def cli(verbose, args):
        click.echo(f"Verbosity: {verbose}")
        click.echo(f"Args: {'|'.join(args)}")

    result = runner.invoke(cli, ["-foo", "-vvvvx", "--muhaha", "x", "y", "-x"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Verbosity: 4",
        "Args: -foo|-x|--muhaha|x|y|-x",
    ]


def test_deprecated_in_help_messages(runner):
    @click.command(deprecated=True)
    def cmd_with_help():
        """CLI HELP"""
        pass

    result = runner.invoke(cmd_with_help, ["--help"])
    assert "(Deprecated)" in result.output

    @click.command(deprecated=True)
    def cmd_without_help():
        pass

    result = runner.invoke(cmd_without_help, ["--help"])
    assert "(Deprecated)" in result.output


def test_deprecated_in_invocation(runner):
    @click.command(deprecated=True)
    def deprecated_cmd():
        pass

    result = runner.invoke(deprecated_cmd)
    assert "DeprecationWarning:" in result.output


def test_disable_double_dash_on_group(runner):
    @click.group(disable_double_dash=True)
    def cli():
        pass

    @cli.command()
    def sdist():
        click.echo("sdist called")

    result = runner.invoke(cli, ["--", "sdist"])
    assert result.exit_code == 2
    assert (
        "Error: can't use '--' between a command and a subcommand and between"
        " subcommands" in result.output
    )


def test_disable_double_dash_on_command_collection(runner):
    @click.group()
    def cli1():
        pass

    @cli1.command()
    def cmd1():
        """Command on cli1"""

    @click.group()
    def cli2():
        pass

    @cli2.command()
    def cmd2():
        """Command on cli2"""

    cli = click.CommandCollection(sources=[cli1, cli2], disable_double_dash=True)
    result = runner.invoke(cli, args=["--", "cmd1"])
    assert result.exit_code == 2
    assert (
        "Error: can't use '--' between a command and a subcommand and between"
        " subcommands" in result.output
    )

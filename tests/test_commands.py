import re

import pytest

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


def test_command_no_args_is_help(runner):
    result = runner.invoke(click.Command("test", no_args_is_help=True))
    assert result.exit_code == 2
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


@pytest.mark.parametrize(
    ("args", "exit_code", "expect"),
    [
        (["obj1"], 2, "Error: Missing command."),
        (["obj1", "--help"], 0, "Show this message and exit."),
        (["obj1", "move"], 0, "obj=obj1\nmove\n"),
        ([], 2, "Show this message and exit."),
    ],
)
def test_group_with_args(runner, args, exit_code, expect):
    @click.group()
    @click.argument("obj")
    def cli(obj):
        click.echo(f"obj={obj}")

    @cli.command()
    def move():
        click.echo("move")

    result = runner.invoke(cli, args)
    assert result.exit_code == exit_code
    assert expect in result.output


def test_custom_parser(runner):
    import optparse

    @click.group()
    def cli():
        pass

    class OptParseCommand(click.Command):
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

    result = runner.invoke(cli, ["test", "-f", "f.txt", "-q", "q1.txt", "q2.txt"])
    assert result.exception is None
    assert result.output.splitlines() == ["q1.txt q2.txt", "f.txt", "False"]

    result = runner.invoke(cli, ["test", "--help"])
    assert result.exception is None
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
    @click.option("-a", type=click.INT, default=42)
    @click.option("-b", type=click.INT, default="15")
    @click.option("-c", multiple=True)
    @click.option(
        "-d",
    )
    @click.pass_context
    def other_cmd(ctx, a, b, c, d):
        return ctx.info_name, a, b, c, d

    result = runner.invoke(cli, standalone_mode=False)
    # invoke should type cast default values, str becomes int, empty
    # multiple should be empty tuple instead of None
    assert result.return_value == ("other", 42, 15, (), None)


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


@pytest.mark.parametrize(
    ("invocation_order", "declaration_order", "expected_order"),
    [
        # Non-eager options.
        ([], ["-a"], ["-a"]),
        (["-a"], ["-a"], ["-a"]),
        ([], ["-a", "-c"], ["-a", "-c"]),
        (["-a"], ["-a", "-c"], ["-a", "-c"]),
        (["-c"], ["-a", "-c"], ["-c", "-a"]),
        ([], ["-c", "-a"], ["-c", "-a"]),
        (["-a"], ["-c", "-a"], ["-a", "-c"]),
        (["-c"], ["-c", "-a"], ["-c", "-a"]),
        (["-a", "-c"], ["-a", "-c"], ["-a", "-c"]),
        (["-c", "-a"], ["-a", "-c"], ["-c", "-a"]),
        # Eager options.
        ([], ["-b"], ["-b"]),
        (["-b"], ["-b"], ["-b"]),
        ([], ["-b", "-d"], ["-b", "-d"]),
        (["-b"], ["-b", "-d"], ["-b", "-d"]),
        (["-d"], ["-b", "-d"], ["-d", "-b"]),
        ([], ["-d", "-b"], ["-d", "-b"]),
        (["-b"], ["-d", "-b"], ["-b", "-d"]),
        (["-d"], ["-d", "-b"], ["-d", "-b"]),
        (["-b", "-d"], ["-b", "-d"], ["-b", "-d"]),
        (["-d", "-b"], ["-b", "-d"], ["-d", "-b"]),
        # Mixed options.
        ([], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-a"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-c"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-c", "-a"]),
        (["-d"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-a", "-c"]),
        (["-a", "-b"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b", "-a"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-d", "-c"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-c", "-a"]),
        (["-c", "-d"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-c", "-a"]),
        (["-a", "-b", "-c", "-d"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b", "-d", "-a", "-c"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        ([], ["-b", "-d", "-e", "-a", "-c"], ["-b", "-d", "-e", "-a", "-c"]),
        (["-a", "-d"], ["-b", "-d", "-e", "-a", "-c"], ["-d", "-b", "-e", "-a", "-c"]),
        (["-c", "-d"], ["-b", "-d", "-e", "-a", "-c"], ["-d", "-b", "-e", "-c", "-a"]),
    ],
)
def test_iter_params_for_processing(
    invocation_order, declaration_order, expected_order
):
    parameters = {
        "-a": click.Option(["-a"]),
        "-b": click.Option(["-b"], is_eager=True),
        "-c": click.Option(["-c"]),
        "-d": click.Option(["-d"], is_eager=True),
        "-e": click.Option(["-e"], is_eager=True),
    }

    invocation_params = [parameters[opt_id] for opt_id in invocation_order]
    declaration_params = [parameters[opt_id] for opt_id in declaration_order]
    expected_params = [parameters[opt_id] for opt_id in expected_order]

    assert (
        click.core.iter_params_for_processing(invocation_params, declaration_params)
        == expected_params
    )


def test_help_param_priority(runner):
    """Cover the edge-case in which the eagerness of help option was not
    respected, because it was internally generated multiple times.

    See: https://github.com/pallets/click/pull/2811
    """

    def print_and_exit(ctx, param, value):
        if value:
            click.echo(f"Value of {param.name} is: {value}")
            ctx.exit()

    @click.command(context_settings={"help_option_names": ("--my-help",)})
    @click.option("-a", is_flag=True, expose_value=False, callback=print_and_exit)
    @click.option(
        "-b", is_flag=True, expose_value=False, callback=print_and_exit, is_eager=True
    )
    def cli():
        pass

    # --my-help is properly called and stop execution.
    result = runner.invoke(cli, ["--my-help"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" in result.stdout
    assert result.exit_code == 0

    # -a is properly called and stop execution.
    result = runner.invoke(cli, ["-a"])
    assert "Value of a is: True" in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # -a takes precedence over -b and stop execution.
    result = runner.invoke(cli, ["-a", "-b"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # --my-help is eager by default so takes precedence over -a and stop
    # execution, whatever the order.
    for args in [["-a", "--my-help"], ["--my-help", "-a"]]:
        result = runner.invoke(cli, args)
        assert "Value of a is: True" not in result.stdout
        assert "Value of b is: True" not in result.stdout
        assert "--my-help" in result.stdout
        assert result.exit_code == 0

    # Both -b and --my-help are eager so they're called in the order they're
    # invoked by the user.
    result = runner.invoke(cli, ["-b", "--my-help"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # But there was a bug when --my-help is called before -b, because the
    # --my-help option created by click via help_option_names is internally
    # created twice and is not the same object, breaking the priority order
    # produced by iter_params_for_processing.
    result = runner.invoke(cli, ["--my-help", "-b"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" in result.stdout
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


@pytest.mark.parametrize("doc", ["CLI HELP", None])
@pytest.mark.parametrize("deprecated", [True, "USE OTHER COMMAND INSTEAD"])
def test_deprecated_in_help_messages(runner, doc, deprecated):
    @click.command(deprecated=deprecated, help=doc)
    def cli():
        pass

    result = runner.invoke(cli, ["--help"])
    assert "(DEPRECATED" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


@pytest.mark.parametrize("deprecated", [True, "USE OTHER COMMAND INSTEAD"])
def test_deprecated_in_invocation(runner, deprecated):
    @click.command(deprecated=deprecated)
    def deprecated_cmd():
        pass

    result = runner.invoke(deprecated_cmd)
    assert "DeprecationWarning:" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_command_parse_args_collects_option_prefixes():
    @click.command()
    @click.option("+p", is_flag=True)
    @click.option("!e", is_flag=True)
    def test(p, e):
        pass

    ctx = click.Context(test)
    test.parse_args(ctx, [])

    assert ctx._opt_prefixes == {"-", "--", "+", "!"}


def test_group_parse_args_collects_base_option_prefixes():
    @click.group()
    @click.option("~t", is_flag=True)
    def group(t):
        pass

    @group.command()
    @click.option("+p", is_flag=True)
    def command1(p):
        pass

    @group.command()
    @click.option("!e", is_flag=True)
    def command2(e):
        pass

    ctx = click.Context(group)
    group.parse_args(ctx, ["command1", "+p"])

    assert ctx._opt_prefixes == {"-", "--", "~"}


def test_group_invoke_collects_used_option_prefixes(runner):
    opt_prefixes = set()

    @click.group()
    @click.option("~t", is_flag=True)
    def group(t):
        pass

    @group.command()
    @click.option("+p", is_flag=True)
    @click.pass_context
    def command1(ctx, p):
        nonlocal opt_prefixes
        opt_prefixes = ctx._opt_prefixes

    @group.command()
    @click.option("!e", is_flag=True)
    def command2(e):
        pass

    runner.invoke(group, ["command1"])
    assert opt_prefixes == {"-", "--", "~", "+"}


@pytest.mark.parametrize("exc", (EOFError, KeyboardInterrupt))
def test_abort_exceptions_with_disabled_standalone_mode(runner, exc):
    @click.command()
    def cli():
        raise exc("catch me!")

    rv = runner.invoke(cli, standalone_mode=False)
    assert rv.exit_code == 1
    assert isinstance(rv.exception.__cause__, exc)
    assert rv.exception.__cause__.args == ("catch me!",)

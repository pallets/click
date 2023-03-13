import click


def test_command_context_class():
    """A command with a custom ``context_class`` should produce a
    context using that type.
    """

    class CustomContext(click.Context):
        pass

    class CustomCommand(click.Command):
        context_class = CustomContext

    command = CustomCommand("test")
    context = command.make_context("test", [])
    assert isinstance(context, CustomContext)


def test_context_invoke_type(runner):
    """A command invoked from a custom context should have a new
    context with the same type.
    """

    class CustomContext(click.Context):
        pass

    class CustomCommand(click.Command):
        context_class = CustomContext

    @click.command()
    @click.argument("first_id", type=int)
    @click.pass_context
    def second(ctx, first_id):
        assert isinstance(ctx, CustomContext)
        assert id(ctx) != first_id

    @click.command(cls=CustomCommand)
    @click.pass_context
    def first(ctx):
        assert isinstance(ctx, CustomContext)
        ctx.invoke(second, first_id=id(ctx))

    assert not runner.invoke(first).exception


def test_context_formatter_class():
    """A context with a custom ``formatter_class`` should format help
    using that type.
    """

    class CustomFormatter(click.HelpFormatter):
        def write_heading(self, heading):
            heading = click.style(heading, fg="yellow")
            return super().write_heading(heading)

    class CustomContext(click.Context):
        formatter_class = CustomFormatter

    context = CustomContext(
        click.Command("test", params=[click.Option(["--value"])]), color=True
    )
    assert "\x1b[33mOptions\x1b[0m:" in context.get_help()


def test_group_command_class(runner):
    """A group with a custom ``command_class`` should create subcommands
    of that type by default.
    """

    class CustomCommand(click.Command):
        pass

    class CustomGroup(click.Group):
        command_class = CustomCommand

    group = CustomGroup()
    subcommand = group.command()(lambda: None)
    assert type(subcommand) is CustomCommand
    subcommand = group.command(cls=click.Command)(lambda: None)
    assert type(subcommand) is click.Command


def test_group_group_class(runner):
    """A group with a custom ``group_class`` should create subgroups
    of that type by default.
    """

    class CustomSubGroup(click.Group):
        pass

    class CustomGroup(click.Group):
        group_class = CustomSubGroup

    group = CustomGroup()
    subgroup = group.group()(lambda: None)
    assert type(subgroup) is CustomSubGroup
    subgroup = group.command(cls=click.Group)(lambda: None)
    assert type(subgroup) is click.Group


def test_group_group_class_self(runner):
    """A group with ``group_class = type`` should create subgroups of
    the same type as itself.
    """

    class CustomGroup(click.Group):
        group_class = type

    group = CustomGroup()
    subgroup = group.group()(lambda: None)
    assert type(subgroup) is CustomGroup


def test_bound_method(runner):
    """
    A custom MultiCommand with ``method Commands``
    methods should be registered as commands inside the __init__ so they can capture
    the reference to `self`
    """
    class Test(click.MultiCommand):
        def __init__(self, attribute="default"):
            super().__init__()
            self.attribute = attribute
            self.commands = {"echo": click.command(self.echo), "shout": click.command(self.shout)}

        def echo(self):
            click.echo(self.attribute)

        @click.argument("message", type=str)
        @click.option("--capitalize/--no-capitalize", default=False)
        def shout(self, message, capitalize):
            loud_message = message.capitalize() if capitalize else message.upper()
            click.echo(loud_message)

        def get_command(self, ctx, cmd_name):
            return self.commands.get(cmd_name)

        def list_commands(self, ctx):
            return [*self.commands.keys()]

    cli_default = Test()
    result = runner.invoke(cli_default, "echo")
    assert result.output == "default\n"

    cli_test = Test("test")
    result = runner.invoke(cli_test, "echo")
    assert result.output == "test\n"

    result = runner.invoke(cli_test, ["shout", "testthis"])
    assert result.output == "TESTTHIS\n"

    result = runner.invoke(cli_test, ["shout", "--capitalize", "testthis"])
    assert result.output == "Testthis\n"

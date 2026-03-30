import pytest

import click


def test_basic_functionality(runner):
    @click.command()
    def cli():
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.

        \b
        This is
        a paragraph
        without rewrapping.

        \b
        1
         2
          3

        And this is a paragraph
        that will be rewrapped again.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "  This is",
        "  a paragraph",
        "  without rewrapping.",
        "",
        "  1",
        "   2",
        "    3",
        "",
        "  And this is a paragraph that will be rewrapped again.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_wrapping_long_options_strings(runner):
    @click.group()
    def cli():
        """Top level command"""

    @cli.group()
    def a_very_long():
        """Second level"""

    @a_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command."""

    # 54 is chosen as a length where the second line is one character
    # longer than the maximum length.
    result = runner.invoke(cli, ["a-very-long", "command", "--help"], terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-long command [OPTIONS] FIRST SECOND",
        "                               THIRD FOURTH FIFTH",
        "                               SIXTH",
        "",
        "  A command.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_wrapping_long_command_name(runner):
    @click.group()
    def cli():
        """Top level command"""

    @cli.group()
    def a_very_very_very_long():
        """Second level"""

    @a_very_very_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command."""

    result = runner.invoke(
        cli, ["a-very-very-very-long", "command", "--help"], terminal_width=54
    )
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-very-very-long command ",
        "           [OPTIONS] FIRST SECOND THIRD FOURTH FIFTH",
        "           SIXTH",
        "",
        "  A command.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_formatting_empty_help_lines(runner):
    @click.command()
    def cli():
        # fmt: off
        """Top level command

        """
        # fmt: on

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  Top level command",
        "",
        "",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_formatting_usage_error(runner):
    @click.command()
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_error_metavar_missing_arg(runner):
    """
    :author: @r-m-n
    Including attribution to #612
    """

    @click.command()
    @click.argument("arg", metavar="metavar")
    def cmd(arg):
        pass

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'metavar'.",
    ]


def test_formatting_usage_error_metavar_bad_arg(runner):
    @click.command()
    @click.argument("arg", type=click.INT, metavar="metavar")
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["3.14"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Invalid value for 'metavar': '3.14' is not a valid integer.",
    ]


def test_formatting_usage_error_nested(runner):
    @click.group()
    def cmd():
        pass

    @cmd.command()
    @click.argument("bar")
    def foo(bar):
        click.echo(f"foo:{bar}")

    result = runner.invoke(cmd, ["foo"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd foo [OPTIONS] BAR",
        "Try 'cmd foo --help' for help.",
        "",
        "Error: Missing argument 'BAR'.",
    ]


def test_formatting_usage_error_no_help(runner):
    @click.command(add_help_option=False)
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_custom_help(runner):
    @click.command(context_settings=dict(help_option_names=["--man"]))
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --man' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_custom_type_metavar(runner):
    class MyType(click.ParamType):
        def get_metavar(self, param: click.Parameter, ctx: click.Context):
            return "MY_TYPE"

    @click.command("foo")
    @click.help_option()
    @click.argument("param", type=MyType())
    def cmd(param):
        pass

    result = runner.invoke(cmd, "--help")
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS] MY_TYPE",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_truncating_docstring(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.
        \f

        :param click.core.Context ctx: Click context.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_truncating_docstring_no_help(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        """
        \f

        This text should be truncated.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_removing_multiline_marker(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def cmd1():
        """\b
        This is command with a multiline help text
        which should not be rewrapped.
        The output of the short help text should
        not contain the multiline marker.
        """
        pass

    result = runner.invoke(cli, ["--help"])
    assert "\b" not in result.output


def test_global_show_default(runner):
    @click.command(context_settings=dict(show_default=True))
    @click.option("-f", "in_file", default="out.txt", help="Output file name")
    def cli():
        pass

    result = runner.invoke(cli, ["--help"])
    # the default to "--help" is not shown because it is False
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  -f TEXT  Output file name  [default: out.txt]",
        "  --help   Show this message and exit.",
    ]


def test_formatting_with_options_metavar_empty(runner):
    cli = click.Command("cli", options_metavar="", params=[click.Argument(["var"])])
    result = runner.invoke(cli, ["--help"])
    assert "Usage: cli VAR\n" in result.output


def test_help_formatter_write_text():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
    formatter = click.HelpFormatter(width=len("  Lorem ipsum dolor sit amet,"))
    formatter.current_indent = 2
    formatter.write_text(text)
    actual = formatter.getvalue()
    expected = "  Lorem ipsum dolor sit amet,\n  consectetur adipiscing elit\n"
    assert actual == expected


def test_usage_error_missing_parameter(runner):
    """Test error messages for missing required parameters."""

    @click.command()
    @click.argument("arg")
    def cli(arg):
        pass

    result = runner.invoke(cli, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'" in result.output
    assert "Usage:" in result.output
    assert "Try 'cli --help' for help." in result.output


def test_usage_error_missing_multiple_arguments(runner):
    """Test error messages when multiple arguments are missing."""

    @click.command()
    @click.argument("first")
    @click.argument("second")
    def cli(first, second):
        pass

    result = runner.invoke(cli, [])
    assert result.exit_code == 2
    # Should report the first missing argument
    assert "Missing argument 'FIRST'" in result.output
    assert "Usage:" in result.output


@pytest.mark.parametrize(
    ("extra_args", "expected_error"),
    [
        # Extra positional argument
        (["arg1", "extra"], "Got unexpected extra argument (extra)"),
        # Multiple extra arguments - uses plural form
        (["arg1", "extra1", "extra2"], "Got unexpected extra arguments (extra1 extra2)"),
    ],
)
def test_usage_error_extra_arguments(runner, extra_args, expected_error):
    """Test error messages for unexpected extra arguments."""

    @click.command()
    @click.argument("arg")
    def cli(arg):
        pass

    result = runner.invoke(cli, extra_args)
    assert result.exit_code == 2
    assert expected_error in result.output


@pytest.mark.parametrize(
    ("option_type", "input_value", "expected_error"),
    [
        # Invalid integer
        (click.INT, "not-a-number", "is not a valid integer"),
        # Invalid float
        (click.FLOAT, "not-a-float", "is not a valid float"),
        # Invalid boolean
        (click.BOOL, "not-a-bool", "is not a valid boolean"),
        # Invalid UUID
        (click.UUID, "not-a-uuid", "is not a valid UUID"),
    ],
)
def test_usage_error_invalid_type(runner, option_type, input_value, expected_error):
    """Test error messages for invalid type conversions."""

    @click.command()
    @click.option("--value", type=option_type)
    def cli(value):
        pass

    result = runner.invoke(cli, ["--value", input_value])
    assert result.exit_code == 2
    assert expected_error in result.output
    assert "Invalid value for '--value'" in result.output


def test_usage_error_nested_command(runner):
    """Test error messages include correct command path for nested commands."""

    @click.group()
    def cli():
        pass

    @cli.group()
    def sub():
        pass

    @sub.command()
    @click.argument("arg")
    def cmd(arg):
        pass

    result = runner.invoke(cli, ["sub", "cmd"])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'" in result.output
    assert "Usage: cli sub cmd [OPTIONS] ARG" in result.output
    assert "Try 'cli sub cmd --help' for help." in result.output


def test_help_text_with_unicode(runner):
    """Test help text correctly displays unicode characters."""

    @click.command()
    @click.option("--name", help="Your name (e.g., \N{SNOWMAN})")
    def cli(name):
        """A command with unicode: \N{SNOWMAN}."""
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "\u2603" in result.output


def test_help_text_special_chars_in_defaults(runner):
    """Test help text with special characters in default values."""

    @click.command()
    @click.option("--path", default="/path/with spaces", show_default=True)
    @click.option("--regex", default=".*\\.txt", show_default=True)
    def cli(path, regex):
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "/path/with spaces" in result.output
    assert ".*\\.txt" in result.output


def test_error_message_with_suggestions(runner):
    """Test error messages include suggestions for similar options."""

    @click.command()
    @click.option("--verbose", is_flag=True)
    @click.option("--version", is_flag=True)
    def cli(verbose, version):
        pass

    # Typo in option name should suggest similar options
    result = runner.invoke(cli, ["--verbo"])
    assert result.exit_code == 2
    assert "no such option" in result.output.lower()
    # Click shows possible options when there are similar matches
    assert "Possible options" in result.output

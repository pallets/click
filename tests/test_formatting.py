import threading

import pytest

import click
from click._compat import strip_ansi


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


@pytest.mark.parametrize(
    ("help_names", "extra_options", "expected_hint"),
    [
        # No shadowing, longest name is picked.
        (["-h", "--help"], [], "Try 'cli foo --help' for help."),
        # -h shadowed by a subcommand option, --help still available.
        (
            ["-h", "--help"],
            [click.option("--host", "-h")],
            "Try 'cli foo --help' for help.",
        ),
        # --help shadowed, -h still available.
        (
            ["-h", "--help"],
            [click.option("--help-file", "--help")],
            "Try 'cli foo -h' for help.",
        ),
        # Both names shadowed: no hint line at all.
        (
            ["-h", "--help"],
            [click.option("--host", "-h"), click.option("--help-file", "--help")],
            None,
        ),
        # Single custom help name, not shadowed.
        (["--man"], [], "Try 'cli foo --man' for help."),
        # Three help names, one shadowed, longest survivor picked.
        (
            ["-h", "--help", "--info"],
            [click.option("--info-file", "--info")],
            "Try 'cli foo --help' for help.",
        ),
    ],
)
def test_formatting_usage_error_help_hint(
    runner, help_names, extra_options, expected_hint
):
    """The error hint should only show non-shadowed help option names, picking the
    longest for readability.
    """

    @click.group(context_settings={"help_option_names": help_names})
    def cli():
        pass

    @cli.command()
    @click.argument("required_arg")
    def foo(required_arg, **kwargs):
        pass

    for option in extra_options:
        option(foo)

    result = runner.invoke(cli, ["foo"])
    assert result.exit_code == 2
    lines = result.output.splitlines()
    assert lines[0] == "Usage: cli foo [OPTIONS] REQUIRED_ARG"
    assert lines[-1] == "Error: Missing argument 'REQUIRED_ARG'."
    if expected_hint is not None:
        assert expected_hint in lines
    else:
        assert not any(line.startswith("Try ") for line in lines)


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


@pytest.mark.parametrize(
    ("body", "width", "initial_indent"),
    [
        # Styled ``initial_indent`` must be measured by visible width, so the
        # ``Usage:`` prefix shouldn't push ``CITY`` to the second line.
        # Regression for the asymmetry between ``HelpFormatter.write_usage``
        # (which sized the prefix with ``term_len``) and ``wrap_text``
        # (which previously used raw ``len``).
        pytest.param(
            "[OPTIONS] CITY",
            30,
            "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m ",
            id="styled-initial-indent-does-not-break-body",
        ),
        # Styled chunks in the body itself wrap on visible width.
        pytest.param(
            "\x1b[31malpha\x1b[0m \x1b[31mbeta\x1b[0m"
            " \x1b[31mgamma\x1b[0m \x1b[31mdelta\x1b[0m",
            15,
            "",
            id="styled-body-wraps-on-visible-width",
        ),
        # Colon-delimited true-color (ISO 8613-6) escapes are excluded from the
        # width budget too.
        pytest.param(
            "\x1b[38:2:255:0:0malpha\x1b[0m \x1b[38:2:0:255:0mbeta\x1b[0m"
            " \x1b[38:2:0:0:255mgamma\x1b[0m \x1b[38:2:9:9:9mdelta\x1b[0m",
            15,
            "",
            id="colon-truecolor-body-wraps-on-visible-width",
        ),
        # A mouse-reporting sequence embedded mid-line is zero-width too.
        pytest.param(
            "\x1b[<0;1;1malpha beta gamma delta\x1b[<0;1;1m",
            15,
            "",
            id="mouse-sequence-is-zero-width",
        ),
    ],
)
def test_wrap_text_visible_width(body, width, initial_indent):
    """``wrap_text`` of styled input produces the same line layout as
    ``wrap_text`` of the ANSI-stripped input.

    ANSI escape bytes must not count toward the width budget, whether they
    appear in the body or in ``initial_indent``. Wrapping moves or drops
    whitespace only: every escape sequence survives, in order.
    """
    styled = click.formatting.wrap_text(
        body, width=width, initial_indent=initial_indent
    )
    plain = click.formatting.wrap_text(
        strip_ansi(body), width=width, initial_indent=strip_ansi(initial_indent)
    )

    styled_visible = [strip_ansi(line) for line in styled.splitlines()]
    assert styled_visible == plain.splitlines()
    assert "".join(styled.split()) == "".join((initial_indent + body).split())


@pytest.mark.parametrize(
    ("text", "width", "expected"),
    [
        # A line breaks between words, never after a hyphen inside one.
        pytest.param(
            "Add --avoid-motorways to stay on country roads.",
            20,
            ["Add", "--avoid-motorways to", "stay on country", "roads."],
            id="hyphenated-word",
        ),
        # A word wider than the line is not cut: it goes on a line of its own.
        pytest.param(
            "Visit Llanfairpwllgwyngyll in Wales.",
            10,
            ["Visit", "Llanfairpwllgwyngyll", "in Wales."],
            id="long-word",
        ),
        # A styled word wider than the line stays whole with its escape
        # sequences.
        pytest.param(
            "Visit \x1b[31mLlanfairpwllgwyngyll\x1b[0m in Wales.",
            10,
            ["Visit", "\x1b[31mLlanfairpwllgwyngyll\x1b[0m", "in Wales."],
            id="styled-long-word",
        ),
    ],
)
def test_wrap_text_keeps_words_whole(text, width, expected):
    """``wrap_text`` breaks lines between words only."""
    assert click.formatting.wrap_text(text, width).splitlines() == expected


def test_wrap_text_rejects_width_below_one():
    """``wrap_text`` raises an error for a width that leaves no room for text."""
    with pytest.raises(ValueError, match="invalid width 0"):
        click.formatting.wrap_text("Rain in Paris.", 0)


@pytest.mark.parametrize(
    ("wrap", "expected"),
    [
        pytest.param(
            lambda: click.formatting.wrap_text(
                " rain", 5, initial_indent=" " * 8, subsequent_indent=" " * 8
            ),
            "        rain",
            id="wrap_text",
        ),
    ],
)
def test_wrap_under_indent_wider_than_width_returns(wrap, expected):
    """Text that starts with a space wraps under an indent wider than the width."""
    result = []
    # The standard library's TextWrapper loops forever on this input with
    # ``break_long_words=True``, on Python 3.10 to 3.16. Run the call in a thread,
    # so a regression fails the test instead of an infinite loop.
    thread = threading.Thread(target=lambda: result.append(wrap()), daemon=True)
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive(), "wrapping did not return"
    assert result == [expected]


def test_write_usage_styled_prefix_keeps_arguments_on_one_line():
    """End-to-end: a downstream-styled ``Usage:`` prefix should not split
    the arguments across two lines.
    """
    styled_prefix = "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m "

    formatter = click.HelpFormatter(width=40)
    formatter.write_usage("cli", "[OPTIONS] CITY", prefix=styled_prefix)
    rendered = formatter.getvalue()

    visible = strip_ansi(rendered)
    assert visible == "Usage: cli [OPTIONS] CITY\n"


@pytest.mark.parametrize(
    ("formatter_kwargs", "current_indent", "prog", "args", "prefix", "expected"),
    [
        # The default prefix used to emit only a blank line because
        # ``wrap_text("", initial_indent=usage_prefix)`` returned ``""`` and discarded
        # the prefix.
        pytest.param(
            {},
            0,
            "Program",
            "",
            None,
            "Usage: Program\n",
            id="empty-args-default-prefix",
        ),
        # A caller-supplied prefix is preserved verbatim.
        pytest.param(
            {},
            0,
            "Program",
            "",
            "Run: ",
            "Run: Program\n",
            id="empty-args-custom-prefix",
        ),
        # ``current_indent`` is preserved even with no args to render.
        pytest.param(
            {},
            4,
            "Program",
            "",
            None,
            "Usage: Program\n",
            id="empty-args-indented",
        ),
        # Prog too long to share a line with args: the wrap branch must not
        # emit a second line.
        pytest.param(
            {"width": 20},
            0,
            "VeryLongProgramName",
            "",
            None,
            "Usage: VeryLongProgramName\n",
            id="empty-args-long-prog",
        ),
        # With non-empty args, the separator space between prog and args is preserved.
        pytest.param(
            {},
            0,
            "Program",
            "[OPTIONS]",
            None,
            "Usage: Program [OPTIONS]\n",
            id="with-args-default-prefix",
        ),
    ],
)
def test_help_formatter_write_usage(
    formatter_kwargs, current_indent, prog, args, prefix, expected
):
    """``HelpFormatter.write_usage`` renders a single usage line whose
    trailing separator tracks whether ``args`` is non-empty.
    """
    f = click.HelpFormatter(**formatter_kwargs)
    f.current_indent = current_indent
    if prefix is None:
        f.write_usage(prog, args)
    else:
        f.write_usage(prog, args, prefix=prefix)
    assert f.getvalue() == expected


def test_help_formatter_write_usage_without_args_styled_prefix():
    """A downstream-styled prefix is preserved when ``args`` is empty:
    the ANSI escape sequences survive, only the trailing separator is
    removed.
    """
    styled_prefix = "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m "
    f = click.HelpFormatter()
    f.write_usage("cli", prefix=styled_prefix)
    rendered = f.getvalue()
    assert strip_ansi(rendered) == "Usage: cli\n"
    assert "\x1b[" in rendered


@pytest.mark.parametrize(
    ("width", "args", "expected"),
    [
        # A line breaks between option names, never after a hyphen inside one.
        pytest.param(
            65,
            "--max-daily-temperature --min-nightly-temperature --wind-speed-unit"
            " --rain-gauge-location --cloud-cover-percentage --sea-level-pressure"
            " --snow-depth-threshold --dew-point-offset",
            [
                "Usage: forecast --max-daily-temperature --min-nightly-temperature",
                "                --wind-speed-unit --rain-gauge-location",
                "                --cloud-cover-percentage --sea-level-pressure",
                "                --snow-depth-threshold --dew-point-offset",
            ],
            id="hyphenated-options",
        ),
        # An argument wider than the line is written whole on its own line,
        # instead of being cut at a hyphen or between two letters.
        pytest.param(
            40,
            "[OPTIONS] --minimum-nightly-temperature CITY",
            [
                "Usage: forecast [OPTIONS]",
                "                --minimum-nightly-temperature",
                "                CITY",
            ],
            id="argument-wider-than-line",
        ),
        # When the arguments go below the program name, each one stays whole
        # too.
        pytest.param(
            16,
            "[OPTIONS] --minimum-nightly-temperature CITY",
            [
                "Usage: forecast",
                "           [OPTIONS]",
                "           --minimum-nightly-temperature",
                "           CITY",
            ],
            id="arguments-below-program-name",
        ),
    ],
)
def test_help_formatter_write_usage_keeps_arguments_whole(width, args, expected):
    """``HelpFormatter.write_usage`` breaks lines between arguments only."""
    f = click.HelpFormatter(width=width)
    f.write_usage("forecast", args)
    # Only line breaks are checked: the program name line can end with a space.
    assert [line.rstrip() for line in f.getvalue().splitlines()] == expected


@pytest.mark.parametrize(
    "write",
    [
        pytest.param(lambda f, text: f.write_usage("forecast", text), id="write_usage"),
        pytest.param(lambda f, text: f.write_text(text), id="write_text"),
        pytest.param(lambda f, text: f.write_dl([("--city", text)]), id="write_dl"),
    ],
)
def test_help_formatter_keeps_words_whole(write):
    """Each ``HelpFormatter`` method that wraps text breaks lines between
    words only.
    """
    words = "Add --avoid-motorways to visit Llanfairpwllgwyngyll by bus.".split()
    f = click.HelpFormatter(width=15)
    write(f, " ".join(words))
    # The usage line and the definition list put a term before the words.
    assert f.getvalue().split()[-len(words) :] == words


@pytest.mark.parametrize(
    ("command_kwargs", "expected_usage_line"),
    [
        # End-to-end regression: an empty ``options_metavar`` with no parameters used to
        # render a blank usage line.
        pytest.param(
            {"options_metavar": ""},
            "Usage: cli",
            id="empty-options-metavar-no-params",
        ),
        # End-to-end regression: ``options_metavar=None`` is the documented
        # way to suppress the ``[OPTIONS]`` slot entirely.
        pytest.param(
            {"options_metavar": None},
            "Usage: cli",
            id="none-options-metavar-no-params",
        ),
    ],
)
def test_command_write_usage_no_args(runner, command_kwargs, expected_usage_line):
    """End-to-end: a command with no parameters and an empty or absent
    ``options_metavar`` renders a usage line with just the program name,
    no trailing space.
    """
    cli = click.Command("cli", **command_kwargs)
    result = runner.invoke(cli, ["--help"])
    assert result.output.splitlines()[0] == expected_usage_line

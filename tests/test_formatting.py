# -*- coding: utf-8 -*-
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
        """Top level command
        """

    @cli.group()
    def a_very_long():
        """Second level
        """

    @a_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command.
        """

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
        """Top level command
        """

    @cli.group()
    def a_very_very_very_long():
        """Second level
        """

    @a_very_very_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command.
        """

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
        """Top level command

        """

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
        click.echo("arg:{}".format(arg))

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
        "Error: Invalid value for 'metavar': 3.14 is not a valid integer",
    ]


def test_formatting_usage_error_nested(runner):
    @click.group()
    def cmd():
        pass

    @cmd.command()
    @click.argument("bar")
    def foo(bar):
        click.echo("foo:{}".format(bar))

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
        click.echo("arg:{}".format(arg))

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
        click.echo("arg:{}".format(arg))

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
        def get_metavar(self, param):
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


def test_global_show_default(runner):
    @click.command(context_settings=dict(show_default=True))
    @click.option("-f", "in_file", default="out.txt", help="Output file name")
    def cli():
        pass

    result = runner.invoke(cli, ["--help"],)
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  -f TEXT  Output file name  [default: out.txt]",
        "  --help   Show this message and exit.  [default: False]",
    ]


def test_formatting_usage_multiline_option_padding(runner):
    @click.command("foo")
    @click.option("--bar", help="This help message will be padded if it wraps.")
    def cli():
        pass

    result = runner.invoke(cli, "--help", terminal_width=45)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS]",
        "",
        "Options:",
        "  --bar TEXT  This help message will be",
        "              padded if it wraps.",
        "",
        "  --help      Show this message and exit.",
    ]


def test_formatting_usage_no_option_padding(runner):
    @click.command("foo")
    @click.option("--bar", help="This help message will be padded if it wraps.")
    def cli():
        pass

    result = runner.invoke(cli, "--help", terminal_width=80)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS]",
        "",
        "Options:",
        "  --bar TEXT  This help message will be padded if it wraps.",
        "  --help      Show this message and exit.",
    ]


TESTCASES_SUCCEEDING_WRAP_TEXT = [

    # Test cases for succeeding wrap_text()
    #
    # Each list item is a testcase tuple with these items:
    # * desc: Short testcase description.
    # * args: Positional arguments for the tested function.
    # * kwargs: Keyword arguments for the tested function.
    # * exp_ret: expected return value of the tested function.

    (
        "Defaults of optional arguments",
        [
            'a b c d e f g h i j k l m n o p q r s t '  # 40
            'u v w x y z 1 2 3 4 5 6 7 8 9 0 1 2 3 4 '  # 40
            # width=78
            # initial_indent=""
            # subsequent_indent=""
            # preserve_paragraphs=False
        ],
        dict(),
        'a b c d e f g h i j k l m n o p q r s t '
        'u v w x y z 1 2 3 4 5 6 7 8 9 0 1 2 3\n'
        '4'
    ),
    (
        "Order of positional arguments",
        [
            'a b c d e f g h j i k',  # text
            20,  # width
            '....',  # initial_indent
            '----',  # subsequent_indent
            False,  # preserve_paragraphs
        ],
        dict(),
        '....a b c d e f g h\n'
        '----j i k'
    ),
    (
        "Names of keyword arguments",
        [],
        dict(
            text='a b c d e f g h j i k',
            width=20,
            initial_indent='....',
            subsequent_indent='----',
            preserve_paragraphs=False,
        ),
        '....a b c d e f g h\n'
        '----j i k'
    ),
    (
        "Use of different indent strings, with preserve=False",
        [],
        dict(
            text='a b c d e f g h i j k l m n o p q r s t ',
            width=20,
            initial_indent='....',
            subsequent_indent='----',
            preserve_paragraphs=False,
        ),
        '....a b c d e f g h\n'
        '----i j k l m n o p\n'
        '----q r s t'
    ),
    (
        "Use of different indent strings, with preserve=True",
        [],
        dict(
            text='a b c d e f g h i j k l m n o p q r s t ',
            width=20,
            initial_indent='....',
            subsequent_indent='----',
            preserve_paragraphs=True,
        ),
        '....a b c d e f g h\n'
        '----i j k l m n o p\n'
        '----q r s t'
    ),
    (
        "One line that meets width exactly, with preserve=False",
        [],
        dict(
            text='a b c d e',
            width=9,
            preserve_paragraphs=False,
        ),
        'a b c d e'
    ),
    (
        "One line that meets width exactly, with preserve=True",
        [],
        dict(
            text='a b c d e',
            width=9,
            preserve_paragraphs=True,
        ),
        'a b c d e'
    ),
    (
        "One line that wraps at end of word, with preserve=False",
        [],
        dict(
            text='a b c d e f g h i j',
            width=9,
            preserve_paragraphs=False,
        ),
        'a b c d e\n'
        'f g h i j'
    ),
    (
        "One line that wraps at end of word, with preserve=True",
        [],
        dict(
            text='a b c d e f g h i j',
            width=9,
            preserve_paragraphs=True,
        ),
        'a b c d e\n'
        'f g h i j'
    ),
    (
        "Initial indent of 1 char, with preserve=False",
        [],
        dict(
            text='a b c d e',
            width=9,
            initial_indent='.',
            subsequent_indent='',
            preserve_paragraphs=False,
        ),
        '.a b c d\n'
        'e'
    ),
    (
        "Initial indent of 1 char, with preserve=True",
        [],
        dict(
            text='a b c d e',
            width=9,
            initial_indent='.',
            subsequent_indent='',
            preserve_paragraphs=True,
        ),
        '.a b c d\n'
        'e'
    ),
    (
        "Initial indent and subsequent indent of 1 char, with preserve=False",
        [],
        dict(
            text='a b c d e f g h i',
            width=9,
            initial_indent='.',
            subsequent_indent='-',
            preserve_paragraphs=False,
        ),
        '.a b c d\n'
        '-e f g h\n'
        '-i'
    ),
    (
        "Initial indent and subsequent indent of 1 char, with preserve=True",
        [],
        dict(
            text='a b c d e f g h i',
            width=9,
            initial_indent='.',
            subsequent_indent='-',
            preserve_paragraphs=True,
        ),
        '.a b c d\n'
        '-e f g h\n'
        '-i'
    ),
    (
        "Line with long second word that exactly fits the width, 2 indent, "
        "with preserve=False",
        [],
        dict(
            text='a longsecdword',
            width=16,
            initial_indent='..',
            subsequent_indent='--',
            preserve_paragraphs=False,
        ),
        '..a longsecdword'
    ),
    (
        "Line with long second word that exactly fits the width, 2 indent, "
        "with preserve=True",
        [],
        dict(
            text='a longsecdword',
            width=16,
            initial_indent='..',
            subsequent_indent='--',
            preserve_paragraphs=True,
        ),
        '..a longsecdword'
    ),
    (
        "Line with long second word that exceeds the width by 1, 2 indent, "
        "with preserve=False",
        [],
        dict(
            text='a longsecdword',
            width=15,
            initial_indent='..',
            subsequent_indent='--',
            preserve_paragraphs=False,
        ),
        '..a\n'
        '--longsecdword'
    ),
    (
        "Line with long second word that exceeds the width by 1, 2 indent, "
        "with preserve=True",
        [],
        dict(
            text='a longsecdword',
            width=15,
            initial_indent='..',
            subsequent_indent='--',
            preserve_paragraphs=True,
        ),
        '..a\n'
        '--longsecdword'
    ),
    (
        "Long second word that itself exactly fits the width, preserve=False",
        [],
        dict(
            text='a longsecdword',
            width=12,
            preserve_paragraphs=False,
        ),
        'a\n'
        'longsecdword'
    ),
    (
        "Long second word that itself exactly fits the width, preserve=True",
        [],
        dict(
            text='a longsecdword',
            width=12,
            preserve_paragraphs=True,
        ),
        'a\n'
        'longsecdword'
    ),
    (
        "Maintaining width overrules word breakage, preserve=False",
        [],
        dict(
            text='a longsecdword',
            width=11,
            preserve_paragraphs=False,
        ),
        'a longsecdw\n'
        'ord'
    ),
    (
        "Maintaining width overrules word breakage, preserve=True",
        [],
        dict(
            text='a longsecdword',
            width=11,
            preserve_paragraphs=True,
        ),
        'a longsecdw\n'
        'ord'
    ),
    (
        "Long width 400, preserve=False",
        [],
        dict(
            text='abc ' * 200,
            width=400,
            preserve_paragraphs=False,
        ),
        ('abc ' * 99) + 'abc\n' + \
        ('abc ' * 99) + 'abc'
    ),
    (
        "Long width 400, preserve=True",
        [],
        dict(
            text='abc ' * 200,
            width=400,
            preserve_paragraphs=True,
        ),
        ('abc ' * 99) + 'abc\n' + \
        ('abc ' * 99) + 'abc'
    ),
    (
        "Initial spaces on line are preserved, with preserve=False",
        [],
        dict(
            text='   abd def ghi',
            width=6,
            preserve_paragraphs=False,
        ),
        '   abd\n'
        'def\n'
        'ghi'
    ),
    (
        "Initial spaces on line are used as intial and subsequent indent, "
        "with preserve=True",
        [],
        dict(
            text='   abd def ghi',
            width=6,
            preserve_paragraphs=True,
        ),
        '   abd\n'
        '   def\n'
        '   ghi'
    ),
    (
        "Trailing spaces get stripped, with preserve=False",
        [],
        dict(
            text='abc def ghi   ',
            width=6,
            preserve_paragraphs=False,
        ),
        'abc\n'
        'def\n'
        'ghi'
    ),
    (
        "Trailing spaces get stripped, with preserve=True",
        [],
        dict(
            text='abc def ghi   ',
            width=6,
            preserve_paragraphs=True,
        ),
        'abc\n'
        'def\n'
        'ghi'
    ),
    (
        "Spaces within line are preserved, with preserve=False",
        [],
        dict(
            text=
            'line   A1\n'
            'line     A2\n',
            width=12,
            preserve_paragraphs=False,
        ),
        'line   A1\n'
        'line     A2'
    ),
    (
        "Spaces within line are preserved, with preserve=True",
        [],
        dict(
            text=
            'line   A1\n'
            'line     A2\n',
            width=12,
            preserve_paragraphs=True,
        ),
        'line   A1\n'
        'line     A2'
    ),
    (
        "Two lines stay separate, with preserve=False",
        [],
        dict(
            text=
            'line A1\n'
            'line A2\n',
            width=12,
            preserve_paragraphs=False,
        ),
        'line A1\n'
        'line\n'  # TODO: Unmotivated line break, see issue #1502
        'A2'
    ),
    (
        "Two lines get combined and wrapped, with preserve=True",
        [],
        dict(
            text=
            'line A1\n'
            'line A2\n',
            width=12,
            preserve_paragraphs=True,
        ),
        'line A1 line\n'
        'A2'
    ),
    (
        "Two paragraphs stay separate and don't get wrapped, "
        "with preserve=False",
        [],
        dict(
            text=
            'line A1\n'
            'line A2\n'
            '\n'
            'line B1\n'
            'line B2\n',
            width=12,
            preserve_paragraphs=False,
        ),
        'line A1\n'
        'line\n'  # TODO: Unmotivated line break, see issue #1502
        'A2\n'
        '\n'
        'line B1\n'
        'line B2'
    ),
    (
        "Two paragraphs stay separate but get wrapped, with preserve=True",
        [],
        dict(
            text=
            'line A1\n'
            'line A2\n'
            '\n'
            'line B1\n'
            'line B2\n',
            width=12,
            preserve_paragraphs=True,
        ),
        'line A1 line\n'
        'A2\n'
        '\n'
        'line B1 line\n'
        'B2'
    ),
    (
        "First paragraph with \\b does not get wrapped, second paragraph "
        "without \\b gets wrapped, with preserve=True",
        [],
        dict(
            text=
            '\b\n'
            'line A1\n'
            'line A2\n'
            '\n'
            'line B1\n'
            'line B2\n',
            width=12,
            preserve_paragraphs=True,
        ),
        'line A1\n'
        'line A2\n'
        '\n'
        'line B1 line\n'
        'B2'
    ),
    (
        "Two paragraphs with different leading space get different indent, "
        "with preserve=True",
        [],
        dict(
            text=
            '  line A1\n'
            'line A2\n'
            '\n'
            '    line B1\n'
            'line B2\n',
            width=16,
            preserve_paragraphs=True,
        ),
        '  line A1 line\n'
        '  A2\n'
        '\n'
        '    line B1 line\n'
        '    B2'
    ),
    (
        "Two lines in a paragraph with different leading space get aligned to "
        "indent of first line, with preserve=True",
        [],
        dict(
            text=
            '  line A1\n'
            '    line A2\n'
            '\n'
            '    line B1\n'
            '  line B2\n',
            width=11,
            preserve_paragraphs=True,
        ),
        '  line A1\n'
        '  line A2\n'
        '\n'
        '    line B1\n'
        '    line B2'
    ),
]


@pytest.mark.parametrize(
    "desc, args, kwargs, exp_ret",
    TESTCASES_SUCCEEDING_WRAP_TEXT)
def test_succeeding_wrap_text(desc, args, kwargs, exp_ret):
    """
    Test for succeeding wrap_text()
    """

    # The code to be tested
    act_ret = click.wrap_text(*args, **kwargs)

    assert act_ret == exp_ret

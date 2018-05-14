# -*- coding: utf-8 -*-
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

    result = runner.invoke(cli, ['--help'], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: cli [OPTIONS]',
        '',
        '  First paragraph.',
        '',
        '  This is a very long second paragraph and not correctly',
        '  wrapped but it will be rewrapped.',
        '',
        '  This is',
        '  a paragraph',
        '  without rewrapping.',
        '',
        '  1',
        '   2',
        '    3',
        '',
        '  And this is a paragraph that will be rewrapped again.',
        '',
        'Options:',
        '  --help  Show this message and exit.',
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
    @click.argument('first')
    @click.argument('second')
    @click.argument('third')
    @click.argument('fourth')
    @click.argument('fifth')
    @click.argument('sixth')
    def command():
        """A command.
        """

    # 54 is chosen as a length where the second line is one character
    # longer than the maximum length.
    result = runner.invoke(cli, ['a-very-long', 'command', '--help'],
                           terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: cli a-very-long command [OPTIONS] FIRST SECOND',
        '                               THIRD FOURTH FIFTH',
        '                               SIXTH',
        '',
        '  A command.',
        '',
        'Options:',
        '  --help  Show this message and exit.',
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
    @click.argument('first')
    @click.argument('second')
    @click.argument('third')
    @click.argument('fourth')
    @click.argument('fifth')
    @click.argument('sixth')
    def command():
        """A command.
        """

    result = runner.invoke(cli, ['a-very-very-very-long', 'command', '--help'],
                           terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: cli a-very-very-very-long command ',
        '           [OPTIONS] FIRST SECOND THIRD FOURTH FIFTH',
        '           SIXTH',
        '',
        '  A command.',
        '',
        'Options:',
        '  --help  Show this message and exit.',
    ]


def test_formatting_empty_help_lines(runner):
    @click.command()
    def cli():
        """Top level command

        """

    result = runner.invoke(cli, ['--help'])
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: cli [OPTIONS]',
        '',
        '  Top level command',
        '',
        '',
        '',
        'Options:',
        '  --help  Show this message and exit.',
    ]


def test_formatting_usage_error(runner):
    @click.command()
    @click.argument('arg')
    def cmd(arg):
        click.echo('arg:' + arg)

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        'Usage: cmd [OPTIONS] ARG',
        'Try "cmd --help" for help.',
        '',
        'Error: Missing argument "arg".'
    ]


def test_formatting_usage_error_metavar(runner):
    @click.command()
    @click.argument('arg', metavar='metavar')
    def cmd(arg):
        click.echo('arg:' + arg)

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        'Usage: cmd [OPTIONS] metavar',
        'Try "cmd --help" for help.',
        '',
        'Error: Missing argument "metavar".'
    ]


def test_formatting_usage_error_nested(runner):
    @click.group()
    def cmd():
        pass

    @cmd.command()
    @click.argument('bar')
    def foo(bar):
        click.echo('foo:' + bar)

    result = runner.invoke(cmd, ['foo'])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        'Usage: cmd foo [OPTIONS] BAR',
        'Try "cmd foo --help" for help.',
        '',
        'Error: Missing argument "bar".'
    ]


def test_formatting_usage_error_no_help(runner):
    @click.command(add_help_option=False)
    @click.argument('arg')
    def cmd(arg):
        click.echo('arg:' + arg)

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        'Usage: cmd [OPTIONS] ARG',
        '',
        'Error: Missing argument "arg".'
    ]


def test_formatting_usage_custom_help(runner):
    @click.command(context_settings=dict(help_option_names=['--man']))
    @click.argument('arg')
    def cmd(arg):
        click.echo('arg:' + arg)

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        'Usage: cmd [OPTIONS] ARG',
        'Try "cmd --man" for help.',
        '',
        'Error: Missing argument "arg".'
    ]

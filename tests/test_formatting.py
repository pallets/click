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

    # 54 is chosen as a lenthg where the second line is one character
    # longer than the maximum length.
    result = runner.invoke(cli, ['a_very_long', 'command', '--help'],
                           terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: cli a_very_long command [OPTIONS] FIRST SECOND',
        '                               THIRD FOURTH FIFTH',
        '                               SIXTH',
        '',
        '  A command.',
        '',
        'Options:',
        '  --help  Show this message and exit.',
    ]

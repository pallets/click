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

@pytest.mark.parametrize('terminal_width', range(20))
def test_small_terminal(runner, terminal_width):
    @click.command()
    def cli():
        '''A paragraph.

        And another one.
        '''

    result = runner.invoke(cli, ['--help'], terminal_width=terminal_width)
    if terminal_width >= 11:
        assert not result.exception
    else:
        assert isinstance(result.exception, SystemExit)
        assert result.output.strip() == (
            'Error: Your terminal is too small. Expand your terminal by at '
            'least {0} columns for proper help output.'
        ).format(11 - terminal_width)

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

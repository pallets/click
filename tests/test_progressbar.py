# -*- coding: utf-8 -*-
import click
from mock import patch


def test_progressbar_strip_regression(runner):
    label = '    padded line'

    @click.command()
    def cli():
        with click.progressbar(tuple(range(10)), label=label) as progress:
            for thing in progress:
                pass

    with patch('click._compat.isatty') as isatty:
        isatty.return_value = True
        assert label in runner.invoke(cli, []).output

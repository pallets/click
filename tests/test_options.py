# -*- coding: utf-8 -*-
import re
import click


def test_prefixes(runner):
    @click.command()
    @click.option('++foo', is_flag=True, help='das foo')
    @click.option('--bar', is_flag=True, help='das bar')
    def cli(foo, bar):
        click.echo('foo=%s bar=%s' % (foo, bar))

    result = runner.invoke(cli, ['++foo', '--bar'])
    assert not result.exception
    assert result.output == 'foo=True bar=True\n'

    result = runner.invoke(cli, ['--help'])
    assert re.search(r'\+\+foo\s+das foo', result.output) is not None
    assert re.search(r'--bar\s+das bar', result.output) is not None

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import click


def test_custom_validation(runner):
    def validate_pos_int(ctx, value):
        if value < 0:
            raise click.BadParameter('That’s no good!')
        return value

    @click.command()
    @click.option('--foo', callback=validate_pos_int, default=1)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ['--foo', '-1'])
    assert 'Invalid value for "--foo": That’s no good' in result.output

    result = runner.invoke(cmd, ['--foo', '42'])
    assert result.output == '42\n'

# -*- coding: utf-8 -*-

import click
from click._bashcomplete import get_choices

def test_basic():
    @click.group()
    @click.option('--global-opt')
    def cli(global_opt):
        pass

    @cli.command()
    @click.option('--local-opt')
    def sub(local_opt):
        pass

    COLORS = ['red', 'green', 'blue']
    @cli.command()
    @click.argument('color', autocompletion=COLORS)
    def sub2(color):
        pass

    def get_colors(ctx, args, incomplete):
        return COLORS

    @cli.command()
    @click.argument('color', autocompletion=get_colors)
    def sub3(color):
        pass

    assert list(get_choices(cli, 'lol', [], '')) == ['sub', 'sub2', 'sub3']
    assert list(get_choices(cli, 'lol', [], '-')) == ['--global-opt']
    assert list(get_choices(cli, 'lol', ['sub'], '')) == []
    assert list(get_choices(cli, 'lol', ['sub'], '-')) == ['--local-opt']
    assert list(get_choices(cli, 'lol', ['sub2'], '')) == COLORS
    assert list(get_choices(cli, 'lol', ['sub2'], 'g')) == ['green']
    assert list(get_choices(cli, 'lol', ['sub3'], '')) == COLORS
    assert list(get_choices(cli, 'lol', ['sub2'], 'b')) == ['blue']

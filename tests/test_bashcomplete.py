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

    assert list(get_choices(cli, 'lol', [], '')) == ['sub']
    assert list(get_choices(cli, 'lol', [], '-')) == ['--global-opt']
    assert list(get_choices(cli, 'lol', ['sub'], '')) == []
    assert list(get_choices(cli, 'lol', ['sub'], '-')) == ['--local-opt']

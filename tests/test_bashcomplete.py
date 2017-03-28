# -*- coding: utf-8 -*-

import click
from click._bashcomplete import get_choices


def test_single_command():
    @click.command()
    @click.option('--local-opt')
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--local-opt']
    assert list(get_choices(cli, 'lol', [], '')) == []


def test_small_chain():
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


def test_long_chain():
    @click.group('cli')
    @click.option('--cli-opt')
    def cli(cli_opt):
        pass

    @cli.group('asub')
    @click.option('--asub-opt')
    def asub(asub_opt):
        pass

    @asub.group('bsub')
    @click.option('--bsub-opt')
    def bsub(bsub_opt):
        pass

    COLORS = ['red', 'green', 'blue']
    def get_colors(ctx, args, incomplete):
        return COLORS

    CSUB_OPT_CHOICES = ['foo', 'bar']
    CSUB_CHOICES = ['bar', 'baz']
    @bsub.command('csub')
    @click.option('--csub-opt', type=click.Choice(CSUB_OPT_CHOICES))
    @click.option('--csub', type=click.Choice(CSUB_CHOICES))
    @click.argument('color', autocompletion=get_colors)
    def csub(csub_opt, color):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--cli-opt']
    assert list(get_choices(cli, 'lol', [], '')) == ['asub']
    assert list(get_choices(cli, 'lol', ['asub'], '-')) == ['--asub-opt']
    assert list(get_choices(cli, 'lol', ['asub'], '')) == ['bsub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '-')) == ['--bsub-opt']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '')) == ['csub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '-')) == ['--csub-opt', '--csub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub-opt'], '')) == CSUB_OPT_CHOICES
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '--csub')) == ['--csub-opt', '--csub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub'], '')) == CSUB_CHOICES
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub-opt'], 'f')) == ['foo']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '')) == COLORS
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], 'b')) == ['blue']

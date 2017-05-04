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

    @bsub.command('csub')
    @click.option('--csub-opt')
    def csub(csub_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--cli-opt']
    assert list(get_choices(cli, 'lol', [], '')) == ['asub']
    assert list(get_choices(cli, 'lol', ['asub'], '-')) == ['--asub-opt']
    assert list(get_choices(cli, 'lol', ['asub'], '')) == ['bsub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '-')) == ['--bsub-opt']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '')) == ['csub']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '-')) == ['--csub-opt']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '')) == []


def test_chaining():
    @click.group('cli', chain=True)
    @click.option('--cli-opt')
    def cli(cli_opt):
        pass

    @cli.command('asub')
    @click.option('--asub-opt')
    def asub(asub_opt):
        pass

    @cli.command('bsub')
    @click.option('--bsub-opt')
    def bsub(bsub_opt, arg):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--cli-opt']
    assert list(get_choices(cli, 'lol', [], '')) == ['asub', 'bsub']
    assert list(get_choices(cli, 'lol', ['asub'], '-')) == ['--asub-opt']
    assert list(get_choices(cli, 'lol', ['asub'], '')) == ['bsub']
    assert list(get_choices(cli, 'lol', ['bsub'], '')) == ['asub']
    assert list(get_choices(cli, 'lol', ['asub', '--asub-opt', '5', 'bsub'], '-')) == ['--bsub-opt']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '-')) == ['--bsub-opt']

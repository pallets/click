# -*- coding: utf-8 -*-

import click
from click._bashcomplete import get_choices
import os
import tempfile
import shutil
from contextlib import contextmanager


def test_single_command():
    @click.command()
    @click.option('--local-opt')
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--local-opt ']
    assert list(get_choices(cli, 'lol', [], '')) == []


def test_boolean_flag():
    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--shout ', '--no-shout ']


def test_multi_value_option():
    @click.group()
    @click.option('--pos', nargs=2, type=float)
    def cli(local_opt):
        pass

    @cli.command()
    @click.option('--local-opt')
    def sub(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--pos ']
    assert list(get_choices(cli, 'lol', ['--pos'], '')) == []
    assert list(get_choices(cli, 'lol', ['--pos', '1.0'], '')) == []
    assert list(get_choices(cli, 'lol', ['--pos', '1.0', '1.0'], '')) == ['sub ']


def test_multi_option():
    @click.command()
    @click.option('--message', '-m', multiple=True)
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--message ', '-m ']
    assert list(get_choices(cli, 'lol', ['-m'], '')) == []


def test_small_chain():
    @click.group()
    @click.option('--global-opt')
    def cli(global_opt):
        pass

    @cli.command()
    @click.option('--local-opt')
    def sub(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '')) == ['sub ']
    assert list(get_choices(cli, 'lol', [], '-')) == ['--global-opt ']
    assert list(get_choices(cli, 'lol', ['sub'], '')) == []
    assert list(get_choices(cli, 'lol', ['sub'], '-')) == ['--local-opt ']


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
        for c in COLORS:
            yield c + ' '

    CSUB_OPT_CHOICES = ['foo', 'bar']
    CSUB_CHOICES = ['bar', 'baz']
    @bsub.command('csub')
    @click.option('--csub-opt', type=click.Choice(CSUB_OPT_CHOICES))
    @click.option('--csub', type=click.Choice(CSUB_CHOICES))
    @click.argument('color', autocompletion=get_colors)
    def csub(csub_opt, color):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--cli-opt ']
    assert list(get_choices(cli, 'lol', [], '')) == ['asub ']
    assert list(get_choices(cli, 'lol', ['asub'], '-')) == ['--asub-opt ']
    assert list(get_choices(cli, 'lol', ['asub'], '')) == ['bsub ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '-')) == ['--bsub-opt ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '')) == ['csub ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '-')) == ['--csub-opt ', '--csub ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub-opt'], '')) == [o + ' ' for o in CSUB_OPT_CHOICES]
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '--csub')) == ['--csub-opt ', '--csub ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub'], '')) == [o + ' ' for o in CSUB_CHOICES]
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub', '--csub-opt'], 'f')) == ['foo ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], '')) == [o + ' ' for o in COLORS]
    assert list(get_choices(cli, 'lol', ['asub', 'bsub', 'csub'], 'b')) == ['blue ']


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
    @click.argument('arg', type=click.Choice(['arg1', 'arg2']))
    def bsub(bsub_opt, arg):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--cli-opt ']
    assert list(get_choices(cli, 'lol', [], '')) == ['asub ', 'bsub ']
    assert list(get_choices(cli, 'lol', ['asub'], '-')) == ['--asub-opt ']
    assert list(get_choices(cli, 'lol', ['asub'], '')) == ['bsub ']
    assert list(get_choices(cli, 'lol', ['bsub'], '')) == ['arg1 ', 'arg2 ', 'asub ']
    assert list(get_choices(cli, 'lol', ['asub', '--asub-opt', '5', 'bsub'], '-')) == ['--bsub-opt ']
    assert list(get_choices(cli, 'lol', ['asub', 'bsub'], '-')) == ['--bsub-opt ']


def test_argument_choice():
    @click.command()
    @click.argument('arg1', required=False, type=click.Choice(['arg11', 'arg12']))
    @click.argument('arg2', required=False, type=click.Choice(['arg21', 'arg22']))
    @click.argument('arg3', required=False, type=click.Choice(['arg', 'argument']))
    def cli():
        pass

    assert list(get_choices(cli, 'lol', [], '')) == ['arg11 ', 'arg12 ']
    assert list(get_choices(cli, 'lol', [], 'arg')) == ['arg11 ', 'arg12 ']
    assert list(get_choices(cli, 'lol', ['arg11'], '')) == ['arg21 ', 'arg22 ']
    assert list(get_choices(cli, 'lol', ['arg12', 'arg21'], '')) == ['arg ', 'argument ']
    assert list(get_choices(cli, 'lol', ['arg12', 'arg21'], 'argu')) == ['argument ']


def test_option_choice():
    @click.command()
    @click.option('--opt1', type=click.Choice(['opt11', 'opt12']))
    @click.option('--opt2', type=click.Choice(['opt21', 'opt22']))
    @click.option('--opt3', type=click.Choice(['opt', 'option']))
    def cli():
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--opt1 ', '--opt2 ', '--opt3 ']
    assert list(get_choices(cli, 'lol', [], '--opt')) == ['--opt1 ', '--opt2 ', '--opt3 ']
    assert list(get_choices(cli, 'lol', [], '--opt1=')) == ['opt11 ', 'opt12 ']
    assert list(get_choices(cli, 'lol', [], '--opt2=')) == ['opt21 ', 'opt22 ']
    assert list(get_choices(cli, 'lol', ['--opt2'], '=')) == ['opt21 ', 'opt22 ']
    assert list(get_choices(cli, 'lol', ['--opt2', '='], 'opt')) == ['opt21 ', 'opt22 ']
    assert list(get_choices(cli, 'lol', ['--opt1'], '')) == ['opt11 ', 'opt12 ']
    assert list(get_choices(cli, 'lol', ['--opt2'], '')) == ['opt21 ', 'opt22 ']
    assert list(get_choices(cli, 'lol', ['--opt1', 'opt11', '--opt2'], '')) == ['opt21 ', 'opt22 ']
    assert list(get_choices(cli, 'lol', ['--opt2', 'opt21'], '-')) == ['--opt1 ', '--opt3 ']
    assert list(get_choices(cli, 'lol', ['--opt1', 'opt11'], '-')) == ['--opt2 ', '--opt3 ']
    assert list(get_choices(cli, 'lol', ['--opt1'], 'opt')) == ['opt11 ', 'opt12 ']
    assert list(get_choices(cli, 'lol', ['--opt3'], 'opti')) == ['option ']

    assert list(get_choices(cli, 'lol', ['--opt1', 'invalid_opt'], '-')) == ['--opt2 ', '--opt3 ']


def test_option_and_arg_choice():
    @click.command()
    @click.option('--opt1', type=click.Choice(['opt11', 'opt12']))
    @click.argument('arg1', required=False, type=click.Choice(['arg11', 'arg12']))
    @click.option('--opt2', type=click.Choice(['opt21', 'opt22']))
    def cli():
        pass

    assert list(get_choices(cli, 'lol', ['--opt1'], '')) == ['opt11 ', 'opt12 ']
    assert list(get_choices(cli, 'lol', [''], '--opt1=')) == ['opt11 ', 'opt12 ']
    assert list(get_choices(cli, 'lol', [], '')) == ['arg11 ', 'arg12 ']
    assert list(get_choices(cli, 'lol', ['--opt2'], '')) == ['opt21 ', 'opt22 ']


def test_boolean_flag_choice():
    @click.command()
    @click.option('--shout/--no-shout', default=False)
    @click.argument('arg', required=False, type=click.Choice(['arg1', 'arg2']))
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', [], '-')) == ['--shout ', '--no-shout ']
    assert list(get_choices(cli, 'lol', ['--shout'], '')) == ['arg1 ', 'arg2 ']


def test_multi_value_option_choice():
    @click.command()
    @click.option('--pos', nargs=2, type=click.Choice(['pos1', 'pos2']))
    @click.argument('arg', required=False, type=click.Choice(['arg1', 'arg2']))
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', ['--pos'], '')) == ['pos1 ', 'pos2 ']
    assert list(get_choices(cli, 'lol', ['--pos', 'pos1'], '')) == ['pos1 ', 'pos2 ']
    assert list(get_choices(cli, 'lol', ['--pos', 'pos1', 'pos2'], '')) == ['arg1 ', 'arg2 ']
    assert list(get_choices(cli, 'lol', ['--pos', 'pos1', 'pos2', 'arg1'], '')) == []


def test_multi_option_choice():
    @click.command()
    @click.option('--message', '-m', multiple=True, type=click.Choice(['m1', 'm2']))
    @click.argument('arg', required=False, type=click.Choice(['arg1', 'arg2']))
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', ['-m'], '')) == ['m1 ', 'm2 ']
    assert list(get_choices(cli, 'lol', ['-m', 'm1', '-m'], '')) == ['m1 ', 'm2 ']
    assert list(get_choices(cli, 'lol', ['-m', 'm1'], '')) == ['arg1 ', 'arg2 ']


def test_variadic_argument_choice():
    @click.command()
    @click.argument('src', nargs=-1, type=click.Choice(['src1', 'src2']))
    def cli(local_opt):
        pass

    assert list(get_choices(cli, 'lol', ['src1', 'src2'], '')) == ['src1 ', 'src2 ']


def test_long_chain_choice():
    @click.group()
    def cli():
        pass

    @cli.group('sub')
    @click.option('--sub-opt', type=click.Choice(['subopt1', 'subopt2']))
    @click.argument('sub-arg', required=False, type=click.Choice(['subarg1', 'subarg2']))
    def sub(sub_opt):
        pass

    @sub.command('bsub')
    @click.option('--bsub-opt', type=click.Choice(['bsubopt1', 'bsubopt2']))
    @click.argument('bsub-arg1', required=False, type=click.Choice(['bsubarg1', 'bsubarg2']))
    @click.argument('bbsub-arg2', required=False, type=click.Choice(['bbsubarg1', 'bbsubarg2']))
    def bsub(bsub_opt):
        pass

    assert list(get_choices(cli, 'lol', ['sub'], '')) == ['subarg1 ', 'subarg2 ']
    assert list(get_choices(cli, 'lol', ['sub', '--sub-opt'], '')) == ['subopt1 ', 'subopt2 ']
    assert list(get_choices(cli, 'lol', ['sub', '--sub-opt', 'subopt1'], '')) == \
        ['subarg1 ', 'subarg2 ']
    assert list(get_choices(cli, 'lol',
        ['sub', '--sub-opt', 'subopt1', 'subarg1', 'bsub'], '-')) == ['--bsub-opt ']
    assert list(get_choices(cli, 'lol',
        ['sub', '--sub-opt', 'subopt1', 'subarg1', 'bsub', '--bsub-opt'], '')) == \
        ['bsubopt1 ', 'bsubopt2 ']
    assert list(get_choices(cli, 'lol',
        ['sub', '--sub-opt', 'subopt1', 'subarg1', 'bsub', '--bsub-opt', 'bsubopt1', 'bsubarg1'],
                            '')) == ['bbsubarg1 ', 'bbsubarg2 ']


# Helper for path tests
@contextmanager
def tempdir(chdir=False):
    temp = tempfile.mkdtemp()
    cwd = os.getcwd()

    if chdir:
        os.chdir(temp)

    yield temp

    os.chdir(cwd)
    shutil.rmtree(temp)


def test_absolute_path():
    @click.command()
    @click.option('--path', type=click.Path())
    def cli(local_opt):
        pass

    with tempdir() as temp:
        os.mkdir(os.path.join(temp, 'dira'))
        os.mkdir(os.path.join(temp, 'dirb'))
        with open(os.path.join(temp, 'dirb', 'file.txt'), 'w') as f:
            f.write('content')

        assert list(get_choices(cli, 'lol', ['--path'], temp)) == [temp + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], temp + os.path.sep)) == \
            [os.path.join(temp, 'dira') + os.path.sep, os.path.join(temp, 'dirb') + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], os.path.join(temp, 'dirb'))) == \
            [os.path.join(temp, 'dirb') + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], os.path.join(temp, 'dirb') + os.path.sep)) == \
            [os.path.join(temp, 'dirb', 'file.txt') + ' ']


def test_relative_path():
    @click.command()
    @click.option('--path', type=click.Path())
    def cli(local_opt):
        pass

    with tempdir(chdir=True) as temp:
        os.mkdir(os.path.join(temp, 'dira'))
        os.mkdir(os.path.join(temp, 'dirb'))
        with open(os.path.join(temp, 'dirb', 'file.txt'), 'w') as f:
            f.write('content')

        assert list(get_choices(cli, 'lol', ['--path'], '')) == ['dira' + os.path.sep, 'dirb' + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], 'dir')) == ['dira' + os.path.sep, 'dirb' + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], 'x')) == []
        assert list(get_choices(cli, 'lol', ['--path'], os.path.join('x', 'y', 'z'))) == []
        assert list(get_choices(cli, 'lol', ['--path'], 'dira')) == ['dira' + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], 'dirb' + os.path.sep)) == [os.path.join('dirb', 'file.txt') + ' ']


def test_directories_only():
    @click.command()
    @click.option('--path', type=click.Path(file_okay=False))
    def cli(local_opt):
        pass

    with tempdir(chdir=True) as temp:
        os.mkdir(os.path.join(temp, 'dira'))
        os.mkdir(os.path.join(temp, 'dirb'))
        with open(os.path.join(temp, 'file.txt'), 'w') as f:
            f.write('content')

        assert list(get_choices(cli, 'lol', ['--path'], '')) == ['dira' + os.path.sep, 'dirb' + os.path.sep]
        assert list(get_choices(cli, 'lol', ['--path'], 'dir')) == ['dira' + os.path.sep, 'dirb' + os.path.sep]


def test_files_only():
    @click.command()
    @click.option('--path', type=click.Path(dir_okay=False))
    def cli(local_opt):
        pass

    with tempdir(chdir=True) as temp:
        os.mkdir(os.path.join(temp, 'dira'))
        os.mkdir(os.path.join(temp, 'dirb'))
        with open(os.path.join(temp, 'file.txt'), 'w') as f:
            f.write('content')

        assert list(get_choices(cli, 'lol', ['--path'], '')) == ['file.txt ']
        assert list(get_choices(cli, 'lol', ['--path'], 'fil')) == ['file.txt ']
        assert list(get_choices(cli, 'lol', ['--path'], 'dir')) == []

# -*- coding: utf-8 -*-
import re
import os
import click
import pytest


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


def test_invalid_option(runner):
    try:
        @click.command()
        @click.option('foo')
        def cli(foo):
            pass
    except TypeError as e:
        assert 'No options defined but a name was passed (foo).' \
            in str(e)
    else:
        assert False, 'Expected a type error because of an invalid option.'


def test_counting(runner):
    @click.command()
    @click.option('-v', count=True, help='Verbosity',
                  type=click.IntRange(0, 3))
    def cli(v):
        click.echo('verbosity=%d' % v)

    result = runner.invoke(cli, ['-vvv'])
    assert not result.exception
    assert result.output == 'verbosity=3\n'

    result = runner.invoke(cli, ['-vvvv'])
    assert result.exception
    assert 'Invalid value for "-v": 4 is not in the valid range of 0 to 3.' \
        in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == 'verbosity=0\n'

    result = runner.invoke(cli, ['--help'])
    assert re.search('-v\s+Verbosity', result.output) is not None


@pytest.mark.parametrize('unknown_flag', ['--foo', '-f'])
def test_unknown_options(runner, unknown_flag):
    @click.command()
    def cli():
        pass

    result = runner.invoke(cli, [unknown_flag])
    assert result.exception
    assert 'no such option: {0}'.format(unknown_flag) in result.output


def test_multiple_required(runner):
    @click.command()
    @click.option('-m', '--message', multiple=True, required=True)
    def cli(message):
        click.echo('\n'.join(message))

    result = runner.invoke(cli, ['-m', 'foo', '-mbar'])
    assert not result.exception
    assert result.output == 'foo\nbar\n'

    result = runner.invoke(cli, [])
    assert result.exception
    assert 'Error: Missing option "-m" / "--message".' in result.output


def test_nargs_star(runner):
    @click.command()
    @click.option('--option', nargs=-1)
    @click.option('--foo', nargs=-1)
    @click.option('--bar', nargs=-1)
    @click.argument('args', nargs=-1)
    def vary(args, foo, bar, option):
        click.echo('|'.join(args))
        click.echo('|'.join(foo))
        click.echo('|'.join(bar))
        click.echo('|'.join(option))

    result = runner.invoke(vary, ['6', '7', '--foo', '1', '2', '3', '--bar', '4', '5', '--option', '9', '10'])
    assert not result.exception
    assert result.output.splitlines() == [
        '6|7',
        '1|2|3',
        '4|5',
        '9|10'
    ]

    result = runner.invoke(vary, ['--foo', '1', '2', '3', '--bar', '4', '5', '--option', '9', '10', '--', '6', '7'])
    assert not result.exception
    assert result.output.splitlines() == [
        '6|7',
        '1|2|3',
        '4|5',
        '9|10'
    ]


def test_multiple_envvar(runner):
    @click.command()
    @click.option('--arg', multiple=True)
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], auto_envvar_prefix='TEST',
                           env={'TEST_ARG': 'foo bar baz'})
    assert not result.exception
    assert result.output == 'foo|bar|baz\n'

    @click.command()
    @click.option('--arg', multiple=True, envvar='X')
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], env={'X': 'foo bar baz'})
    assert not result.exception
    assert result.output == 'foo|bar|baz\n'

    @click.command()
    @click.option('--arg', multiple=True, type=click.Path())
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], auto_envvar_prefix='TEST',
                           env={'TEST_ARG': 'foo%sbar' % os.path.pathsep})
    assert not result.exception
    assert result.output == 'foo|bar\n'


def test_nargs_envvar(runner):
    @click.command()
    @click.option('--arg', nargs=2)
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], auto_envvar_prefix='TEST',
                           env={'TEST_ARG': 'foo bar'})
    assert not result.exception
    assert result.output == 'foo|bar\n'

    @click.command()
    @click.option('--arg', nargs=2, multiple=True)
    def cmd(arg):
        for item in arg:
            click.echo('|'.join(item))

    result = runner.invoke(cmd, [], auto_envvar_prefix='TEST',
                           env={'TEST_ARG': 'x 1 y 2'})
    assert not result.exception
    assert result.output == 'x|1\ny|2\n'


def test_custom_validation(runner):
    def validate_pos_int(ctx, value):
        if value < 0:
            raise click.BadParameter('Value needs to be positive')
        return value

    @click.command()
    @click.option('--foo', callback=validate_pos_int, default=1)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ['--foo', '-1'])
    assert 'Invalid value for "--foo": Value needs to be positive' \
        in result.output

    result = runner.invoke(cmd, ['--foo', '42'])
    assert result.output == '42\n'


def test_winstyle_options(runner):
    @click.command()
    @click.option('/debug;/no-debug', help='Enables or disables debug mode.')
    def cmd(debug):
        click.echo(debug)

    result = runner.invoke(cmd, ['/debug'], help_option_names=['/?'])
    assert result.output == 'True\n'
    result = runner.invoke(cmd, ['/no-debug'], help_option_names=['/?'])
    assert result.output == 'False\n'
    result = runner.invoke(cmd, [], help_option_names=['/?'])
    assert result.output == 'False\n'
    result = runner.invoke(cmd, ['/?'], help_option_names=['/?'])
    assert '/debug; /no-debug  Enables or disables debug mode.' in result.output
    assert '/?                 Show this message and exit.' in result.output


def test_legacy_options(runner):
    @click.command()
    @click.option('-whatever')
    def cmd(whatever):
        click.echo(whatever)

    result = runner.invoke(cmd, ['-whatever', '42'])
    assert result.output == '42\n'
    result = runner.invoke(cmd, ['-whatever=23'])
    assert result.output == '23\n'


def test_missing_choice(runner):
    @click.command()
    @click.option('--foo', type=click.Choice(['foo', 'bar']),
                  required=True)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd)
    assert result.exit_code == 2
    assert 'Error: Missing option "--foo".  Choose from foo, bar.' \
        in result.output


def test_multiline_help(runner):
    @click.command()
    @click.option('--foo', help="""
        hello

        i am

        multiline
    """)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ['--help'])
    assert result.exit_code == 0
    out = result.output.splitlines()
    assert '  --foo TEXT  hello' in out
    assert '              i am' in out
    assert '              multiline' in out

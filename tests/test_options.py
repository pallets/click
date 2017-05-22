# -*- coding: utf-8 -*-
import re
import os
import click
import pytest

from click._compat import text_type


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


def test_invalid_nargs(runner):
    try:
        @click.command()
        @click.option('--foo', nargs=-1)
        def cli(foo):
            pass
    except TypeError as e:
        assert 'Options cannot have nargs < 0' in str(e)
    else:
        assert False, 'Expected a type error because of an invalid option.'


def test_nargs_tup_composite_mult(runner):
    @click.command()
    @click.option('--item', type=(str, int), multiple=True)
    def copy(item):
        for item in item:
            click.echo('name=%s id=%d' % item)

    result = runner.invoke(copy, ['--item', 'peter', '1', '--item', 'max', '2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'name=peter id=1',
        'name=max id=2',
    ]


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


def test_multiple_default_help(runner):
    @click.command()
    @click.option('--arg1', multiple=True, default=('foo', 'bar'),
                  show_default=True)
    @click.option('--arg2', multiple=True, default=(1, 2), type=int,
                  show_default=True)
    def cmd(arg, arg2):
        pass

    result = runner.invoke(cmd, ['--help'])
    assert not result.exception
    assert 'foo, bar' in result.output
    assert '1, 2' in result.output


def test_multiple_default_type(runner):
    @click.command()
    @click.option('--arg1', multiple=True, default=('foo', 'bar'))
    @click.option('--arg2', multiple=True, default=(1, 'a'))
    def cmd(arg1, arg2):
        assert all(isinstance(e[0], text_type) for e in arg1)
        assert all(isinstance(e[1], text_type) for e in arg1)

        assert all(isinstance(e[0], int) for e in arg2)
        assert all(isinstance(e[1], text_type) for e in arg2)

    result = runner.invoke(cmd, '--arg1 a b --arg1 test 1 --arg2 2 '
                           'two --arg2 4 four'.split())
    assert not result.exception


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


def test_argument_custom_class(runner):
    class CustomArgument(click.Argument):
        def get_default(self, ctx):
            '''a dumb override of a default value for testing'''
            return 'I am a default'

    @click.command()
    @click.argument('testarg', cls=CustomArgument, default='you wont see me')
    def cmd(testarg):
        click.echo(testarg)

    result = runner.invoke(cmd)
    assert 'I am a default' in result.output
    assert 'you wont see me' not in result.output


def test_option_custom_class(runner):
    class CustomOption(click.Option):
        def get_help_record(self, ctx):
            '''a dumb override of a help text for testing'''
            return ('--help', 'I am a help text')

    @click.command()
    @click.option('--testoption', cls=CustomOption, help='you wont see me')
    def cmd(testoption):
        click.echo(testoption)

    result = runner.invoke(cmd, ['--help'])
    assert 'I am a help text' in result.output
    assert 'you wont see me' not in result.output


def test_aliases_for_flags(runner):
    @click.command()
    @click.option('--warnings/--no-warnings', ' /-W', default=True)
    def cli(warnings):
        click.echo(warnings)

    result = runner.invoke(cli, ['--warnings'])
    assert result.output == 'True\n'
    result = runner.invoke(cli, ['--no-warnings'])
    assert result.output == 'False\n'
    result = runner.invoke(cli, ['-W'])
    assert result.output == 'False\n'

    @click.command()
    @click.option('--warnings/--no-warnings', '-w', default=True)
    def cli_alt(warnings):
        click.echo(warnings)

    result = runner.invoke(cli_alt, ['--warnings'])
    assert result.output == 'True\n'
    result = runner.invoke(cli_alt, ['--no-warnings'])
    assert result.output == 'False\n'
    result = runner.invoke(cli_alt, ['-w'])
    assert result.output == 'True\n'

@pytest.mark.parametrize('option_args,expected', [
    (['--aggressive', '--all', '-a'], 'aggressive'),
    (['--first', '--second', '--third', '-a', '-b', '-c'], 'first'),
    (['--apple', '--banana', '--cantaloupe', '-a', '-b', '-c'], 'apple'),
    (['--cantaloupe', '--banana', '--apple', '-c', '-b', '-a'], 'cantaloupe'),
    (['-a', '-b', '-c'], 'a'),
    (['-c', '-b', '-a'], 'c'),
    (['-a', '--apple', '-b', '--banana', '-c', '--cantaloupe'], 'apple'),
    (['-c', '-a', '--cantaloupe', '-b', '--banana', '--apple'], 'cantaloupe'),
    (['--from', '-f', '_from'], '_from'),
    (['--return', '-r', '_ret'], '_ret'),
])
def test_option_names(runner, option_args, expected):

    @click.command()
    @click.option(*option_args, is_flag=True)
    def cmd(**kwargs):
        click.echo(str(kwargs[expected]))

    assert cmd.params[0].name == expected

    for form in option_args:
        if form.startswith('-'):
            result = runner.invoke(cmd, [form])
            assert result.output == 'True\n'

import sys
import click
import pytest


def debug():
    click.echo('%s=%s' % (
        sys._getframe(1).f_code.co_name,
        '|'.join(click.get_current_context().args),
    ))


def test_basic_chaining(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    def sdist():
        click.echo('sdist called')

    @cli.command('bdist')
    def bdist():
        click.echo('bdist called')

    result = runner.invoke(cli, ['bdist', 'sdist', 'bdist'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called',
        'sdist called',
        'bdist called',
    ]


def test_chaining_help(runner):
    @click.group(chain=True)
    def cli():
        """ROOT HELP"""
        pass

    @cli.command('sdist')
    def sdist():
        """SDIST HELP"""
        click.echo('sdist called')

    @cli.command('bdist')
    def bdist():
        """BDIST HELP"""
        click.echo('bdist called')

    result = runner.invoke(cli, ['--help'])
    assert not result.exception
    assert 'COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...' in result.output
    assert 'ROOT HELP' in result.output

    result = runner.invoke(cli, ['sdist', '--help'])
    assert not result.exception
    assert 'SDIST HELP' in result.output

    result = runner.invoke(cli, ['bdist', '--help'])
    assert not result.exception
    assert 'BDIST HELP' in result.output

    result = runner.invoke(cli, ['bdist', 'sdist', '--help'])
    assert not result.exception
    assert 'SDIST HELP' in result.output


def test_chaining_with_options(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    @click.option('--format')
    def sdist(format):
        click.echo('sdist called %s' % format)

    @cli.command('bdist')
    @click.option('--format')
    def bdist(format):
        click.echo('bdist called %s' % format)

    result = runner.invoke(cli, ['bdist', '--format=1', 'sdist', '--format=2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called 1',
        'sdist called 2',
    ]


def test_chaining_with_arguments(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    @click.argument('format')
    def sdist(format):
        click.echo('sdist called %s' % format)

    @cli.command('bdist')
    @click.argument('format')
    def bdist(format):
        click.echo('bdist called %s' % format)

    result = runner.invoke(cli, ['bdist', '1', 'sdist', '2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called 1',
        'sdist called 2',
    ]


def test_pipeline(runner):
    @click.group(chain=True, invoke_without_command=True)
    @click.option('-i', '--input', type=click.File('r'))
    def cli(input):
        pass

    @cli.resultcallback()
    def process_pipeline(processors, input):
        iterator = (x.rstrip('\r\n') for x in input)
        for processor in processors:
            iterator = processor(iterator)
        for item in iterator:
            click.echo(item)

    @cli.command('uppercase')
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()
        return processor

    @cli.command('strip')
    def make_strip():
        def processor(iterator):
            for line in iterator:
                yield line.strip()
        return processor

    result = runner.invoke(cli, ['-i', '-'], input='foo\nbar')
    assert not result.exception
    assert result.output.splitlines() == [
        'foo',
        'bar',
    ]

    result = runner.invoke(cli, ['-i', '-', 'strip'], input='foo \n bar')
    assert not result.exception
    assert result.output.splitlines() == [
        'foo',
        'bar',
    ]

    result = runner.invoke(cli, ['-i', '-', 'strip', 'uppercase'],
                           input='foo \n bar')
    assert not result.exception
    assert result.output.splitlines() == [
        'FOO',
        'BAR',
    ]


def test_args_and_chain(runner):
    @click.group(chain=True)
    def cli():
        debug()

    @cli.command()
    def a():
        debug()

    @cli.command()
    def b():
        debug()

    @cli.command()
    def c():
        debug()

    result = runner.invoke(cli, ['a', 'b', 'c'])
    assert not result.exception
    assert result.output.splitlines() == [
        'cli=',
        'a=',
        'b=',
        'c=',
    ]


def test_multicommand_arg_behavior(runner):
    with pytest.raises(RuntimeError):
        @click.group(chain=True)
        @click.argument('forbidden', required=False)
        def bad_cli():
            pass

    with pytest.raises(RuntimeError):
        @click.group(chain=True)
        @click.argument('forbidden', nargs=-1)
        def bad_cli2():
            pass

    @click.group(chain=True)
    @click.argument('arg')
    def cli(arg):
        click.echo('cli:%s' % arg)

    @cli.command()
    def a():
        click.echo('a')

    result = runner.invoke(cli, ['foo', 'a'])
    assert not result.exception
    assert result.output.splitlines() == [
        'cli:foo',
        'a',
    ]


def test_multicommand_chaining(runner):
    @click.group(chain=True)
    def cli():
        debug()

    @cli.group()
    def l1a():
        debug()

    @l1a.command()
    def l2a():
        debug()

    @l1a.command()
    def l2b():
        debug()

    @cli.command()
    def l1b():
        debug()

    result = runner.invoke(cli, ['l1a', 'l2a', 'l1b'])
    assert not result.exception
    assert result.output.splitlines() == [
        'cli=',
        'l1a=',
        'l2a=',
        'l1b=',
    ]

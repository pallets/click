# -*- coding: utf-8 -*-
import click


def test_basic_functionality(runner):
    @click.command()
    def cli():
        """Hello World!"""
        click.echo('I EXECUTED')

    result = runner.invoke(cli, ['--help'])
    assert not result.exception
    assert 'Hello World!' in result.output
    assert 'Show this message and exit.' in result.output
    assert result.exit_code == 0
    assert 'I EXECUTED' not in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert 'I EXECUTED' in result.output
    assert result.exit_code == 0


def test_basic_group(runner):
    @click.group()
    def cli():
        """This is the root."""
        click.echo('ROOT EXECUTED')

    @cli.command()
    def subcommand():
        """This is a subcommand."""
        click.echo('SUBCOMMAND EXECUTED')

    result = runner.invoke(cli, ['--help'])
    assert not result.exception
    assert 'This is the root' in result.output
    assert 'This is a subcommand.' in result.output
    assert result.exit_code == 0
    assert 'ROOT EXECUTED' not in result.output

    result = runner.invoke(cli, ['subcommand'])
    assert not result.exception
    assert result.exit_code == 0
    assert 'ROOT EXECUTED' in result.output
    assert 'SUBCOMMAND EXECUTED' in result.output


def test_basic_option(runner):
    @click.command()
    @click.option('--foo', default='no value')
    def cli(foo):
        click.echo('FOO:[%s]' % foo)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert 'FOO:[no value]' in result.output

    result = runner.invoke(cli, ['--foo=42'])
    assert not result.exception
    assert 'FOO:[42]' in result.output

    result = runner.invoke(cli, ['--foo'])
    assert result.exception
    assert '--foo option requires an argument' in result.output

    result = runner.invoke(cli, ['--foo='])
    assert not result.exception
    assert 'FOO:[]' in result.output

    result = runner.invoke(cli, [u'--foo=\N{SNOWMAN}'])
    assert not result.exception
    assert u'FOO:[\N{SNOWMAN}]' in result.output


def test_int_option(runner):
    @click.command()
    @click.option('--foo', default=42)
    def cli(foo):
        click.echo('FOO:[%s]' % (foo * 2))

    result = runner.invoke(cli, [])
    assert not result.exception
    assert 'FOO:[84]' in result.output

    result = runner.invoke(cli, ['--foo=23'])
    assert not result.exception
    assert 'FOO:[46]' in result.output

    result = runner.invoke(cli, ['--foo=bar'])
    assert result.exception
    assert 'Invalid value for "--foo": bar is not a valid integer' \
        in result.output


def test_float_option(runner):
    @click.command()
    @click.option('--foo', default=42, type=click.FLOAT)
    def cli(foo):
        assert type(foo) is float
        click.echo('FOO:[%s]' % foo)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert 'FOO:[42.0]' in result.output

    result = runner.invoke(cli, ['--foo=23.5'])
    assert not result.exception
    assert 'FOO:[23.5]' in result.output

    result = runner.invoke(cli, ['--foo=bar'])
    assert result.exception
    assert 'Invalid value for "--foo": bar is not a valid float' \
        in result.output


def test_boolean_option(runner):
    for default in True, False:
        @click.command()
        @click.option('--with-foo/--without-foo', default=default)
        def cli(with_foo):
            click.echo(with_foo)

        result = runner.invoke(cli, ['--with-foo'])
        assert not result.exception
        assert result.output == 'True\n'
        result = runner.invoke(cli, ['--without-foo'])
        assert not result.exception
        assert result.output == 'False\n'
        result = runner.invoke(cli, [])
        assert not result.exception
        assert result.output == '%s\n' % default

    for default in True, False:
        @click.command()
        @click.option('--flag', is_flag=True, default=default)
        def cli(flag):
            click.echo(flag)

        result = runner.invoke(cli, ['--flag'])
        assert not result.exception
        assert result.output == '%s\n' % (not default)
        result = runner.invoke(cli, [])
        assert not result.exception
        assert result.output == '%s\n' % (default)


def test_file_option(runner):
    @click.command()
    @click.option('--file', type=click.File('w'))
    def input(file):
        file.write('Hello World!\n')

    @click.command()
    @click.option('--file', type=click.File('r'))
    def output(file):
        click.echo(file.read())

    with runner.isolated_filesystem():
        result_in = runner.invoke(input, ['--file=example.txt'])
        result_out = runner.invoke(output, ['--file=example.txt'])

    assert not result_in.exception
    assert result_in.output == ''
    assert not result_out.exception
    assert result_out.output == 'Hello World!\n\n'

def test_eager_required_option_allows_help(runner):
    def get_from_source(ctx,value):
        return value or ctx.params['source']

    @click.command()
    @click.option('--source',
        required=True,
        is_eager=True,
        help='source file')
    @click.option('--dest',
        callback=get_from_source,
        help='destination file. If not supplied, operates in place.')
    def cli(source,dest):
        print 'source:',source
        print 'dest:',dest

    result = runner.invoke(cli,['--help'])
    assert not result.exception

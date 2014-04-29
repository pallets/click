# -*- coding: utf-8 -*-
import click


def test_basic_functionality(runner):
    @click.command()
    def cli():
        """Hello World!"""
        click.echo('I EXECUTED')

    result = runner.invoke(cli, ['--help'])
    assert result.okay
    assert 'Hello World!' in result.output
    assert 'Show this message and exit.' in result.output
    assert result.exit_code == 0
    assert 'I EXECUTED' not in result.output

    result = runner.invoke(cli, [])
    assert result.okay
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
    assert result.okay
    assert 'This is the root' in result.output
    assert 'This is a subcommand.' in result.output
    assert result.exit_code == 0
    assert 'ROOT EXECUTED' not in result.output

    result = runner.invoke(cli, ['subcommand'])
    assert result.okay
    assert result.exit_code == 0
    assert 'ROOT EXECUTED' in result.output
    assert 'SUBCOMMAND EXECUTED' in result.output


def test_basic_option(runner):
    @click.command()
    @click.option('--foo', default='no value')
    def cli(foo):
        click.echo('FOO:[%s]' % foo)

    result = runner.invoke(cli, [])
    assert result.okay
    assert 'FOO:[no value]' in result.output

    result = runner.invoke(cli, ['--foo=42'])
    assert result.okay
    assert 'FOO:[42]' in result.output

    result = runner.invoke(cli, ['--foo'])
    assert not result.okay
    assert '--foo option requires an argument' in result.output

    result = runner.invoke(cli, ['--foo='])
    assert result.okay
    assert 'FOO:[]' in result.output

    result = runner.invoke(cli, [u'--foo=\N{SNOWMAN}'])
    assert result.okay
    assert u'FOO:[\N{SNOWMAN}]' in result.output

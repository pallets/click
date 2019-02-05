# -*- coding: utf-8 -*-
import re

import click
import pytest


def test_other_command_invoke(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd, arg=42)

    @click.command()
    @click.argument('arg', type=click.INT)
    def other_cmd(arg):
        click.echo(arg)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == '42\n'


def test_other_command_forward(runner):
    cli = click.Group()

    @cli.command()
    @click.option('--count', default=1)
    def test(count):
        click.echo('Count: %d' % count)

    @cli.command()
    @click.option('--count', default=1)
    @click.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

    result = runner.invoke(cli, ['dist'])
    assert not result.exception
    assert result.output == 'Count: 1\nCount: 42\n'


def test_auto_shorthelp(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def short():
        """This is a short text."""

    @cli.command()
    def special_chars():
        """Login and store the token in ~/.netrc."""

    @cli.command()
    def long():
        """This is a long text that is too long to show as short help
        and will be truncated instead."""

    result = runner.invoke(cli, ['--help'])
    assert re.search(
        r'Commands:\n\s+'
        r'long\s+This is a long text that is too long to show as short help\.\.\.\n\s+'
        r'short\s+This is a short text\.\n\s+'
        r'special-chars\s+Login and store the token in ~/.netrc\.\s*',
        result.output) is not None


def test_default_maps(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--name', default='normal')
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ['foo'], default_map={
        'foo': {'name': 'changed'}
    })

    assert not result.exception
    assert result.output == 'changed\n'


def test_group_with_args(runner):
    @click.group()
    @click.argument('obj')
    def cli(obj):
        click.echo('obj=%s' % obj)

    @cli.command()
    def move():
        click.echo('move')

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Show this message and exit.' in result.output

    result = runner.invoke(cli, ['obj1'])
    assert result.exit_code == 2
    assert 'Error: Missing command.' in result.output

    result = runner.invoke(cli, ['obj1', '--help'])
    assert result.exit_code == 0
    assert 'Show this message and exit.' in result.output

    result = runner.invoke(cli, ['obj1', 'move'])
    assert result.exit_code == 0
    assert result.output == 'obj=obj1\nmove\n'


def test_base_command(runner):
    import optparse

    @click.group()
    def cli():
        pass

    class OptParseCommand(click.BaseCommand):

        def __init__(self, name, parser, callback):
            click.BaseCommand.__init__(self, name)
            self.parser = parser
            self.callback = callback

        def parse_args(self, ctx, args):
            try:
                opts, args = parser.parse_args(args)
            except Exception as e:
                ctx.fail(str(e))
            ctx.args = args
            ctx.params = vars(opts)

        def get_usage(self, ctx):
            return self.parser.get_usage()

        def get_help(self, ctx):
            return self.parser.format_help()

        def invoke(self, ctx):
            ctx.invoke(self.callback, ctx.args, **ctx.params)

    parser = optparse.OptionParser(usage='Usage: foo test [OPTIONS]')
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    def test_callback(args, filename, verbose):
        click.echo(' '.join(args))
        click.echo(filename)
        click.echo(verbose)
    cli.add_command(OptParseCommand('test', parser, test_callback))

    result = runner.invoke(cli, ['test', '-f', 'test.txt', '-q',
                                 'whatever.txt', 'whateverelse.txt'])
    assert not result.exception
    assert result.output.splitlines() == [
        'whatever.txt whateverelse.txt',
        'test.txt',
        'False',
    ]

    result = runner.invoke(cli, ['test', '--help'])
    assert not result.exception
    assert result.output.splitlines() == [
        'Usage: foo test [OPTIONS]',
        '',
        'Options:',
        '  -h, --help            show this help message and exit',
        '  -f FILE, --file=FILE  write report to FILE',
        '  -q, --quiet           don\'t print status messages to stdout',
    ]


def test_object_propagation(runner):
    for chain in False, True:
        @click.group(chain=chain)
        @click.option('--debug/--no-debug', default=False)
        @click.pass_context
        def cli(ctx, debug):
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj['DEBUG'] = debug

        @cli.command()
        @click.pass_context
        def sync(ctx):
            click.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))

        result = runner.invoke(cli, ['sync'])
        assert result.exception is None
        assert result.output == 'Debug is off\n'


def test_other_command_invoke_with_defaults(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd)

    @click.command()
    @click.option('--foo', type=click.INT, default=42)
    @click.pass_context
    def other_cmd(ctx, foo):
        assert ctx.info_name == 'other-cmd'
        click.echo(foo)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == '42\n'


def test_invoked_subcommand(runner):
    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo('no subcommand, use default')
            ctx.invoke(sync)
        else:
            click.echo('invoke subcommand')

    @cli.command()
    def sync():
        click.echo('in subcommand')

    result = runner.invoke(cli, ['sync'])
    assert not result.exception
    assert result.output == 'invoke subcommand\nin subcommand\n'

    result = runner.invoke(cli)
    assert not result.exception
    assert result.output == 'no subcommand, use default\nin subcommand\n'


def test_unprocessed_options(runner):
    @click.command(context_settings=dict(
        ignore_unknown_options=True
    ))
    @click.argument('args', nargs=-1, type=click.UNPROCESSED)
    @click.option('--verbose', '-v', count=True)
    def cli(verbose, args):
        click.echo('Verbosity: %s' % verbose)
        click.echo('Args: %s' % '|'.join(args))

    result = runner.invoke(cli, ['-foo', '-vvvvx', '--muhaha', 'x', 'y', '-x'])
    assert not result.exception
    assert result.output.splitlines() == [
        'Verbosity: 4',
        'Args: -foo|-x|--muhaha|x|y|-x',
    ]


def test_deferred_options(runner):
    loose_ordering = dict(
        allow_interspersed_args=True,
        defer_unknown_options=True,
    )

    @click.group(context_settings=loose_ordering)
    @click.option('--aa', '-a', count=True)
    def cli(aa):
        click.echo(f'cli a: {aa}')

    @cli.group(context_settings=loose_ordering)
    @click.option('--bb', '-b', count=True)
    @click.option('--cc', '-c', count=True)
    def cmd(bb, cc):
        click.echo(f'cmd b: {bb}')
        click.echo(f'cmd c: {cc}')

    @cmd.command()
    @click.option('--cc', '-c', count=True)
    @click.option('--dd', '-d', count=True)
    def subcmd(cc, dd):
        click.echo(f'subcmd c: {cc}')
        click.echo(f'subcmd d: {dd}')

    result = runner.invoke(cli, ['-abcd', 'cmd', '-abcd', 'subcmd', '-abcd'])
    assert not result.exception, result.output
    assert result.output.splitlines() == [
        'cli a: 3',
        'cmd b: 3',
        'cmd c: 2',
        'subcmd c: 1',
        'subcmd d: 3',
    ]

    result = runner.invoke(cli, ['--aa', '--bb', '--cc', '--dd',
                                 'cmd', '--aa', '--bb', '--cc', '--dd',
                                 'subcmd', '--aa', '--bb', '--cc', '--dd'])
    assert not result.exception, result.output
    assert result.output.splitlines() == [
        'cli a: 3',
        'cmd b: 3',
        'cmd c: 2',
        'subcmd c: 1',
        'subcmd d: 3',
    ]


def test_deprecated_in_help_messages(runner):
    @click.command(deprecated=True)
    def cmd_with_help():
        """CLI HELP"""
        pass

    result = runner.invoke(cmd_with_help, ['--help'])
    assert '(DEPRECATED)' in result.output

    @click.command(deprecated=True)
    def cmd_without_help():
        pass

    result = runner.invoke(cmd_without_help, ['--help'])
    assert '(DEPRECATED)' in result.output


def test_deprecated_in_invocation(runner):
    @click.command(deprecated=True)
    def deprecated_cmd():
        debug()

    result = runner.invoke(deprecated_cmd)
    assert 'DeprecationWarning:' in result.output

# -*- coding: utf-8 -*-
import re
import click


def test_other_command_invoke(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd, 42)

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
        r'long\s+This is a long text that is too long to show\.\.\.\n\s+'
        r'short\s+This is a short text\.\n\s+'
        r'special_chars\s+Login and store the token in ~/.netrc\.\s*',
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

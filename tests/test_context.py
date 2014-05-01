# -*- coding: utf-8 -*-
import click


def test_ensure_context_objects(runner):
    class Foo(object):
        def __init__(self):
            self.title = 'default'

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @pass_foo
    def cli(foo):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ['test'])
    assert not result.exception
    assert result.output == 'default\n'


def test_get_context_objects(runner):
    class Foo(object):
        def __init__(self):
            self.title = 'default'

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = 'test'

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ['test'])
    assert not result.exception
    assert result.output == 'test\n'


def test_get_context_objects_no_ensuring(runner):
    class Foo(object):
        def __init__(self):
            self.title = 'default'

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = 'test'

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ['test'])
    assert not result.exception
    assert result.output == 'test\n'


def test_get_context_objects_missing(runner):
    class Foo(object):
        pass

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ['test'])
    assert result.exception is not None
    assert isinstance(result.exception, RuntimeError)
    assert "Managed to invoke callback without a context object " \
        "of type 'Foo' existing" in str(result.exception)

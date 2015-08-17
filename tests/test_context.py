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


def test_multi_enter(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        def callback():
            called.append(True)
        ctx.call_on_close(callback)

        with ctx:
            pass
        assert not called

    result = runner.invoke(cli, [])
    assert result.exception is None
    assert called == [True]


def test_global_context_object(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        assert click.get_current_context() is ctx
        ctx.obj = 'FOOBAR'
        assert click.get_current_context().obj == 'FOOBAR'

    assert click.get_current_context(silent=True) is None
    runner.invoke(cli, [], catch_exceptions=False)
    assert click.get_current_context(silent=True) is None


def test_context_meta(runner):
    LANG_KEY = __name__ + '.lang'

    def set_language(value):
        click.get_current_context().meta[LANG_KEY] = value

    def get_language():
        return click.get_current_context().meta.get(LANG_KEY, 'en_US')

    @click.command()
    @click.pass_context
    def cli(ctx):
        assert get_language() == 'en_US'
        set_language('de_DE')
        assert get_language() == 'de_DE'

    runner.invoke(cli, [], catch_exceptions=False)


def test_context_pushing():
    rv = []

    @click.command()
    def cli():
        pass

    ctx = click.Context(cli)

    @ctx.call_on_close
    def test_callback():
        rv.append(42)

    with ctx.scope(cleanup=False):
        # Internal
        assert ctx._depth == 2

    assert rv == []

    with ctx.scope():
        # Internal
        assert ctx._depth == 1

    assert rv == [42]


def test_pass_obj(runner):
    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = 'test'

    @cli.command()
    @click.pass_obj
    def test(obj):
        click.echo(obj)

    result = runner.invoke(cli, ['test'])
    assert not result.exception
    assert result.output == 'test\n'

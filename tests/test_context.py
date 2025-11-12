import logging
from contextlib import AbstractContextManager
from contextlib import contextmanager
from types import TracebackType

import pytest

import click
from click import Context
from click import Option
from click import Parameter
from click.core import ParameterSource
from click.decorators import help_option
from click.decorators import pass_meta_key


def test_ensure_context_objects(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @pass_foo
    def cli(foo):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "default\n"


def test_get_context_objects(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_no_ensuring(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_missing(runner):
    class Foo:
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

    result = runner.invoke(cli, ["test"])
    assert result.exception is not None
    assert isinstance(result.exception, RuntimeError)
    assert (
        "Managed to invoke callback without a context object of type"
        " 'Foo' existing" in str(result.exception)
    )


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
        ctx.obj = "FOOBAR"
        assert click.get_current_context().obj == "FOOBAR"

    assert click.get_current_context(silent=True) is None
    runner.invoke(cli, [], catch_exceptions=False)
    assert click.get_current_context(silent=True) is None


def test_context_meta(runner):
    LANG_KEY = f"{__name__}.lang"

    def set_language(value):
        click.get_current_context().meta[LANG_KEY] = value

    def get_language():
        return click.get_current_context().meta.get(LANG_KEY, "en_US")

    @click.command()
    @click.pass_context
    def cli(ctx):
        assert get_language() == "en_US"
        set_language("de_DE")
        assert get_language() == "de_DE"

    runner.invoke(cli, [], catch_exceptions=False)


def test_make_pass_meta_decorator(runner):
    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.meta["value"] = "good"

    @cli.command()
    @pass_meta_key("value")
    def show(value):
        return value

    result = runner.invoke(cli, ["show"], standalone_mode=False)
    assert result.return_value == "good"


def test_make_pass_meta_decorator_doc():
    pass_value = pass_meta_key("value")
    assert "the 'value' key from :attr:`click.Context.meta`" in pass_value.__doc__
    pass_value = pass_meta_key("value", doc_description="the test value")
    assert "passes the test value" in pass_value.__doc__


def test_hiding_of_unset_sentinel_in_callbacks():
    """Fix: https://github.com/pallets/click/issues/3136"""

    def inspect_other_params(ctx, param, value):
        """A callback that inspects other parameters' values via the context."""
        assert click.get_current_context() is ctx
        click.echo(f"callback.my_arg: {ctx.params.get('my_arg')!r}")
        click.echo(f"callback.my_opt: {ctx.params.get('my_opt')!r}")
        click.echo(f"callback.my_callback: {ctx.params.get('my_callback')!r}")

        click.echo(f"callback.param: {param!r}")
        click.echo(f"callback.value: {value!r}")

        return "hard-coded"

    class ParameterInternalCheck(Option):
        """An option that checks internal state during processing."""

        def process_value(self, ctx, value):
            """Check that UNSET values are hidden as None in ctx.params within the
            callback, and then properly restored afterwards.
            """
            assert click.get_current_context() is ctx
            click.echo(f"before_process.my_arg: {ctx.params.get('my_arg')!r}")
            click.echo(f"before_process.my_opt: {ctx.params.get('my_opt')!r}")
            click.echo(f"before_process.my_callback: {ctx.params.get('my_callback')!r}")

            value = super().process_value(ctx, value)

            assert click.get_current_context() is ctx
            click.echo(f"after_process.my_arg: {ctx.params.get('my_arg')!r}")
            click.echo(f"after_process.my_opt: {ctx.params.get('my_opt')!r}")
            click.echo(f"after_process.my_callback: {ctx.params.get('my_callback')!r}")

            return value

    def change_other_params(ctx, param, value):
        """A callback that modifies other parameters' values via the context."""
        assert click.get_current_context() is ctx
        click.echo(f"before_change.my_arg: {ctx.params.get('my_arg')!r}")
        click.echo(f"before_change.my_opt: {ctx.params.get('my_opt')!r}")
        click.echo(f"before_change.my_callback: {ctx.params.get('my_callback')!r}")

        click.echo(f"before_change.param: {param!r}")
        click.echo(f"before_change.value: {value!r}")

        ctx.params["my_arg"] = "changed"
        # Reset to None parameters that where not UNSET to see they are not forced back
        # to UNSET.
        ctx.params["my_callback"] = None

        return value

    @click.command
    @click.argument("my-arg", required=False)
    @click.option("--my-opt")
    @click.option("--my-callback", callback=inspect_other_params)
    @click.option("--check-internal", cls=ParameterInternalCheck)
    @click.option(
        "--modifying-callback", cls=ParameterInternalCheck, callback=change_other_params
    )
    @click.pass_context
    def cli(ctx, my_arg, my_opt, my_callback, check_internal, modifying_callback):
        click.echo(f"cli.my_arg: {my_arg!r}")
        click.echo(f"cli.my_opt: {my_opt!r}")
        click.echo(f"cli.my_callback: {my_callback!r}")
        click.echo(f"cli.check_internal: {check_internal!r}")
        click.echo(f"cli.modifying_callback: {modifying_callback!r}")

    runner = click.testing.CliRunner()
    result = runner.invoke(cli)

    assert result.stdout.splitlines() == [
        # Values of other parameters within the callback are None, not UNSET.
        "callback.my_arg: None",
        "callback.my_opt: None",
        "callback.my_callback: None",
        "callback.param: <Option my_callback>",
        "callback.value: None",
        # Previous UNSET values were not altered by the callback.
        "before_process.my_arg: Sentinel.UNSET",
        "before_process.my_opt: Sentinel.UNSET",
        "before_process.my_callback: 'hard-coded'",
        "after_process.my_arg: Sentinel.UNSET",
        "after_process.my_opt: Sentinel.UNSET",
        "after_process.my_callback: 'hard-coded'",
        # Changes on other parameters within the callback are restored afterwards.
        "before_process.my_arg: Sentinel.UNSET",
        "before_process.my_opt: Sentinel.UNSET",
        "before_process.my_callback: 'hard-coded'",
        "before_change.my_arg: None",
        "before_change.my_opt: None",
        "before_change.my_callback: 'hard-coded'",
        "before_change.param: <ParameterInternalCheck modifying_callback>",
        "before_change.value: None",
        "after_process.my_arg: 'changed'",
        "after_process.my_opt: Sentinel.UNSET",
        "after_process.my_callback: None",
        # Unset values within the main command are UNSET, but hidden as None.
        "cli.my_arg: 'changed'",
        "cli.my_opt: None",
        "cli.my_callback: None",
        "cli.check_internal: None",
        "cli.modifying_callback: None",
    ]
    assert not result.stderr
    assert not result.exception
    assert result.exit_code == 0


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
        ctx.obj = "test"

    @cli.command()
    @click.pass_obj
    def test(obj):
        click.echo(obj)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_close_before_pop(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.obj = "test"

        @ctx.call_on_close
        def foo():
            assert click.get_current_context().obj == "test"
            called.append(True)

        click.echo("aha!")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "aha!\n"
    assert called == [True]


def test_close_before_exit(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.obj = "test"

        @ctx.call_on_close
        def foo():
            assert click.get_current_context().obj == "test"
            called.append(True)

        ctx.exit()

        click.echo("aha!")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert not result.output
    assert called == [True]


@pytest.mark.parametrize(
    ("cli_args", "expect"),
    [
        pytest.param(
            ("--option-with-callback", "--force-exit"),
            ["ExitingOption", "NonExitingOption"],
            id="natural_order",
        ),
        pytest.param(
            ("--force-exit", "--option-with-callback"),
            ["ExitingOption"],
            id="eagerness_precedence",
        ),
    ],
)
def test_multiple_eager_callbacks(runner, cli_args, expect):
    """Checks all callbacks are called on exit, even the nasty ones hidden within
    callbacks.

    Also checks the order in which they're called.
    """
    # Keeps track of callback calls.
    called = []

    class NonExitingOption(Option):
        def reset_state(self):
            called.append(self.__class__.__name__)

        def set_state(self, ctx: Context, param: Parameter, value: str) -> str:
            ctx.call_on_close(self.reset_state)
            return value

        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("expose_value", False)
            kwargs.setdefault("callback", self.set_state)
            super().__init__(*args, **kwargs)

    class ExitingOption(NonExitingOption):
        def set_state(self, ctx: Context, param: Parameter, value: str) -> str:
            value = super().set_state(ctx, param, value)
            ctx.exit()
            return value

    @click.command()
    @click.option("--option-with-callback", is_eager=True, cls=NonExitingOption)
    @click.option("--force-exit", is_eager=True, cls=ExitingOption)
    def cli():
        click.echo("This will never be printed as we forced exit via --force-exit")

    result = runner.invoke(cli, cli_args)
    assert not result.exception
    assert not result.output

    assert called == expect


def test_no_state_leaks(runner):
    """Demonstrate state leaks with a specific case of the generic test above.

    Use a logger as a real-world example of a common fixture which, due to its global
    nature, can leak state if not clean-up properly in a callback.
    """
    # Keeps track of callback calls.
    called = []

    class DebugLoggerOption(Option):
        """A custom option to set the name of the debug logger."""

        logger_name: str
        """The ID of the logger to use."""

        def reset_loggers(self):
            """Forces logger managed by the option to be reset to the default level."""
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(logging.NOTSET)

            # Logger has been properly reset to its initial state.
            assert logger.level == logging.NOTSET
            assert logger.getEffectiveLevel() == logging.WARNING

            called.append(True)

        def set_level(self, ctx: Context, param: Parameter, value: str) -> None:
            """Set the logger to DEBUG level."""
            # Keep the logger name around so we can reset it later when winding down
            # the option.
            self.logger_name = value

            # Get the global logger object.
            logger = logging.getLogger(self.logger_name)

            # Check pre-conditions: new logger is not set, but inherits its level from
            # default <root> logger. That's the exact same state we are expecting our
            # logger to be in after being messed with by the CLI.
            assert logger.level == logging.NOTSET
            assert logger.getEffectiveLevel() == logging.WARNING

            logger.setLevel(logging.DEBUG)
            ctx.call_on_close(self.reset_loggers)
            return value

        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("callback", self.set_level)
            super().__init__(*args, **kwargs)

    @click.command()
    @click.option("--debug-logger-name", is_eager=True, cls=DebugLoggerOption)
    @help_option()
    @click.pass_context
    def messing_with_logger(ctx, debug_logger_name):
        # Introspect context to make sure logger name are aligned.
        assert debug_logger_name == ctx.command.params[0].logger_name

        logger = logging.getLogger(debug_logger_name)

        # Logger's level has been properly set to DEBUG by DebugLoggerOption.
        assert logger.level == logging.DEBUG
        assert logger.getEffectiveLevel() == logging.DEBUG

        logger.debug("Blah blah blah")

        ctx.exit()

        click.echo("This will never be printed as we exited early")

    # Call the CLI to mess with the custom logger.
    result = runner.invoke(
        messing_with_logger, ["--debug-logger-name", "my_logger", "--help"]
    )

    assert called == [True]

    # Check the custom logger has been reverted to it initial state by the option
    # callback after being messed with by the CLI.
    logger = logging.getLogger("my_logger")
    assert logger.level == logging.NOTSET
    assert logger.getEffectiveLevel() == logging.WARNING

    assert not result.exception
    assert result.output.startswith("Usage: messing-with-logger [OPTIONS]")


def test_with_resource():
    @contextmanager
    def manager():
        val = [1]
        yield val
        val[0] = 0

    ctx = click.Context(click.Command("test"))

    with ctx.scope():
        rv = ctx.with_resource(manager())
        assert rv[0] == 1

    assert rv == [0]


def test_with_resource_exception() -> None:
    class TestContext(AbstractContextManager[list[int]]):
        _handle_exception: bool
        _base_val: int
        val: list[int]

        def __init__(self, base_val: int = 1, *, handle_exception: bool = True) -> None:
            self._handle_exception = handle_exception
            self._base_val = base_val

        def __enter__(self) -> list[int]:
            self.val = [self._base_val]
            return self.val

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None:
            if not exc_type:
                self.val[0] = self._base_val - 1
                return None

            self.val[0] = self._base_val + 1
            return self._handle_exception

    class TestException(Exception):
        pass

    ctx = click.Context(click.Command("test"))

    base_val = 1

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        assert rv[0] == base_val

    assert rv == [base_val - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        raise TestException()

    assert rv == [base_val + 1]

    with pytest.raises(TestException):
        with ctx.scope():
            rv = ctx.with_resource(
                TestContext(base_val=base_val, handle_exception=False)
            )
            raise TestException()


def test_with_resource_nested_exception() -> None:
    class TestContext(AbstractContextManager[list[int]]):
        _handle_exception: bool
        _base_val: int
        val: list[int]

        def __init__(self, base_val: int = 1, *, handle_exception: bool = True) -> None:
            self._handle_exception = handle_exception
            self._base_val = base_val

        def __enter__(self) -> list[int]:
            self.val = [self._base_val]
            return self.val

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None:
            if not exc_type:
                self.val[0] = self._base_val - 1
                return None

            self.val[0] = self._base_val + 1
            return self._handle_exception

    class TestException(Exception):
        pass

    ctx = click.Context(click.Command("test"))
    base_val = 1
    base_val_nested = 11

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(TestContext(base_val=base_val_nested))
        assert rv[0] == base_val
        assert rv_nested[0] == base_val_nested

    assert rv == [base_val - 1]
    assert rv_nested == [base_val_nested - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(TestContext(base_val=base_val_nested))
        raise TestException()

    # If one of the context "eats" the exceptions they will not be forwarded to other
    # parts. This is due to how ExitStack unwinding works
    assert rv_nested == [base_val_nested + 1]
    assert rv == [base_val - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(
            TestContext(base_val=base_val_nested, handle_exception=False)
        )
        raise TestException()

    assert rv_nested == [base_val_nested + 1]
    assert rv == [base_val + 1]

    with pytest.raises(TestException):
        rv = ctx.with_resource(TestContext(base_val=base_val, handle_exception=False))
        rv_nested = ctx.with_resource(
            TestContext(base_val=base_val_nested, handle_exception=False)
        )
        raise TestException()


def test_make_pass_decorator_args(runner):
    """
    Test to check that make_pass_decorator doesn't consume arguments based on
    invocation order.
    """

    class Foo:
        title = "foocmd"

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()

    @cli.command()
    @click.pass_context
    @pass_foo
    def test1(foo, ctx):
        click.echo(foo.title)

    @cli.command()
    @pass_foo
    @click.pass_context
    def test2(ctx, foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test1"])
    assert not result.exception
    assert result.output == "foocmd\n"

    result = runner.invoke(cli, ["test2"])
    assert not result.exception
    assert result.output == "foocmd\n"


def test_propagate_show_default_setting(runner):
    """A context's ``show_default`` setting defaults to the value from
    the parent context.
    """
    group = click.Group(
        commands={
            "sub": click.Command("sub", params=[click.Option(["-a"], default="a")]),
        },
        context_settings={"show_default": True},
    )
    result = runner.invoke(group, ["sub", "--help"])
    assert "[default: a]" in result.output


def test_exit_not_standalone():
    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.exit(1)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 1

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.exit(0)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 0


@pytest.mark.parametrize(
    ("option_args", "invoke_args", "expect"),
    [
        pytest.param({}, {}, ParameterSource.DEFAULT, id="default"),
        pytest.param(
            {},
            {"default_map": {"option": 1}},
            ParameterSource.DEFAULT_MAP,
            id="default_map",
        ),
        pytest.param(
            {},
            {"args": ["-o", "1"]},
            ParameterSource.COMMANDLINE,
            id="commandline short",
        ),
        pytest.param(
            {},
            {"args": ["--option", "1"]},
            ParameterSource.COMMANDLINE,
            id="commandline long",
        ),
        pytest.param(
            {},
            {"auto_envvar_prefix": "TEST", "env": {"TEST_OPTION": "1"}},
            ParameterSource.ENVIRONMENT,
            id="environment auto",
        ),
        pytest.param(
            {"envvar": "NAME"},
            {"env": {"NAME": "1"}},
            ParameterSource.ENVIRONMENT,
            id="environment manual",
        ),
    ],
)
def test_parameter_source(runner, option_args, invoke_args, expect):
    @click.command()
    @click.pass_context
    @click.option("-o", "--option", default=1, **option_args)
    def cli(ctx, option):
        return ctx.get_parameter_source("option")

    rv = runner.invoke(cli, standalone_mode=False, **invoke_args)
    assert rv.return_value == expect


def test_propagate_opt_prefixes():
    parent = click.Context(click.Command("test"))
    parent._opt_prefixes = {"-", "--", "!"}
    ctx = click.Context(click.Command("test2"), parent=parent)

    assert ctx._opt_prefixes == {"-", "--", "!"}

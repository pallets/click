import pytest

import click


@pytest.mark.parametrize(
    ("default", "type", "expected_output", "expected_type"),
    [
        (42, click.FLOAT, "42.0", float),
        ("42", click.INT, "42", int),
        (1.5, click.STRING, "1.5", str),
        ("1.5", click.FLOAT, "1.5", float),
        ("true", click.BOOL, "True", bool),
        ("0", click.BOOL, "False", bool),
    ],
)
def test_basic_defaults(runner, default, type, expected_output, expected_type):
    """Smoke test: a single option's default is type-coerced.

    This covers basic single-option default type coercion.
    """

    @click.command()
    @click.option("--foo", default=default, type=type)
    def cli(foo):
        assert isinstance(foo, expected_type)
        click.echo(f"FOO:[{foo}]")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert f"FOO:[{expected_output}]" in result.output


def test_multiple_defaults(runner):
    """Smoke test: each element in a multiple-option default is type-coerced.

    .. hint::
        ``test_options.py::test_good_defaults_for_multiple``
        covers the structural default processing (``list`` to
        ``tuple``, various ``nargs``) exhaustively.

        This test fills the gap of explicit
        ``type=click.FLOAT`` coercion on the elements.
    """

    @click.command()
    @click.option("--foo", default=[23, 42], type=click.FLOAT, multiple=True)
    def cli(foo):
        for item in foo:
            assert isinstance(item, float)
            click.echo(item)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["23.0", "42.0"]


def test_nargs_plus_multiple(runner):
    """Smoke test: option with ``nargs=2`` + ``multiple=True`` and a
    tuple-of-tuples default.

    .. hint::
        ``test_options.py::test_good_defaults_for_multiple``
        expands this with many more edge cases with various
        ``nargs``/``multiple``/``default`` combinations.

        An argument-specific equivalent is in
        ``test_arguments.py::test_good_defaults_for_nargs``.
    """

    @click.command()
    @click.option(
        "--arg", default=((1, 2), (3, 4)), nargs=2, multiple=True, type=click.INT
    )
    def cli(arg):
        for a, b in arg:
            click.echo(f"<{a:d}|{b:d}>")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["<1|2>", "<3|4>"]


def test_multiple_flag_default(runner):
    """Default default for flags when multiple=True should be empty tuple."""

    @click.command
    # flag due to secondary token
    @click.option("-y/-n", multiple=True)
    # flag due to is_flag
    @click.option("-f", is_flag=True, multiple=True)
    # flag due to flag_value
    @click.option("-v", "v", flag_value=1, multiple=True)
    @click.option("-q", "v", flag_value=-1, multiple=True)
    def cli(y, f, v):
        return y, f, v

    result = runner.invoke(cli, standalone_mode=False)
    assert result.return_value == ((), (), ())

    result = runner.invoke(cli, ["-y", "-n", "-f", "-v", "-q"], standalone_mode=False)
    assert result.return_value == ((True, False), (True,), (1, -1))


def test_flag_default_map(runner):
    """test flag with default map"""

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name/--no-name", is_flag=True, show_default=True, help="name flag")
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ["foo"])
    assert "False" in result.output

    result = runner.invoke(cli, ["foo", "--help"])
    assert "default: no-name" in result.output

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": True}})
    assert "True" in result.output

    result = runner.invoke(cli, ["foo", "--help"], default_map={"foo": {"name": True}})
    assert "default: name" in result.output


def test_shared_param_prefers_first_default(runner):
    """The first ``default=True`` wins when multiple ``flag_value`` options share
    a parameter name, regardless of which positional option carries it.

    .. hint::
        ``test_basic.py::test_flag_value_dual_options`` and
        ``test_options.py::test_default_dual_option_callback`` are wider
        parametrized sibling tests covering many more default-value types (``None``,
        ``UNSET``, strings, numbers) but always place the default on the first
        option. This test complements them by exercising both placements.
    """

    @click.command
    @click.option("--red", "color", flag_value="red")
    @click.option("--green", "color", flag_value="green", default=True)
    def prefers_green(color):
        click.echo(color)

    @click.command
    @click.option("--red", "color", flag_value="red", default=True)
    @click.option("--green", "color", flag_value="green")
    def prefers_red(color):
        click.echo(color)

    result = runner.invoke(prefers_green, [])
    assert "green" in result.output
    result = runner.invoke(prefers_green, ["--red"])
    assert "red" in result.output

    result = runner.invoke(prefers_red, [])
    assert "red" in result.output
    result = runner.invoke(prefers_red, ["--green"])
    assert "green" in result.output


@pytest.mark.parametrize(
    ("default_map", "key", "expected"),
    [
        # Key present in default_map.
        ({"email": "a@b.com"}, "email", "a@b.com"),
        # Key missing from default_map.
        ({"email": "a@b.com"}, "nonexistent", None),
        # No default_map at all / empty default_map.
        (None, "anything", None),
        ({}, "anything", None),
        # Falsy values are returned as-is.
        ({"key": None}, "key", None),
        ({"key": 0}, "key", 0),
        ({"key": ""}, "key", ""),
        ({"key": False}, "key", False),
    ],
)
def test_lookup_default_returns_hides_sentinel(default_map, key, expected):
    """``lookup_default()`` should return ``None`` for missing keys, not :attr:`UNSET`.

    Regression test for https://github.com/pallets/click/issues/3145.
    """
    cmd = click.Command("test")
    ctx = click.Context(cmd)
    if default_map is not None:
        ctx.default_map = default_map
    assert ctx.lookup_default(key) == expected


def test_lookup_default_callable_in_default_map(runner):
    """A callable in ``default_map`` is invoked with ``call=True``
    (the default) and returned as-is with ``call=False``.

    Click uses both paths internally:
    - ``get_default()`` passes ``call=False``,
    - ``resolve_ctx()`` passes ``call=True``.
    """
    factory = lambda: "lazy-value"  # noqa: E731

    # Unit-level: call=True invokes, call=False returns as-is.
    cmd = click.Command("test")
    ctx = click.Context(cmd)
    ctx.default_map = {"name": factory}
    assert ctx.lookup_default("name", call=True) == "lazy-value"
    assert ctx.lookup_default("name", call=False) is factory

    # Integration: the callable is invoked during value resolution.
    @click.command()
    @click.option("--name", default="original", show_default=True)
    @click.pass_context
    def cli(ctx, name):
        click.echo(f"name={name!r}")

    result = runner.invoke(cli, [], default_map={"name": factory})
    assert not result.exception
    assert "name='lazy-value'" in result.output

    # Help rendering gets the callable via call=False, so it
    # shows "(dynamic)" rather than invoking it.
    result = runner.invoke(cli, ["--help"], default_map={"name": factory})
    assert not result.exception
    assert "(dynamic)" in result.output


@pytest.mark.parametrize(
    ("args", "default_map", "expected_value", "expected_source"),
    [
        # CLI arg wins over everything.
        (["--name", "cli"], {"name": "mapped"}, "cli", "COMMANDLINE"),
        # default_map overrides parameter default.
        ([], {"name": "mapped"}, "mapped", "DEFAULT_MAP"),
        # Explicit None in default_map still counts as DEFAULT_MAP.
        ([], {"name": None}, None, "DEFAULT_MAP"),
        # Falsy values in default_map are not confused with missing keys.
        ([], {"name": ""}, "", "DEFAULT_MAP"),
        ([], {"name": 0}, "0", "DEFAULT_MAP"),
        # No default_map falls back to parameter default.
        ([], None, "original", "DEFAULT"),
    ],
)
def test_default_map_source(runner, args, default_map, expected_value, expected_source):
    """``get_parameter_source()`` reports the correct origin for a parameter
    value across the resolution chain: CLI > default_map > parameter default.
    """

    @click.command()
    @click.option("--name", default="original")
    @click.pass_context
    def cli(ctx, name):
        source = ctx.get_parameter_source("name")
        click.echo(f"name={name!r} source={source.name}")

    kwargs = {}
    if default_map is not None:
        kwargs["default_map"] = default_map
    result = runner.invoke(cli, args, **kwargs)
    assert not result.exception
    assert f"name={expected_value!r}" in result.output
    assert f"source={expected_source}" in result.output


def test_lookup_default_override_respected(runner):
    """A subclass override of ``lookup_default()`` should be called by Click
    internals, not bypassed by a private method.

    Reproduce exactly https://github.com/pallets/click/issues/3145 in which a
    subclass that falls back to prefix-based lookup when the parent returns
    ``None``.

    Previous attempts in https://github.com/pallets/click/pr/3199 were entirely
    bypassing the user's overridded method.
    """

    class CustomContext(click.Context):
        def lookup_default(self, name, call=True):
            default = super().lookup_default(name, call=call)

            if default is not None:
                return default

            # Prefix-based fallback: look up "app" sub-dict for "app_email".
            prefix = name.split("_", 1)[0]
            group = getattr(self, "default_map", None) or {}
            sub = group.get(prefix)
            if isinstance(sub, dict):
                return sub.get(name)
            return default

    @click.command("get-views")
    @click.option("--app-email", default="original", show_default=True)
    @click.pass_context
    def cli(ctx, app_email):
        click.echo(f"app_email={app_email!r}")

    cli.context_class = CustomContext
    default_map = {"app": {"app_email": "prefix@example.com"}}

    # resolve_ctx path: the override provides the runtime value.
    result = runner.invoke(cli, [], default_map=default_map)
    assert not result.exception
    assert "app_email='prefix@example.com'" in result.output

    # get_default path: the override is also used when
    # rendering --help with show_default=True.
    result = runner.invoke(cli, ["--help"], default_map=default_map)
    assert not result.exception
    assert "prefix@example.com" in result.output

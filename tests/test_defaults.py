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

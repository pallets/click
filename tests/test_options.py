import os
import re

import pytest

import click
from click import Option


def test_prefixes(runner):
    @click.command()
    @click.option("++foo", is_flag=True, help="das foo")
    @click.option("--bar", is_flag=True, help="das bar")
    def cli(foo, bar):
        click.echo(f"foo={foo} bar={bar}")

    result = runner.invoke(cli, ["++foo", "--bar"])
    assert not result.exception
    assert result.output == "foo=True bar=True\n"

    result = runner.invoke(cli, ["--help"])
    assert re.search(r"\+\+foo\s+das foo", result.output) is not None
    assert re.search(r"--bar\s+das bar", result.output) is not None


def test_invalid_option(runner):
    with pytest.raises(TypeError, match="name was passed") as exc_info:
        click.Option(["foo"])

    message = str(exc_info.value)
    assert "name was passed (foo)" in message
    assert "declare an argument" in message
    assert "'--foo'" in message


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_usage(runner, deprecated):
    @click.command()
    @click.option("--foo", default="bar", deprecated=deprecated)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--help"])
    assert "(DEPRECATED" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_warning(runner, deprecated):
    @click.command()
    @click.option(
        "--my-option", required=False, deprecated=deprecated, default="default option"
    )
    def cli(my_option: str):
        click.echo(f"{my_option}")

    # defaults should not give a deprecated warning
    result = runner.invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "is deprecated" not in result.output

    result = runner.invoke(cli, ["--my-option", "hello"])
    assert result.exit_code == 0, result.output
    assert "option 'my_option' is deprecated" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_deprecated_required(runner):
    with pytest.raises(ValueError, match="is deprecated and still required"):
        click.Option(["--a"], required=True, deprecated=True)


def test_deprecated_prompt(runner):
    with pytest.raises(ValueError, match="`deprecated` options cannot use `prompt`"):
        click.Option(["--a"], prompt=True, deprecated=True)


def test_invalid_nargs(runner):
    with pytest.raises(TypeError, match="nargs=-1"):

        @click.command()
        @click.option("--foo", nargs=-1)
        def cli(foo):
            pass


def test_nargs_tup_composite_mult(runner):
    @click.command()
    @click.option("--item", type=(str, int), multiple=True)
    def copy(item):
        for name, id in item:
            click.echo(f"name={name} id={id:d}")

    result = runner.invoke(copy, ["--item", "peter", "1", "--item", "max", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter id=1", "name=max id=2"]


def test_counting(runner):
    @click.command()
    @click.option("-v", count=True, help="Verbosity", type=click.IntRange(0, 3))
    def cli(v):
        click.echo(f"verbosity={v:d}")

    result = runner.invoke(cli, ["-vvv"])
    assert not result.exception
    assert result.output == "verbosity=3\n"

    result = runner.invoke(cli, ["-vvvv"])
    assert result.exception
    assert "Invalid value for '-v': 4 is not in the range 0<=x<=3." in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "verbosity=0\n"

    result = runner.invoke(cli, ["--help"])
    assert re.search(r"-v\s+Verbosity", result.output) is not None


@pytest.mark.parametrize("unknown_flag", ["--foo", "-f"])
def test_unknown_options(runner, unknown_flag):
    @click.command()
    def cli():
        pass

    result = runner.invoke(cli, [unknown_flag])
    assert result.exception
    assert f"No such option: {unknown_flag}" in result.output


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("--cat", "Did you mean --count?"),
        ("--bounds", "(Possible options: --bound, --count)"),
        ("--bount", "(Possible options: --bound, --count)"),
    ],
)
def test_suggest_possible_options(runner, value, expect):
    cli = click.Command(
        "cli", params=[click.Option(["--bound"]), click.Option(["--count"])]
    )
    result = runner.invoke(cli, [value])
    assert expect in result.output


def test_multiple_required(runner):
    @click.command()
    @click.option("-m", "--message", multiple=True, required=True)
    def cli(message):
        click.echo("\n".join(message))

    result = runner.invoke(cli, ["-m", "foo", "-mbar"])
    assert not result.exception
    assert result.output == "foo\nbar\n"

    result = runner.invoke(cli, [])
    assert result.exception
    assert "Error: Missing option '-m' / '--message'." in result.output


@pytest.mark.parametrize(
    ("multiple", "nargs", "default"),
    [
        (True, 1, []),
        (True, 1, [1]),
        # (False, -1, []),
        # (False, -1, [1]),
        (False, 2, [1, 2]),
        # (True, -1, [[]]),
        # (True, -1, []),
        # (True, -1, [[1]]),
        (True, 2, []),
        (True, 2, [[1, 2]]),
    ],
)
def test_init_good_default_list(runner, multiple, nargs, default):
    click.Option(["-a"], multiple=multiple, nargs=nargs, default=default)


@pytest.mark.parametrize(
    ("multiple", "nargs", "default"),
    [
        (True, 1, 1),
        # (False, -1, 1),
        (False, 2, [1]),
        (True, 2, [[1]]),
    ],
)
def test_init_bad_default_list(runner, multiple, nargs, default):
    type = (str, str) if nargs == 2 else None

    with pytest.raises(ValueError, match="default"):
        click.Option(["-a"], type=type, multiple=multiple, nargs=nargs, default=default)


@pytest.mark.parametrize("env_key", ["MYPATH", "AUTO_MYPATH"])
def test_empty_envvar(runner, env_key):
    @click.command()
    @click.option("--mypath", type=click.Path(exists=True), envvar="MYPATH")
    def cli(mypath):
        click.echo(f"mypath: {mypath}")

    result = runner.invoke(cli, env={env_key: ""}, auto_envvar_prefix="AUTO")
    assert result.exception is None
    assert result.output == "mypath: None\n"


def test_multiple_envvar(runner):
    @click.command()
    @click.option("--arg", multiple=True)
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "foo bar baz"}
    )
    assert not result.exception
    assert result.output == "foo|bar|baz\n"

    @click.command()
    @click.option("--arg", multiple=True, envvar="X")
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(cmd, [], env={"X": "foo bar baz"})
    assert not result.exception
    assert result.output == "foo|bar|baz\n"

    @click.command()
    @click.option("--arg", multiple=True, type=click.Path())
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd,
        [],
        auto_envvar_prefix="TEST",
        env={"TEST_ARG": f"foo{os.path.pathsep}bar"},
    )
    assert not result.exception
    assert result.output == "foo|bar\n"


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    (
        # Lower-cased variations of value.
        ("SHOUT", "true", True),
        ("SHOUT", "false", False),
        # Title-cased variations of value.
        ("SHOUT", "True", True),
        ("SHOUT", "False", False),
        # Upper-cased variations of value.
        ("SHOUT", "TRUE", True),
        ("SHOUT", "FALSE", False),
        # Random-cased variations of value.
        ("SHOUT", "TruE", True),
        ("SHOUT", "truE", True),
        ("SHOUT", "FaLsE", False),
        ("SHOUT", "falsE", False),
        # Extra spaces around the value.
        ("SHOUT", "true ", True),
        ("SHOUT", " true", True),
        ("SHOUT", " true ", True),
        ("SHOUT", "false ", False),
        ("SHOUT", " false", False),
        ("SHOUT", " false ", False),
        # Integer variations.
        ("SHOUT", "1", True),
        ("SHOUT", "0", False),
        # Alternative states.
        ("SHOUT", "t", True),
        ("SHOUT", "f", False),
        ("SHOUT", "y", True),
        ("SHOUT", "n", False),
        ("SHOUT", "yes", True),
        ("SHOUT", "no", False),
        ("SHOUT", "on", True),
        ("SHOUT", "off", False),
        # Blank value variations.
        ("SHOUT", None, False),
        ("SHOUT", "", False),
        ("SHOUT", " ", False),
        ("SHOUT", "       ", False),
        # Variable names are not stripped of spaces and so don't match the
        # flag, which then naturraly takes its default value.
        ("SHOUT  ", "True", False),
        ("SHOUT  ", "False", False),
        ("  SHOUT  ", "True", False),
        ("  SHOUT  ", "False", False),
        # Same for random and reverse environment variable names: they are not
        # recognized by the option.
        ("RANDOM", "True", False),
        ("NO_SHOUT", "True", False),
        ("NO_SHOUT", "False", False),
    ),
)
def test_boolean_envvar_normalization(runner, name, value, expected):
    @click.command()
    @click.option("--shout/--no-shout", envvar="SHOUT")
    def cli(shout):
        click.echo(f"shout: {shout!r}")

    result = runner.invoke(cli, [], env={name: value})
    assert result.exit_code == 0
    assert result.output == f"shout: {expected}\n"


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("SHOUT", "tr ue"),
        ("SHOUT", "10"),
        ("SHOUT", "01"),
        ("SHOUT", "00"),
        ("SHOUT", "11"),
        ("SHOUT", "randomstring"),
        ("SHOUT", "None"),
    ),
)
def test_boolean_envvar_bad_values(runner, name, value):
    @click.command()
    @click.option("--shout/--no-shout", envvar="SHOUT")
    def cli(shout):
        click.echo(f"shout: {shout!r}")

    result = runner.invoke(cli, [], env={name: value})
    assert result.exit_code == 2
    assert (
        f"Invalid value for '--shout': {value!r} is not a valid boolean."
        in result.output
    )


def test_multiple_default_help(runner):
    @click.command()
    @click.option("--arg1", multiple=True, default=("foo", "bar"), show_default=True)
    @click.option("--arg2", multiple=True, default=(1, 2), type=int, show_default=True)
    def cmd(arg, arg2):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert not result.exception
    assert "foo, bar" in result.output
    assert "1, 2" in result.output


def test_show_default_default_map(runner):
    @click.command()
    @click.option("--arg", default="a", show_default=True)
    def cmd(arg):
        click.echo(arg)

    result = runner.invoke(cmd, ["--help"], default_map={"arg": "b"})

    assert not result.exception
    assert "[default: b]" in result.output


def test_multiple_default_type():
    opt = click.Option(["-a"], multiple=True, default=(1, 2))
    assert opt.nargs == 1
    assert opt.multiple
    assert opt.type is click.INT
    ctx = click.Context(click.Command("test"))
    assert opt.get_default(ctx) == (1, 2)


def test_multiple_default_composite_type():
    opt = click.Option(["-a"], multiple=True, default=[(1, "a")])
    assert opt.nargs == 2
    assert opt.multiple
    assert isinstance(opt.type, click.Tuple)
    assert opt.type.types == [click.INT, click.STRING]
    ctx = click.Context(click.Command("test"))
    assert opt.type_cast_value(ctx, opt.get_default(ctx)) == ((1, "a"),)


def test_parse_multiple_default_composite_type(runner):
    @click.command()
    @click.option("-a", multiple=True, default=("a", "b"))
    @click.option("-b", multiple=True, default=[(1, "a")])
    def cmd(a, b):
        click.echo(a)
        click.echo(b)

    # result = runner.invoke(cmd, "-a c -a 1 -a d -b 2 two -b 4 four".split())
    # assert result.output == "('c', '1', 'd')\n((2, 'two'), (4, 'four'))\n"
    result = runner.invoke(cmd)
    assert result.output == "('a', 'b')\n((1, 'a'),)\n"


def test_dynamic_default_help_unset(runner):
    @click.command()
    @click.option(
        "--username",
        prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default=True,
    )
    def cmd(username):
        print("Hello,", username)

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "--username" in result.output
    assert "lambda" not in result.output
    assert "(dynamic)" in result.output


def test_dynamic_default_help_text(runner):
    @click.command()
    @click.option(
        "--username",
        prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default="current user",
    )
    def cmd(username):
        print("Hello,", username)

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "--username" in result.output
    assert "lambda" not in result.output
    assert "(current user)" in result.output


def test_dynamic_default_help_special_method(runner):
    class Value:
        def __call__(self):
            return 42

        def __str__(self):
            return "special value"

    opt = click.Option(["-a"], default=Value(), show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {"default": "special value"}
    assert "special value" in opt.get_help_record(ctx)[1]


@pytest.mark.parametrize(
    ("type", "expect"),
    [
        (click.IntRange(1, 32), "1<=x<=32"),
        (click.IntRange(1, 32, min_open=True, max_open=True), "1<x<32"),
        (click.IntRange(1), "x>=1"),
        (click.IntRange(max=32), "x<=32"),
    ],
)
def test_intrange_default_help_text(type, expect):
    option = click.Option(["--num"], type=type, show_default=True, default=2)
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {"default": "2", "range": expect}
    result = option.get_help_record(context)[1]
    assert expect in result


def test_count_default_type_help():
    """A count option with the default type should not show >=0 in help."""
    option = click.Option(["--count"], count=True, help="some words")
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {}
    result = option.get_help_record(context)[1]
    assert result == "some words"


def test_file_type_help_default():
    """The default for a File type is a filename string. The string
    should be displayed in help, not an open file object.

    Type casting is only applied to defaults in processing, not when
    getting the default value.
    """
    option = click.Option(
        ["--in"], type=click.File(), default=__file__, show_default=True
    )
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {"default": __file__}
    result = option.get_help_record(context)[1]
    assert __file__ in result


def test_toupper_envvar_prefix(runner):
    @click.command()
    @click.option("--arg")
    def cmd(arg):
        click.echo(arg)

    result = runner.invoke(cmd, [], auto_envvar_prefix="test", env={"TEST_ARG": "foo"})
    assert not result.exception
    assert result.output == "foo\n"


def test_nargs_envvar(runner):
    @click.command()
    @click.option("--arg", nargs=2)
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "foo bar"}
    )
    assert not result.exception
    assert result.output == "foo|bar\n"

    @click.command()
    @click.option("--arg", nargs=2, multiple=True)
    def cmd(arg):
        for item in arg:
            click.echo("|".join(item))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "x 1 y 2"}
    )
    assert not result.exception
    assert result.output == "x|1\ny|2\n"


def test_show_envvar(runner):
    @click.command()
    @click.option("--arg1", envvar="ARG1", show_envvar=True)
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert not result.exception
    assert "ARG1" in result.output


def test_show_envvar_auto_prefix(runner):
    @click.command()
    @click.option("--arg1", show_envvar=True)
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["--help"], auto_envvar_prefix="TEST")
    assert not result.exception
    assert "TEST_ARG1" in result.output


def test_show_envvar_auto_prefix_dash_in_command(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--baz", show_envvar=True)
    def foo_bar(baz):
        pass

    result = runner.invoke(cli, ["foo-bar", "--help"], auto_envvar_prefix="TEST")
    assert not result.exception
    assert "TEST_FOO_BAR_BAZ" in result.output


def test_custom_validation(runner):
    def validate_pos_int(ctx, param, value):
        if value < 0:
            raise click.BadParameter("Value needs to be positive")
        return value

    @click.command()
    @click.option("--foo", callback=validate_pos_int, default=1)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "-1"])
    assert "Invalid value for '--foo': Value needs to be positive" in result.output

    result = runner.invoke(cmd, ["--foo", "42"])
    assert result.output == "42\n"


def test_callback_validates_prompt(runner, monkeypatch):
    def validate(ctx, param, value):
        if value < 0:
            raise click.BadParameter("should be positive")

        return value

    @click.command()
    @click.option("-a", type=int, callback=validate, prompt=True)
    def cli(a):
        click.echo(a)

    result = runner.invoke(cli, input="-12\n60\n")
    assert result.output == "A: -12\nError: should be positive\nA: 60\n60\n"


def test_winstyle_options(runner):
    @click.command()
    @click.option("/debug;/no-debug", help="Enables or disables debug mode.")
    def cmd(debug):
        click.echo(debug)

    result = runner.invoke(cmd, ["/debug"], help_option_names=["/?"])
    assert result.output == "True\n"
    result = runner.invoke(cmd, ["/no-debug"], help_option_names=["/?"])
    assert result.output == "False\n"
    result = runner.invoke(cmd, [], help_option_names=["/?"])
    assert result.output == "False\n"
    result = runner.invoke(cmd, ["/?"], help_option_names=["/?"])
    assert "/debug; /no-debug  Enables or disables debug mode." in result.output
    assert "/?                 Show this message and exit." in result.output


def test_legacy_options(runner):
    @click.command()
    @click.option("-whatever")
    def cmd(whatever):
        click.echo(whatever)

    result = runner.invoke(cmd, ["-whatever", "42"])
    assert result.output == "42\n"
    result = runner.invoke(cmd, ["-whatever=23"])
    assert result.output == "23\n"


def test_missing_option_string_cast():
    ctx = click.Context(click.Command(""))

    with pytest.raises(click.MissingParameter) as excinfo:
        click.Option(["-a"], required=True).process_value(ctx, None)

    assert str(excinfo.value) == "Missing parameter: a"


def test_missing_required_flag(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--on/--off"], is_flag=True, required=True)]
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--on'." in result.output


def test_missing_choice(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["foo", "bar"]), required=True)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd)
    assert result.exit_code == 2
    error, separator, choices = result.output.partition("Choose from")
    assert "Error: Missing option '--foo'. " in error
    assert "Choose from" in separator
    assert "foo" in choices
    assert "bar" in choices


def test_missing_envvar(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--foo"], envvar="bar", required=True)]
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--foo'." in result.output
    cli = click.Command(
        "cli",
        params=[click.Option(["--foo"], envvar="bar", show_envvar=True, required=True)],
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--foo' (env var: 'bar')." in result.output


def test_case_insensitive_choice(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"], case_sensitive=False))
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"

    result = runner.invoke(cmd, ["--foo", "oRANGe"])
    assert result.exit_code == 0
    assert result.output == "Orange\n"

    result = runner.invoke(cmd, ["--foo", "Apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"

    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"]))
    def cmd2(foo):
        click.echo(foo)

    result = runner.invoke(cmd2, ["--foo", "apple"])
    assert result.exit_code == 2

    result = runner.invoke(cmd2, ["--foo", "oRANGe"])
    assert result.exit_code == 2

    result = runner.invoke(cmd2, ["--foo", "Apple"])
    assert result.exit_code == 0


def test_case_insensitive_choice_returned_exactly(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"], case_sensitive=False))
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"


def test_option_help_preserve_paragraphs(runner):
    @click.command()
    @click.option(
        "-C",
        "--config",
        type=click.Path(),
        help="""Configuration file to use.

        If not given, the environment variable CONFIG_FILE is consulted
        and used if set. If neither are given, a default configuration
        file is loaded.""",
    )
    def cmd(config):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    i = " " * 21
    assert (
        "  -C, --config PATH  Configuration file to use.\n"
        f"{i}\n"
        f"{i}If not given, the environment variable CONFIG_FILE is\n"
        f"{i}consulted and used if set. If neither are given, a default\n"
        f"{i}configuration file is loaded."
    ) in result.output


def test_argument_custom_class(runner):
    class CustomArgument(click.Argument):
        def get_default(self, ctx, call=True):
            """a dumb override of a default value for testing"""
            return "I am a default"

    @click.command()
    @click.argument("testarg", cls=CustomArgument, default="you wont see me")
    def cmd(testarg):
        click.echo(testarg)

    result = runner.invoke(cmd)
    assert "I am a default" in result.output
    assert "you wont see me" not in result.output


def test_option_custom_class(runner):
    class CustomOption(click.Option):
        def get_help_record(self, ctx):
            """a dumb override of a help text for testing"""
            return ("--help", "I am a help text")

    @click.command()
    @click.option("--testoption", cls=CustomOption, help="you wont see me")
    def cmd(testoption):
        click.echo(testoption)

    result = runner.invoke(cmd, ["--help"])
    assert "I am a help text" in result.output
    assert "you wont see me" not in result.output


def test_option_custom_class_reusable(runner):
    """Ensure we can reuse a custom class option. See Issue #926"""

    class CustomOption(click.Option):
        def get_help_record(self, ctx):
            """a dumb override of a help text for testing"""
            return ("--help", "I am a help text")

    # Assign to a variable to re-use the decorator.
    testoption = click.option("--testoption", cls=CustomOption, help="you wont see me")

    @click.command()
    @testoption
    def cmd1(testoption):
        click.echo(testoption)

    @click.command()
    @testoption
    def cmd2(testoption):
        click.echo(testoption)

    # Both of the commands should have the --help option now.
    for cmd in (cmd1, cmd2):
        result = runner.invoke(cmd, ["--help"])
        assert "I am a help text" in result.output
        assert "you wont see me" not in result.output


@pytest.mark.parametrize("custom_class", (True, False))
@pytest.mark.parametrize(
    ("name_specs", "expected"),
    (
        (
            ("-h", "--help"),
            "  -h, --help  Show this message and exit.\n",
        ),
        (
            ("-h",),
            "  -h      Show this message and exit.\n"
            "  --help  Show this message and exit.\n",
        ),
        (
            ("--help",),
            "  --help  Show this message and exit.\n",
        ),
    ),
)
def test_help_option_custom_names_and_class(runner, custom_class, name_specs, expected):
    class CustomHelpOption(click.Option):
        pass

    option_attrs = {}
    if custom_class:
        option_attrs["cls"] = CustomHelpOption

    @click.command()
    @click.help_option(*name_specs, **option_attrs)
    def cmd():
        pass

    for arg in name_specs:
        result = runner.invoke(cmd, [arg])
        assert not result.exception
        assert result.exit_code == 0
        assert expected in result.output


def test_bool_flag_with_type(runner):
    @click.command()
    @click.option("--shout/--no-shout", default=False, type=bool)
    def cmd(shout):
        pass

    result = runner.invoke(cmd)
    assert not result.exception


def test_aliases_for_flags(runner):
    @click.command()
    @click.option("--warnings/--no-warnings", " /-W", default=True)
    def cli(warnings):
        click.echo(warnings)

    result = runner.invoke(cli, ["--warnings"])
    assert result.output == "True\n"
    result = runner.invoke(cli, ["--no-warnings"])
    assert result.output == "False\n"
    result = runner.invoke(cli, ["-W"])
    assert result.output == "False\n"

    @click.command()
    @click.option("--warnings/--no-warnings", "-w", default=True)
    def cli_alt(warnings):
        click.echo(warnings)

    result = runner.invoke(cli_alt, ["--warnings"])
    assert result.output == "True\n"
    result = runner.invoke(cli_alt, ["--no-warnings"])
    assert result.output == "False\n"
    result = runner.invoke(cli_alt, ["-w"])
    assert result.output == "True\n"


@pytest.mark.parametrize(
    "option_args,expected",
    [
        (["--aggressive", "--all", "-a"], "aggressive"),
        (["--first", "--second", "--third", "-a", "-b", "-c"], "first"),
        (["--apple", "--banana", "--cantaloupe", "-a", "-b", "-c"], "apple"),
        (["--cantaloupe", "--banana", "--apple", "-c", "-b", "-a"], "cantaloupe"),
        (["-a", "-b", "-c"], "a"),
        (["-c", "-b", "-a"], "c"),
        (["-a", "--apple", "-b", "--banana", "-c", "--cantaloupe"], "apple"),
        (["-c", "-a", "--cantaloupe", "-b", "--banana", "--apple"], "cantaloupe"),
        (["--from", "-f", "_from"], "_from"),
        (["--return", "-r", "_ret"], "_ret"),
    ],
)
def test_option_names(runner, option_args, expected):
    @click.command()
    @click.option(*option_args, is_flag=True)
    def cmd(**kwargs):
        click.echo(str(kwargs[expected]))

    assert cmd.params[0].name == expected

    for form in option_args:
        if form.startswith("-"):
            result = runner.invoke(cmd, [form])
            assert result.output == "True\n"


def test_flag_duplicate_names(runner):
    with pytest.raises(ValueError, match="cannot use the same flag for true/false"):
        click.Option(["--foo/--foo"], default=False)


@pytest.mark.parametrize(("default", "expect"), [(False, "no-cache"), (True, "cache")])
def test_show_default_boolean_flag_name(runner, default, expect):
    """When a boolean flag has distinct True/False opts, it should show
    the default opt name instead of the default value. It should only
    show one name even if multiple are declared.
    """
    opt = click.Option(
        ("--cache/--no-cache", "--c/--nc"),
        default=default,
        show_default=True,
        help="Enable/Disable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {"default": expect}
    message = opt.get_help_record(ctx)[1]
    assert f"[default: {expect}]" in message


def test_show_true_default_boolean_flag_value(runner):
    """When a boolean flag only has one opt and its default is True,
    it will show the default value, not the opt name.
    """
    opt = click.Option(
        ("--cache",),
        is_flag=True,
        show_default=True,
        default=True,
        help="Enable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {"default": "True"}
    message = opt.get_help_record(ctx)[1]
    assert "[default: True]" in message


@pytest.mark.parametrize("default", [False, None])
def test_hide_false_default_boolean_flag_value(runner, default):
    """When a boolean flag only has one opt and its default is False or
    None, it will not show the default
    """
    opt = click.Option(
        ("--cache",),
        is_flag=True,
        show_default=True,
        default=default,
        help="Enable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert "[default: " not in message


def test_show_default_string(runner):
    """When show_default is a string show that value as default."""
    opt = click.Option(["--limit"], show_default="unlimited")
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {"default": "(unlimited)"}
    message = opt.get_help_record(ctx)[1]
    assert "[default: (unlimited)]" in message


def test_show_default_with_empty_string(runner):
    """When show_default is True and default is set to an empty string."""
    opt = click.Option(["--limit"], default="", show_default=True)
    ctx = click.Context(click.Command("cli"))
    message = opt.get_help_record(ctx)[1]
    assert '[default: ""]' in message


def test_do_not_show_no_default(runner):
    """When show_default is True and no default is set do not show None."""
    opt = click.Option(["--limit"], show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert "[default: None]" not in message


def test_do_not_show_default_empty_multiple():
    """When show_default is True and multiple=True is set, it should not
    print empty default value in --help output.
    """
    opt = click.Option(["-a"], multiple=True, help="values", show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert message == "values"


@pytest.mark.parametrize(
    ("ctx_value", "opt_value", "extra_value", "expect"),
    [
        (None, None, {}, False),
        (None, False, {}, False),
        (None, True, {"default": "1"}, True),
        (False, None, {}, False),
        (False, False, {}, False),
        (False, True, {"default": "1"}, True),
        (True, None, {"default": "1"}, True),
        (True, False, {}, False),
        (True, True, {"default": "1"}, True),
        (False, "one", {"default": "(one)"}, True),
    ],
)
def test_show_default_precedence(ctx_value, opt_value, extra_value, expect):
    ctx = click.Context(click.Command("test"), show_default=ctx_value)
    opt = click.Option("-a", default=1, help="value", show_default=opt_value)
    assert opt.get_help_extra(ctx) == extra_value
    help = opt.get_help_record(ctx)[1]
    assert ("default:" in help) is expect


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        (None, (None, None, ())),
        (["--opt"], ("flag", None, ())),
        (["--opt", "-a", 42], ("flag", "42", ())),
        (["--opt", "test", "-a", 42], ("test", "42", ())),
        (["--opt=test", "-a", 42], ("test", "42", ())),
        (["-o"], ("flag", None, ())),
        (["-o", "-a", 42], ("flag", "42", ())),
        (["-o", "test", "-a", 42], ("test", "42", ())),
        (["-otest", "-a", 42], ("test", "42", ())),
        (["a", "b", "c"], (None, None, ("a", "b", "c"))),
        (["--opt", "a", "b", "c"], ("a", None, ("b", "c"))),
        (["--opt", "test"], ("test", None, ())),
        (["-otest", "a", "b", "c"], ("test", None, ("a", "b", "c"))),
        (["--opt=test", "a", "b", "c"], ("test", None, ("a", "b", "c"))),
    ],
)
def test_option_with_optional_value(runner, args, expect):
    @click.command()
    @click.option("-o", "--opt", is_flag=False, flag_value="flag")
    @click.option("-a")
    @click.argument("b", nargs=-1)
    def cli(opt, a, b):
        return opt, a, b

    result = runner.invoke(cli, args, standalone_mode=False, catch_exceptions=False)
    assert result.return_value == expect


def test_multiple_option_with_optional_value(runner):
    cli = click.Command(
        "cli",
        params=[
            click.Option(["-f"], is_flag=False, flag_value="flag", multiple=True),
            click.Option(["-a"]),
            click.Argument(["b"], nargs=-1),
        ],
        callback=lambda **kwargs: kwargs,
    )
    result = runner.invoke(
        cli,
        ["-f", "-f", "other", "-f", "-a", "1", "a", "b"],
        standalone_mode=False,
        catch_exceptions=False,
    )
    assert result.return_value == {
        "f": ("flag", "other", "flag"),
        "a": "1",
        "b": ("a", "b"),
    }


def test_type_from_flag_value():
    param = click.Option(["-a", "x"], default=True, flag_value=4)
    assert param.type is click.INT
    param = click.Option(["-b", "x"], flag_value=8)
    assert param.type is click.INT


@pytest.mark.parametrize(
    ("opt_params", "pass_flag", "expected"),
    [
        # Effect of the presence/absence of flag depending on type
        ({"type": bool}, False, False),
        ({"type": bool}, True, True),
        ({"type": click.BOOL}, False, False),
        ({"type": click.BOOL}, True, True),
        ({"type": str}, False, "False"),
        ({"type": str}, True, "True"),
        # Effects of default value
        ({"type": bool, "default": True}, False, True),
        ({"type": bool, "default": True}, True, True),
        ({"type": bool, "default": False}, False, False),
        ({"type": bool, "default": False}, True, True),
        ({"type": bool, "default": None}, False, False),
        ({"type": bool, "default": None}, True, True),
        ({"type": click.BOOL, "default": True}, False, True),
        ({"type": click.BOOL, "default": True}, True, True),
        ({"type": click.BOOL, "default": False}, False, False),
        ({"type": click.BOOL, "default": False}, True, True),
        ({"type": click.BOOL, "default": None}, False, False),
        ({"type": click.BOOL, "default": None}, True, True),
        ({"type": str, "default": True}, False, "True"),
        ({"type": str, "default": True}, True, "True"),
        ({"type": str, "default": False}, False, "False"),
        ({"type": str, "default": False}, True, "True"),
        ({"type": str, "default": "foo"}, False, "foo"),
        ({"type": str, "default": "foo"}, True, "foo"),
        ({"type": str, "default": None}, False, "False"),
        ({"type": str, "default": None}, True, "True"),
        # Effects of flag_value
        ({"type": bool, "flag_value": True}, False, False),
        ({"type": bool, "flag_value": True}, True, True),
        ({"type": bool, "flag_value": False}, False, False),
        ({"type": bool, "flag_value": False}, True, False),
        ({"type": bool, "flag_value": None}, False, False),
        ({"type": bool, "flag_value": None}, True, True),
        ({"type": click.BOOL, "flag_value": True}, False, False),
        ({"type": click.BOOL, "flag_value": True}, True, True),
        ({"type": click.BOOL, "flag_value": False}, False, False),
        ({"type": click.BOOL, "flag_value": False}, True, False),
        ({"type": click.BOOL, "flag_value": None}, False, False),
        ({"type": click.BOOL, "flag_value": None}, True, True),
        ({"type": str, "flag_value": True}, False, "False"),
        ({"type": str, "flag_value": True}, True, "True"),
        ({"type": str, "flag_value": False}, False, "False"),
        ({"type": str, "flag_value": False}, True, "False"),
        ({"type": str, "flag_value": "foo"}, False, "False"),
        ({"type": str, "flag_value": "foo"}, True, "foo"),
        ({"type": str, "flag_value": None}, False, "False"),
        ({"type": str, "flag_value": None}, True, "True"),
        # Not passing --foo returns the default value as-is
        ({"type": bool, "default": True, "flag_value": True}, False, True),
        ({"type": bool, "default": True, "flag_value": False}, False, True),
        ({"type": bool, "default": False, "flag_value": True}, False, False),
        ({"type": bool, "default": False, "flag_value": False}, False, False),
        ({"type": bool, "default": None, "flag_value": True}, False, False),
        ({"type": bool, "default": None, "flag_value": False}, False, False),
        ({"type": str, "default": True, "flag_value": True}, False, "True"),
        ({"type": str, "default": True, "flag_value": False}, False, "True"),
        ({"type": str, "default": False, "flag_value": True}, False, "False"),
        ({"type": str, "default": False, "flag_value": False}, False, "False"),
        ({"type": str, "default": "foo", "flag_value": True}, False, "foo"),
        ({"type": str, "default": "foo", "flag_value": False}, False, "foo"),
        ({"type": str, "default": "foo", "flag_value": "bar"}, False, "foo"),
        ({"type": str, "default": "foo", "flag_value": None}, False, "foo"),
        ({"type": str, "default": None, "flag_value": True}, False, "False"),
        ({"type": str, "default": None, "flag_value": False}, False, "False"),
        # Passing --foo returns the explicitly set flag_value
        ({"type": bool, "default": True, "flag_value": True}, True, True),
        ({"type": bool, "default": True, "flag_value": False}, True, False),
        ({"type": bool, "default": False, "flag_value": True}, True, True),
        ({"type": bool, "default": False, "flag_value": False}, True, False),
        ({"type": bool, "default": None, "flag_value": True}, True, True),
        ({"type": bool, "default": None, "flag_value": False}, True, False),
        ({"type": str, "default": True, "flag_value": True}, True, "True"),
        ({"type": str, "default": True, "flag_value": False}, True, "False"),
        ({"type": str, "default": False, "flag_value": True}, True, "True"),
        ({"type": str, "default": False, "flag_value": False}, True, "False"),
        ({"type": str, "default": "foo", "flag_value": True}, True, "True"),
        ({"type": str, "default": "foo", "flag_value": False}, True, "False"),
        ({"type": str, "default": "foo", "flag_value": "bar"}, True, "bar"),
        ({"type": str, "default": "foo", "flag_value": None}, True, "foo"),
        ({"type": str, "default": None, "flag_value": True}, True, "True"),
        ({"type": str, "default": None, "flag_value": False}, True, "False"),
    ],
)
def test_flag_value_and_default(runner, opt_params, pass_flag, expected):
    @click.command()
    @click.option("--foo", is_flag=True, **opt_params)
    def cmd(foo):
        click.echo(repr(foo))

    result = runner.invoke(cmd, ["--foo"] if pass_flag else [])
    assert result.output == f"{expected!r}\n"


@pytest.mark.parametrize(
    "opts",
    [
        {"type": bool, "default": "foo"},
        {"type": bool, "flag_value": "foo"},
        {"type": click.BOOL, "default": "foo"},
        {"type": click.BOOL, "flag_value": "foo"},
    ],
)
def test_invalid_flag_definition(runner, opts):
    @click.command()
    @click.option("--foo", is_flag=True, **opts)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo"])
    assert (
        "Error: Invalid value for '--foo': 'foo' is not a valid boolean"
        in result.output
    )


@pytest.mark.parametrize(
    ("flag_value", "envvar_value", "expected"),
    [
        # Envvar is set to false, so the flag default value is returned.
        ("bar", "False", "False"),
        # Same as above with alternative states and blank values.
        ("bar", "0", "False"),
        ("bar", "f", "False"),
        ("bar", "", "False"),
        # Envvar is set to true, so the flag_value is returned.
        ("bar", "True", "bar"),
        ("bar", "1", "bar"),
        ("bar", "t", "bar"),
        # So far we have the same cases as the test_flag_value_and_default
        # test case. Now instead of passing a boolean-like value, let's use
        # the flag_value as the envvar value.
        ("bar", "bar", "bar"),
        # flag_value is expected to be the exact same in the envvar for the flag to be
        # activated.
        ("bar", " bar ", "False"),
        ("bar", "BAR", "False"),
        ("bar", "random", "False"),
        ("bar", "bar random", "False"),
        ("bar", "random bar", "False"),
        ("BAR", "BAR", "BAR"),
        ("BAR", "bar", "False"),
        (" bar ", " bar ", " bar "),
        (" bar ", "bar", "False"),
        (" bar ", "BAR", "False"),
    ],
)
def test_envvar_flag_value(runner, flag_value, envvar_value, expected):
    """Ensure that flag_value is recognized by the envvar."""

    @click.command()
    @click.option(
        "--upper", type=str, is_flag=True, flag_value=flag_value, envvar="UPPER"
    )
    def cmd(upper):
        click.echo(repr(upper))

    result = runner.invoke(cmd, env={"UPPER": envvar_value})
    assert result.exit_code == 0
    assert result.output == f"{expected!r}\n"


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        # Not boolean flags
        pytest.param(Option(["-a"], type=int), False, id="int option"),
        pytest.param(Option(["-a"], type=bool), False, id="bool non-flag [None]"),
        pytest.param(Option(["-a"], default=True), False, id="bool non-flag [True]"),
        pytest.param(Option(["-a"], default=False), False, id="bool non-flag [False]"),
        pytest.param(Option(["-a"], flag_value=1), False, id="non-bool flag_value"),
        # Boolean flags
        pytest.param(Option(["-a"], is_flag=True), True, id="is_flag=True"),
        pytest.param(Option(["-a/-A"]), True, id="secondary option [implicit flag]"),
        pytest.param(Option(["-a"], flag_value=True), True, id="bool flag_value"),
    ],
)
def test_bool_flag_auto_detection(option, expected):
    assert option.is_bool_flag is expected


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"count": True, "multiple": True}, "'count' is not valid with 'multiple'."),
        ({"count": True, "is_flag": True}, "'count' is not valid with 'is_flag'."),
    ],
)
def test_invalid_flag_combinations(runner, kwargs, message):
    with pytest.raises(TypeError) as e:
        click.Option(["-a"], **kwargs)

    assert message in str(e.value)


def test_non_flag_with_non_negatable_default(runner):
    class NonNegatable:
        def __bool__(self):
            raise ValueError("Cannot negate this object")

    @click.command()
    @click.option("--foo", default=NonNegatable())
    def cmd(foo):
        pass

    result = runner.invoke(cmd)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("choices", "metavars"),
    [
        pytest.param(["foo", "bar"], "[TEXT]", id="text choices"),
        pytest.param([1, 2], "[INTEGER]", id="int choices"),
        pytest.param([1.0, 2.0], "[FLOAT]", id="float choices"),
        pytest.param([True, False], "[BOOLEAN]", id="bool choices"),
        pytest.param(["foo", 1], "[TEXT|INTEGER]", id="text/int choices"),
    ],
)
def test_usage_show_choices(runner, choices, metavars):
    """When show_choices=False is set, the --help output
    should print choice metavars instead of values.
    """

    @click.command()
    @click.option("-g", type=click.Choice(choices))
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option(
        "-g",
        type=click.Choice(choices),
        show_choices=False,
    )
    def cli_without_choices(g):
        pass

    result = runner.invoke(cli_with_choices, ["--help"])
    assert f"[{'|'.join([str(i) for i in choices])}]" in result.output

    result = runner.invoke(cli_without_choices, ["--help"])
    assert metavars in result.output


@pytest.mark.parametrize(
    "opts_one,opts_two",
    [
        # No duplicate shortnames
        (
            ("-a", "--aardvark"),
            ("-a", "--avocado"),
        ),
        # No duplicate long names
        (
            ("-a", "--aardvark"),
            ("-b", "--aardvark"),
        ),
    ],
)
def test_duplicate_names_warning(runner, opts_one, opts_two):
    @click.command()
    @click.option(*opts_one)
    @click.option(*opts_two)
    def cli(one, two):
        pass

    with pytest.warns(UserWarning):
        runner.invoke(cli, [])

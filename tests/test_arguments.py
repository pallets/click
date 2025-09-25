import sys
from unittest import mock

import pytest

import click
from click._utils import UNSET


def test_nargs_star(runner):
    @click.command()
    @click.argument("src", nargs=-1)
    @click.argument("dst")
    def copy(src, dst):
        click.echo(f"src={'|'.join(src)}")
        click.echo(f"dst={dst}")

    result = runner.invoke(copy, ["foo.txt", "bar.txt", "dir"])
    assert not result.exception
    assert result.output.splitlines() == ["src=foo.txt|bar.txt", "dst=dir"]


def test_nargs_tup(runner):
    @click.command()
    @click.argument("name", nargs=1)
    @click.argument("point", nargs=2, type=click.INT)
    def copy(name, point):
        click.echo(f"name={name}")
        x, y = point
        click.echo(f"point={x}/{y}")

    result = runner.invoke(copy, ["peter", "1", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter", "point=1/2"]


@pytest.mark.parametrize(
    "opts",
    [
        dict(type=(str, int)),
        dict(type=click.Tuple([str, int])),
        dict(nargs=2, type=click.Tuple([str, int])),
        dict(nargs=2, type=(str, int)),
    ],
)
def test_nargs_tup_composite(runner, opts):
    @click.command()
    @click.argument("item", **opts)
    def copy(item):
        name, id = item
        click.echo(f"name={name} id={id:d}")

    result = runner.invoke(copy, ["peter", "1"])
    assert result.exception is None
    assert result.output.splitlines() == ["name=peter id=1"]


def test_nargs_mismatch_with_tuple_type():
    with pytest.raises(ValueError, match="nargs.*must be 2.*but it was 3"):

        @click.command()
        @click.argument("test", type=(str, int), nargs=3)
        def cli(_):
            pass


def test_nargs_err(runner):
    @click.command()
    @click.argument("x")
    def copy(x):
        click.echo(x)

    result = runner.invoke(copy, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(copy, ["foo", "bar"])
    assert result.exit_code == 2
    assert "Got unexpected extra argument (bar)" in result.output


def test_bytes_args(runner, monkeypatch):
    @click.command()
    @click.argument("arg")
    def from_bytes(arg):
        assert isinstance(arg, str), (
            "UTF-8 encoded argument should be implicitly converted to Unicode"
        )

    # Simulate empty locale environment variables
    monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "utf-8")
    monkeypatch.setattr(sys, "getdefaultencoding", lambda: "utf-8")
    # sys.stdin.encoding is readonly, needs some extra effort to patch.
    stdin = mock.Mock(wraps=sys.stdin)
    stdin.encoding = "utf-8"
    monkeypatch.setattr(sys, "stdin", stdin)

    runner.invoke(
        from_bytes,
        ["Something outside of ASCII range: 林".encode()],
        catch_exceptions=False,
    )


def test_file_args(runner):
    @click.command()
    @click.argument("input", type=click.File("rb"))
    @click.argument("output", type=click.File("wb"))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

    with runner.isolated_filesystem():
        result = runner.invoke(inout, ["-", "hello.txt"], input="Hey!")
        assert result.output == ""
        assert result.exit_code == 0
        with open("hello.txt", "rb") as f:
            assert f.read() == b"Hey!"

        result = runner.invoke(inout, ["hello.txt", "-"])
        assert result.output == "Hey!"
        assert result.exit_code == 0


def test_path_allow_dash(runner):
    @click.command()
    @click.argument("input", type=click.Path(allow_dash=True))
    def foo(input):
        click.echo(input)

    result = runner.invoke(foo, ["-"])
    assert result.output == "-\n"
    assert result.exit_code == 0


def test_file_atomics(runner):
    @click.command()
    @click.argument("output", type=click.File("wb", atomic=True))
    def inout(output):
        output.write(b"Foo bar baz\n")
        output.flush()
        with open(output.name, "rb") as f:
            old_content = f.read()
            assert old_content == b"OLD\n"

    with runner.isolated_filesystem():
        with open("foo.txt", "wb") as f:
            f.write(b"OLD\n")
        result = runner.invoke(inout, ["foo.txt"], input="Hey!", catch_exceptions=False)
        assert result.output == ""
        assert result.exit_code == 0
        with open("foo.txt", "rb") as f:
            assert f.read() == b"Foo bar baz\n"


def test_stdout_default(runner):
    @click.command()
    @click.argument("output", type=click.File("w"), default="-")
    def inout(output):
        output.write("Foo bar baz\n")
        output.flush()

    result = runner.invoke(inout, [])
    assert not result.exception
    assert result.output == "Foo bar baz\n"
    assert result.stdout == "Foo bar baz\n"
    assert not result.stderr


@pytest.mark.parametrize(
    ("nargs", "value", "expect"),
    [
        (2, "", None),
        (2, "a", "Takes 2 values but 1 was given."),
        (2, "a b", ("a", "b")),
        (2, "a b c", "Takes 2 values but 3 were given."),
        (-1, "a b c", ("a", "b", "c")),
        (-1, "", ()),
    ],
)
def test_nargs_envvar(runner, nargs, value, expect):
    if nargs == -1:
        param = click.argument("arg", envvar="X", nargs=nargs)
    else:
        param = click.option("--arg", envvar="X", nargs=nargs)

    @click.command()
    @param
    def cmd(arg):
        return arg

    result = runner.invoke(cmd, env={"X": value}, standalone_mode=False)

    if isinstance(expect, str):
        assert isinstance(result.exception, click.BadParameter)
        assert expect in result.exception.format_message()
    else:
        assert result.return_value == expect


def test_nargs_envvar_only_if_values_empty(runner):
    @click.command()
    @click.argument("arg", envvar="X", nargs=-1)
    def cli(arg):
        return arg

    result = runner.invoke(cli, ["a", "b"], standalone_mode=False)
    assert result.return_value == ("a", "b")

    result = runner.invoke(cli, env={"X": "a"}, standalone_mode=False)
    assert result.return_value == ("a",)


def test_empty_nargs(runner):
    @click.command()
    @click.argument("arg", nargs=-1)
    def cmd(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert result.output == "arg:\n"

    @click.command()
    @click.argument("arg", nargs=-1, required=True)
    def cmd2(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd2, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG...'" in result.output


def test_missing_arg(runner):
    @click.command()
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'." in result.output


@pytest.mark.parametrize(
    ("value", "expect_missing", "processed_value"),
    [
        # Unspecified type of the argument fallback to string, so everything is
        # processed the click.STRING type.
        ("", False, ""),
        ("  ", False, "  "),
        ("foo", False, "foo"),
        ("12", False, "12"),
        (12, False, "12"),
        (12.1, False, "12.1"),
        (list(), False, "[]"),
        (tuple(), False, "()"),
        (set(), False, "set()"),
        (frozenset(), False, "frozenset()"),
        (dict(), False, "{}"),
        # None is a value that is allowed to be processed by a required argument
        # because at this stage, the process_value method happens after the default is
        # applied.
        (None, False, None),
        # An UNSET required argument will raise MissingParameter.
        (UNSET, True, None),
    ],
)
def test_required_argument(value, expect_missing, processed_value):
    """Test how a required argument is processing the provided values."""
    ctx = click.Context(click.Command(""))
    argument = click.Argument(["a"], required=True)

    if expect_missing:
        with pytest.raises(click.MissingParameter) as excinfo:
            argument.process_value(ctx, value)
        assert str(excinfo.value) == "Missing parameter: a"

    else:
        value = argument.process_value(ctx, value)
        assert value == processed_value


def test_implicit_non_required(runner):
    @click.command()
    @click.argument("f", default="test")
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "test\n"


def test_deprecated_usage(runner):
    @click.command()
    @click.argument("f", required=False, deprecated=True)
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "[F!]" in result.output


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_warning(runner, deprecated):
    @click.command()
    @click.argument(
        "my-argument", required=False, deprecated=deprecated, default="default argument"
    )
    def cli(my_argument: str):
        click.echo(f"{my_argument}")

    # defaults should not give a deprecated warning
    result = runner.invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "is deprecated" not in result.output

    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0, result.output
    assert "argument 'MY_ARGUMENT' is deprecated" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_deprecated_required(runner):
    with pytest.raises(ValueError, match="is deprecated and still required"):
        click.Argument(["a"], required=True, deprecated=True)


def test_eat_options(runner):
    @click.command()
    @click.option("-f")
    @click.argument("files", nargs=-1)
    def cmd(f, files):
        for filename in files:
            click.echo(filename)
        click.echo(f)

    result = runner.invoke(cmd, ["--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", ""]

    result = runner.invoke(cmd, ["-f", "-x", "--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", "-x"]


def test_nargs_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c")
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c"])
    assert result.output.splitlines() == ["('a',)", "b", "c"]


def test_nargs_specified_plus_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c", nargs=2)
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c", "d", "e", "f"])
    assert result.output.splitlines() == ["('a', 'b', 'c')", "d", "('e', 'f')"]


@pytest.mark.parametrize(
    ("argument_params", "args", "expected"),
    [
        # Any iterable with the same number of arguments as nargs is valid.
        [{"nargs": 2, "default": (1, 2)}, [], (1, 2)],
        [{"nargs": 2, "default": (1.1, 2.2)}, [], (1, 2)],
        [{"nargs": 2, "default": ("1", "2")}, [], (1, 2)],
        [{"nargs": 2, "default": (None, None)}, [], (None, None)],
        [{"nargs": 2, "default": [1, 2]}, [], (1, 2)],
        [{"nargs": 2, "default": {1, 2}}, [], (1, 2)],
        [{"nargs": 2, "default": frozenset([1, 2])}, [], (1, 2)],
        [{"nargs": 2, "default": {1: "a", 2: "b"}}, [], (1, 2)],
        # Empty iterable is valid if default is None.
        [{"nargs": 2, "default": None}, [], None],
        # Arguments overrides the default.
        [{"nargs": 2, "default": (1, 2)}, ["3", "4"], (3, 4)],
        # Unbounded arguments are allowed to have a default.
        # See: https://github.com/pallets/click/issues/2164
        [{"nargs": -1, "default": [42]}, [], (42,)],
        [{"nargs": -1, "default": None}, [], ()],
        [{"nargs": -1, "default": {1, 2, 3, 4, 5}}, [], (1, 2, 3, 4, 5)],
    ],
)
def test_good_defaults_for_nargs(runner, argument_params, args, expected):
    @click.command()
    @click.argument("a", type=int, **argument_params)
    def cmd(a):
        click.echo(repr(a), nl=False)

    result = runner.invoke(cmd, args)
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("default", "message"),
    [
        # Non-iterables defaults.
        ["Yo", "Error: Invalid value for '[A]...': Value must be an iterable."],
        ["", "Error: Invalid value for '[A]...': Value must be an iterable."],
        [True, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [False, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [12, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [7.9, "Error: Invalid value for '[A]...': Value must be an iterable."],
        # Generator default.
        [(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        # Unset default.
        [UNSET, "Error: Missing argument 'A...'."],
        # Tuples defaults with wrong length.
        [
            tuple(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [(1,), "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            (1, 2, 3),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Lists defaults with wrong length.
        [list(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [[1], "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            [1, 2, 3],
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Sets defaults with wrong length.
        [set(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            set([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            set([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Frozensets defaults with wrong length.
        [
            frozenset(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [
            frozenset([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            frozenset([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Dictionaries defaults with wrong length.
        [dict(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            {1: "a"},
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            {1: "a", 2: "b", 3: "c"},
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
    ],
)
def test_bad_defaults_for_nargs(runner, default, message):
    """Some defaults are not valid when nargs is set."""

    @click.command()
    @click.argument("a", nargs=2, type=int, default=default)
    def cmd(a):
        click.echo(repr(a))

    result = runner.invoke(cmd, [])
    assert message in result.stderr


def test_multiple_param_decls_not_allowed(runner):
    with pytest.raises(TypeError):

        @click.command()
        @click.argument("x", click.Choice(["a", "b"]))
        def copy(x):
            click.echo(x)


def test_multiple_not_allowed():
    with pytest.raises(TypeError, match="multiple"):
        click.Argument(["a"], multiple=True)


def test_subcommand_help(runner):
    @click.group()
    @click.argument("name")
    @click.argument("val")
    @click.option("--opt")
    @click.pass_context
    def cli(ctx, name, val, opt):
        ctx.obj = dict(name=name, val=val)

    @cli.command()
    @click.pass_obj
    def cmd(obj):
        click.echo(f"CMD for {obj['name']} with value {obj['val']}")

    result = runner.invoke(cli, ["foo", "bar", "cmd", "--help"])
    assert not result.exception
    assert "Usage: cli NAME VAL cmd [OPTIONS]" in result.output


def test_nested_subcommand_help(runner):
    @click.group()
    @click.argument("arg1")
    @click.option("--opt1")
    def cli(arg1, opt1):
        pass

    @cli.group()
    @click.argument("arg2")
    @click.option("--opt2")
    def cmd(arg2, opt2):
        pass

    @cmd.command()
    def subcmd():
        click.echo("subcommand")

    result = runner.invoke(cli, ["arg1", "cmd", "arg2", "subcmd", "--help"])
    assert not result.exception
    assert "Usage: cli ARG1 cmd ARG2 subcmd [OPTIONS]" in result.output


def test_when_argument_decorator_is_used_multiple_times_cls_is_preserved():
    class CustomArgument(click.Argument):
        pass

    reusable_argument = click.argument("art", cls=CustomArgument)

    @click.command()
    @reusable_argument
    def foo(arg):
        pass

    @click.command()
    @reusable_argument
    def bar(arg):
        pass

    assert isinstance(foo.params[0], CustomArgument)
    assert isinstance(bar.params[0], CustomArgument)


@pytest.mark.parametrize(
    "args_one,args_two",
    [
        (
            ("aardvark",),
            ("aardvark",),
        ),
    ],
)
def test_duplicate_names_warning(runner, args_one, args_two):
    @click.command()
    @click.argument(*args_one)
    @click.argument(*args_two)
    def cli(one, two):
        pass

    with pytest.warns(UserWarning):
        runner.invoke(cli, [])


@pytest.mark.parametrize(
    ("argument_kwargs", "pass_argv"),
    (
        # there is a large potential parameter space to explore here
        # this is just a very small sample of it
        ({}, ["myvalue"]),
        ({"nargs": -1}, []),
        ({"nargs": -1}, ["myvalue"]),
        ({"default": None}, ["myvalue"]),
        ({"required": False}, []),
        ({"required": False}, ["myvalue"]),
    ),
)
def test_argument_custom_class_can_override_type_cast_value_and_never_sees_unset(
    runner, argument_kwargs, pass_argv
):
    """
    Test that overriding type_cast_value is supported

    In particular, the argument is never passed an UNSET sentinel value.
    """

    class CustomArgument(click.Argument):
        def type_cast_value(self, ctx, value):
            assert value is not UNSET
            return value

    @click.command()
    @click.argument("myarg", **argument_kwargs, cls=CustomArgument)
    def cmd(myarg):
        click.echo("ok")

    result = runner.invoke(cmd, pass_argv)
    assert not result.exception
    assert result.exit_code == 0

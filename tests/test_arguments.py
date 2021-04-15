import sys

import pytest

import click


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


def test_argument_unbounded_nargs_cant_have_default(runner):
    with pytest.raises(TypeError, match="nargs=-1"):

        @click.command()
        @click.argument("src", nargs=-1, default=["42"])
        def copy(src):
            pass


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


def test_nargs_tup_composite(runner):
    variations = [
        dict(type=(str, int)),
        dict(type=click.Tuple([str, int])),
        dict(nargs=2, type=click.Tuple([str, int])),
        dict(nargs=2, type=(str, int)),
    ]

    for opts in variations:

        @click.command()
        @click.argument("item", **opts)
        def copy(item):
            name, id = item
            click.echo(f"name={name} id={id:d}")

        result = runner.invoke(copy, ["peter", "1"])
        assert not result.exception
        assert result.output.splitlines() == ["name=peter id=1"]


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
        assert isinstance(
            arg, str
        ), "UTF-8 encoded argument should be implicitly converted to Unicode"

    # Simulate empty locale environment variables
    monkeypatch.setattr(sys.stdin, "encoding", "utf-8")
    monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "utf-8")
    monkeypatch.setattr(sys, "getdefaultencoding", lambda: "utf-8")

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


def test_path_args(runner):
    @click.command()
    @click.argument("input", type=click.Path(dir_okay=False, allow_dash=True))
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


def test_missing_argument_string_cast():
    ctx = click.Context(click.Command(""))

    with pytest.raises(click.MissingParameter) as excinfo:
        click.Argument(["a"], required=True).process_value(ctx, None)

    assert str(excinfo.value) == "Missing parameter: a"


def test_implicit_non_required(runner):
    @click.command()
    @click.argument("f", default="test")
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "test\n"


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


def test_defaults_for_nargs(runner):
    @click.command()
    @click.argument("a", nargs=2, type=int, default=(1, 2))
    def cmd(a):
        x, y = a
        click.echo(x + y)

    result = runner.invoke(cmd, [])
    assert result.output.strip() == "3"

    result = runner.invoke(cmd, ["3", "4"])
    assert result.output.strip() == "7"

    result = runner.invoke(cmd, ["3"])
    assert result.exception is not None
    assert "Argument 'a' takes 2 values." in result.output


def test_multiple_param_decls_not_allowed(runner):
    with pytest.raises(TypeError):

        @click.command()
        @click.argument("x", click.Choice(["a", "b"]))
        def copy(x):
            click.echo(x)


def test_multiple_not_allowed():
    with pytest.raises(TypeError, match="multiple"):
        click.Argument(["a"], multiple=True)


@pytest.mark.parametrize("value", [(), ("a",), ("a", "b", "c")])
def test_nargs_bad_default(runner, value):
    with pytest.raises(ValueError, match="nargs=2"):
        click.Argument(["a"], nargs=2, default=value)


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

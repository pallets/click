import os
import sys
from io import BytesIO
from pathlib import Path

import pytest

import click
from click.exceptions import ClickException
from click.testing import CliRunner


def test_runner():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\n"


def test_echo_stdin_stream():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_echo_stdin_prompts():
    @click.command()
    def test_python_input():
        foo = input("Foo: ")
        click.echo(f"foo={foo}")

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test_python_input, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: bar bar\nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True)
    def test_prompt(foo):
        click.echo(f"foo={foo}")

    result = runner.invoke(test_prompt, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: bar bar\nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True, hide_input=True)
    def test_hidden_prompt(foo):
        click.echo(f"foo={foo}")

    result = runner.invoke(test_hidden_prompt, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: \nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True)
    @click.option("--bar", prompt=True)
    def test_multiple_prompts(foo, bar):
        click.echo(f"foo={foo}, bar={bar}")

    result = runner.invoke(test_multiple_prompts, input="one\ntwo\n")
    assert not result.exception
    assert result.output == "Foo: one\nBar: two\nfoo=one, bar=two\n"


def test_runner_with_stream():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input=BytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input=BytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_prompts():
    @click.command()
    @click.option("--foo", prompt=True)
    def test(foo):
        click.echo(f"foo={foo}")

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: wau wau\nfoo=wau wau\n"

    @click.command()
    @click.option("--foo", prompt=True, hide_input=True)
    def test(foo):
        click.echo(f"foo={foo}")

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: \nfoo=wau wau\n"


def test_getchar():
    @click.command()
    def continue_it():
        click.echo(click.getchar())

    runner = CliRunner()
    result = runner.invoke(continue_it, input="y")
    assert not result.exception
    assert result.output == "y\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(continue_it, input="y")
    assert not result.exception
    assert result.output == "y\n"

    @click.command()
    def getchar_echo():
        click.echo(click.getchar(echo=True))

    runner = CliRunner()
    result = runner.invoke(getchar_echo, input="y")
    assert not result.exception
    assert result.output == "yy\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(getchar_echo, input="y")
    assert not result.exception
    assert result.output == "yy\n"


def test_catch_exceptions():
    class CustomError(Exception):
        pass

    @click.command()
    def cli():
        raise CustomError(1)

    runner = CliRunner()

    result = runner.invoke(cli)
    assert isinstance(result.exception, CustomError)
    assert type(result.exc_info) is tuple
    assert len(result.exc_info) == 3

    with pytest.raises(CustomError):
        runner.invoke(cli, catch_exceptions=False)

    CustomError = SystemExit

    result = runner.invoke(cli)
    assert result.exit_code == 1


def test_catch_exceptions_cli_runner():
    """Test that invoke `catch_exceptions` takes the value from CliRunner if not set
    explicitly."""

    class CustomError(Exception):
        pass

    @click.command()
    def cli():
        raise CustomError(1)

    runner = CliRunner(catch_exceptions=False)

    result = runner.invoke(cli, catch_exceptions=True)
    assert isinstance(result.exception, CustomError)
    assert type(result.exc_info) is tuple
    assert len(result.exc_info) == 3

    with pytest.raises(CustomError):
        runner.invoke(cli)


def test_with_color():
    @click.command()
    def cli():
        click.secho("hello world", fg="blue")

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == "hello world\n"
    assert not result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == f"{click.style('hello world', fg='blue')}\n"
    assert not result.exception


def test_with_color_errors():
    class CLIError(ClickException):
        def format_message(self) -> str:
            return click.style(self.message, fg="red")

    @click.command()
    def cli():
        raise CLIError("Red error")

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == "Error: Red error\n"
    assert result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == f"Error: {click.style('Red error', fg='red')}\n"
    assert result.exception


def test_with_color_but_pause_not_blocking():
    @click.command()
    def cli():
        click.pause()

    runner = CliRunner()
    result = runner.invoke(cli, color=True)
    assert not result.exception
    assert result.output == ""


def test_exit_code_and_output_from_sys_exit():
    # See issue #362
    @click.command()
    def cli_string():
        click.echo("hello world")
        sys.exit("error")

    @click.command()
    @click.pass_context
    def cli_string_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit("error")

    @click.command()
    def cli_int():
        click.echo("hello world")
        sys.exit(1)

    @click.command()
    @click.pass_context
    def cli_int_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit(1)

    @click.command()
    def cli_float():
        click.echo("hello world")
        sys.exit(1.0)

    @click.command()
    @click.pass_context
    def cli_float_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit(1.0)

    @click.command()
    def cli_no_error():
        click.echo("hello world")

    runner = CliRunner()

    result = runner.invoke(cli_string)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_string_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_int)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_int_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_float)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_float_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_no_error)
    assert result.exit_code == 0
    assert result.output == "hello world\n"


def test_env():
    @click.command()
    def cli_env():
        click.echo(f"ENV={os.environ['TEST_CLICK_ENV']}")

    runner = CliRunner()

    env_orig = dict(os.environ)
    env = dict(env_orig)
    assert "TEST_CLICK_ENV" not in env
    env["TEST_CLICK_ENV"] = "some_value"
    result = runner.invoke(cli_env, env=env)
    assert result.exit_code == 0
    assert result.output == "ENV=some_value\n"

    assert os.environ == env_orig


def test_stderr():
    @click.command()
    def cli_stderr():
        click.echo("1 - stdout")
        click.echo("2 - stderr", err=True)
        click.echo("3 - stdout")
        click.echo("4 - stderr", err=True)

    runner_mix = CliRunner()
    result_mix = runner_mix.invoke(cli_stderr)

    assert result_mix.output == "1 - stdout\n2 - stderr\n3 - stdout\n4 - stderr\n"
    assert result_mix.stdout == "1 - stdout\n3 - stdout\n"
    assert result_mix.stderr == "2 - stderr\n4 - stderr\n"

    @click.command()
    def cli_empty_stderr():
        click.echo("stdout")

    runner = CliRunner()
    result = runner.invoke(cli_empty_stderr)

    assert result.output == "stdout\n"
    assert result.stdout == "stdout\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "args, expected_output",
    [
        (None, "bar\n"),
        ([], "bar\n"),
        ("", "bar\n"),
        (["--foo", "one two"], "one two\n"),
        ('--foo "one two"', "one two\n"),
    ],
)
def test_args(args, expected_output):
    @click.command()
    @click.option("--foo", default="bar")
    def cli_args(foo):
        click.echo(foo)

    runner = CliRunner()
    result = runner.invoke(cli_args, args=args)
    assert result.exit_code == 0
    assert result.output == expected_output


def test_setting_prog_name_in_extra():
    @click.command()
    def cli():
        click.echo("ok")

    runner = CliRunner()
    result = runner.invoke(cli, prog_name="foobar")
    assert not result.exception
    assert result.output == "ok\n"


def test_command_standalone_mode_returns_value():
    @click.command()
    def cli():
        click.echo("ok")
        return "Hello, World!"

    runner = CliRunner()
    result = runner.invoke(cli, standalone_mode=False)
    assert result.output == "ok\n"
    assert result.return_value == "Hello, World!"
    assert result.exit_code == 0


def test_file_stdin_attrs(runner):
    @click.command()
    @click.argument("f", type=click.File())
    def cli(f):
        click.echo(f.name)
        click.echo(f.mode, nl=False)

    result = runner.invoke(cli, ["-"])
    assert result.output == "<stdin>\nr"


def test_isolated_runner(runner):
    with runner.isolated_filesystem() as d:
        assert os.path.exists(d)

    assert not os.path.exists(d)


def test_isolated_runner_custom_tempdir(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path) as d:
        assert os.path.exists(d)

    assert os.path.exists(d)
    os.rmdir(d)


def test_isolation_stderr_errors():
    """Writing to stderr should escape invalid characters instead of
    raising a UnicodeEncodeError.
    """
    runner = CliRunner()

    with runner.isolation() as (_, err, _):
        click.echo("\udce2", err=True, nl=False)
        assert err.getvalue() == b"\\udce2"


def test_isolation_flushes_unflushed_stderr():
    """An un-flushed write to stderr, as with `print(..., file=sys.stderr)`, will end up
    flushed by the runner at end of invocation.
    """
    runner = CliRunner()

    with runner.isolation() as (_, err, _):
        click.echo("\udce2", err=True, nl=False)
        assert err.getvalue() == b"\\udce2"

    @click.command()
    def cli():
        # set end="", flush=False so that it's totally clear that we won't get any
        # auto-flush behaviors
        print("gyarados gyarados gyarados", file=sys.stderr, end="", flush=False)

    result = runner.invoke(cli)
    assert result.stderr == "gyarados gyarados gyarados"


def test_pathlib_path_in_args_works_with_fix():
    """
    Test that passing pathlib.Path objects to CliRunner.invoke() now works correctly.

    This verifies the fix for: "object of type 'PosixPath' has no len()" when Path
    objects were passed to Click's argument parser instead of strings.

    See: https://github.com/pallets/click/issues/1324
    """

    @click.command()
    @click.argument("path")
    def cmd(path):
        click.echo(f"Path: {path}")

    runner = CliRunner()

    # This should work fine with strings
    result = runner.invoke(cmd, ["/tmp/test"])
    assert result.exit_code == 0
    assert "Path: /tmp/test" in result.output

    # This should now work with Path objects too (automatic conversion)
    test_path = Path("/tmp/test")
    result = runner.invoke(cmd, [test_path])

    # CliRunner should automatically convert Path to string
    assert result.exit_code == 0
    assert result.exception is None
    assert "Path: /tmp/test" in result.output


def test_pathlib_path_string_conversion_works():
    """
    Test that pathlib.Path objects work when converted to strings.

    This demonstrates the correct workaround for the bug.
    """

    @click.command()
    @click.argument("path")
    def cmd(path):
        click.echo(f"Path: {path}")

    runner = CliRunner()
    test_path = Path("/tmp/test")

    # The correct approach: convert Path to string explicitly
    result = runner.invoke(cmd, [str(test_path)])
    assert result.exit_code == 0
    assert "Path: /tmp/test" in result.output


@pytest.mark.parametrize(
    "path_input",
    [
        pytest.param(Path("/tmp/test"), id="absolute"),
        pytest.param(Path("/tmp/test/file.txt"), id="absolute_file"),
        pytest.param(Path("relative/path"), id="relative"),
        pytest.param(Path("."), id="current_dir"),
        pytest.param(Path(".."), id="parent_dir"),
    ],
)
def test_various_pathlib_objects_work_consistently(path_input):
    """
    Test that all types of pathlib.Path objects work consistently with the fix.

    This ensures automatic Path-to-string conversion works for different Path
    object types.
    """

    @click.command()
    @click.argument("path")
    def cmd(path):
        click.echo(f"Path: {path}")

    runner = CliRunner()

    # All Path objects should now work correctly (automatic conversion)
    result = runner.invoke(cmd, [path_input])
    assert result.exit_code == 0
    assert result.exception is None
    assert f"Path: {str(path_input)}" in result.output


def test_direct_parser_still_fails_with_pathlib():
    """
    Test that Click's parser still fails when given Path objects directly.

    This ensures we haven't changed the core parser behavior - only CliRunner
    now handles Path objects gracefully by converting them to strings.
    """
    from click.core import Argument
    from click.core import Context
    from click.parser import _OptionParser

    @click.command()
    @click.argument("path")
    def cmd(path):
        click.echo(f"Path: {path}")

    ctx = Context(cmd)
    parser = _OptionParser(ctx)

    # Add argument to parser
    arg = Argument(["path"])
    arg.add_to_parser(parser, ctx)

    # This should still work with strings
    result = parser.parse_args(["/tmp/test"])
    assert result[0]["path"] == "/tmp/test"

    # This should still fail with Path objects (parser behavior unchanged)
    test_path = Path("/tmp/test")
    with pytest.raises(
        TypeError,
        match=r"('PosixPath' has no length|object of type 'PosixPath' has no len)",
    ):
        parser.parse_args([test_path])

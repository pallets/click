import sys
from io import BytesIO
from io import StringIO

import pytest

import click._termui_impl
import click.utils
from click._compat import WIN


def test_echo(runner):
    with runner.isolation() as outstreams:
        click.echo("\N{SNOWMAN}")
        click.echo(b"\x44\x44")
        click.echo(42, nl=False)
        click.echo(b"a", nl=False)
        click.echo("\x1b[31mx\x1b[39m", nl=False)
        bytes = outstreams[0].getvalue().replace(b"\r\n", b"\n")
        assert bytes == b"\xe2\x98\x83\nDD\n42ax"

    # if wrapped, we expect bytes to survive.
    @click.command()
    def cli():
        click.echo(b"\xf6")

    result = runner.invoke(cli, [])
    assert result.stdout_bytes == b"\xf6\n"

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        click.echo(bytearray(b"\x1b[31mx\x1b[39m"), nl=False)
        assert outstreams[0].getvalue() == b"\x1b[31mx\x1b[39m"


def test_echo_custom_file():
    f = StringIO()
    click.echo("hello", file=f)
    assert f.getvalue() == "hello\n"

    b = BytesIO()
    click.echo(b"", b)
    assert b.getvalue() == b"\n"


def test_echo_no_streams(monkeypatch, runner):
    """echo should not fail when stdout and stderr are None with pythonw on Windows."""
    with runner.isolation():
        sys.stdout = None
        sys.stderr = None
        click.echo("test")
        click.echo("test", err=True)


def test_echo_with_capsys(capsys):
    click.echo("Capture me.")
    out, err = capsys.readouterr()
    assert out == "Capture me.\n"


def test_echo_color_flag(monkeypatch, capfd):
    isatty = True
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)

    text = "foo"
    styled_text = click.style(text, fg="red")
    assert styled_text == "\x1b[31mfoo\x1b[0m"

    click.echo(styled_text, color=False)
    out, err = capfd.readouterr()
    assert out == f"{text}\n"

    click.echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    click.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    isatty = False
    click.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == f"{text}\n"

    click.echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"


def test_echo_force_color(monkeypatch, capfd):
    monkeypatch.setattr(click._compat, "isatty", lambda x: False)

    text = "foo"
    styled_text = click.style(text, fg="red")

    # Default without FORCE_COLOR on non-tty strips color
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("PYTHON_COLORS", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{text}\n"

    # FORCE_COLOR=1 forces color
    monkeypatch.setenv("FORCE_COLOR", "1")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{styled_text}\n"

    # FORCE_COLOR=true forces color
    monkeypatch.setenv("FORCE_COLOR", "true")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{styled_text}\n"

    # FORCE_COLOR=0 disables color
    monkeypatch.setenv("FORCE_COLOR", "0")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{text}\n"

    # PYTHON_COLORS=1 forces color
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("PYTHON_COLORS", "1")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{styled_text}\n"

    # PYTHON_COLORS=0 disables color
    monkeypatch.setenv("PYTHON_COLORS", "0")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{text}\n"

    # Explicit color=False overrides FORCE_COLOR=1
    monkeypatch.setenv("FORCE_COLOR", "1")
    click.echo(styled_text, color=False)
    out, _ = capfd.readouterr()
    assert out == f"{text}\n"


def test_echo_no_color(monkeypatch, capfd):
    monkeypatch.setattr(click._compat, "isatty", lambda x: True)

    text = "foo"
    styled_text = click.style(text, fg="red")

    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("PYTHON_COLORS", raising=False)

    # NO_COLOR=1 strips color even on TTY
    monkeypatch.setenv("NO_COLOR", "1")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{text}\n"

    # NO_COLOR="" (empty) does not disable color
    monkeypatch.setenv("NO_COLOR", "")
    click.echo(styled_text)
    out, _ = capfd.readouterr()
    assert out == f"{styled_text}\n"

    # Explicit color=True overrides NO_COLOR
    monkeypatch.setenv("NO_COLOR", "1")
    click.echo(styled_text, color=True)
    out, _ = capfd.readouterr()
    assert out == f"{styled_text}\n"


def test_echo_runner_env_color(runner):
    @click.command()
    def cli():
        click.echo(click.style("hello", fg="green"))

    # Default runner has no color
    result = runner.invoke(cli)
    assert result.output == "hello\n"

    # FORCE_COLOR=1 enables color in runner
    result = runner.invoke(cli, env={"FORCE_COLOR": "1"})
    assert result.output == f"{click.style('hello', fg='green')}\n"

    # NO_COLOR=1 disables color in runner even if runner color=True
    result = runner.invoke(cli, color=True, env={"NO_COLOR": "1"})
    assert result.output == "hello\n"


@pytest.mark.skipif(WIN, reason="Test too complex to make work windows.")
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        monkeypatch.setattr(sys, "stdin", StringIO(text))

    click.echo("Echo to standard output")
    out, err = capfd.readouterr()
    assert out == "Echo to standard output\n"
    assert err == ""

    click.echo("Echo to standard error", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Echo to standard error\n"

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin: "
    assert err == ""

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stdin with no suffix", prompt_suffix="")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin with no suffix"
    assert err == ""

    # On non-Windows the full prompt goes through redirect_stdout so
    # nothing leaks to stdout when err=True.
    # https://github.com/pallets/click/issues/2968
    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr: "

    # https://github.com/pallets/click/issues/3019
    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr with no suffix"

    emulate_input("y\n")
    click.confirm("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin [y/N]: "
    assert err == ""

    emulate_input("y\n")
    click.confirm("Prompt to stdin with no suffix", prompt_suffix="")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin with no suffix [y/N]"
    assert err == ""

    # https://github.com/pallets/click/issues/2968
    emulate_input("y\n")
    click.confirm("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr [y/N]: "

    # https://github.com/pallets/click/issues/3019
    emulate_input("y\n")
    click.confirm("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr with no suffix [y/N]"

    monkeypatch.setattr(click.termui, "isatty", lambda x: True)
    monkeypatch.setattr(click.termui, "getchar", lambda: " ")

    click.pause("Pause to stdout")
    out, err = capfd.readouterr()
    assert out == "Pause to stdout\n"
    assert err == ""

    click.pause("Pause to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Pause to stderr\n"

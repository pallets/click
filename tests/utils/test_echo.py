import sys
from io import StringIO

import pytest

import click
from click import echo
from click._compat import WIN


def test_echo(runner):
    with runner.isolation() as outstreams:
        echo("\N{SNOWMAN}")
        echo(b"\x44\x44")
        echo(42, nl=False)
        echo(b"a", nl=False)
        echo("\x1b[31mx\x1b[39m", nl=False)
        bytes = outstreams[0].getvalue().replace(b"\r\n", b"\n")
        assert bytes == b"\xe2\x98\x83\nDD\n42ax"

    # if wrapped, we expect bytes to survive.
    @click.command()
    def cli():
        echo(b"\xf6")

    result = runner.invoke(cli, [])
    assert result.stdout_bytes == b"\xf6\n"

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        echo(bytearray(b"\x1b[31mx\x1b[39m"), nl=False)
        assert outstreams[0].getvalue() == b"\x1b[31mx\x1b[39m"


def test_echo_color_flag(monkeypatch, capfd):
    isatty = True
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)

    text = "foo"
    styled_text = click.style(text, fg="red")
    assert styled_text == "\x1b[31mfoo\x1b[0m"

    echo(styled_text, color=False)
    out, err = capfd.readouterr()
    assert out == f"{text}\n"

    echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    isatty = True
    echo(styled_text)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    isatty = False
    # Faking isatty() is not enough on Windows;
    # the implementation caches the colorama wrapped stream
    # so we have to use a new stream for each test
    stream = StringIO()
    echo(styled_text, file=stream)
    assert stream.getvalue() == f"{text}\n"

    stream = StringIO()
    echo(styled_text, file=stream, color=True)
    assert stream.getvalue() == f"{styled_text}\n"


def test_echo_custom_file():
    f = StringIO()
    echo("hello", file=f)
    assert f.getvalue() == "hello\n"


def test_echo_no_streams(monkeypatch, runner):
    """echo should not fail when stdout and stderr are None with pythonw on Windows."""
    with runner.isolation():
        sys.stdout = None
        sys.stderr = None
        echo("test")
        echo("test", err=True)


@pytest.mark.skipif(WIN, reason="Test too complex to make work windows.")
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        monkeypatch.setattr(sys, "stdin", StringIO(text))

    echo("Echo to standard output")
    out, err = capfd.readouterr()
    assert out == "Echo to standard output\n"
    assert err == ""

    echo("Echo to standard error", err=True)
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

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == " "
    assert err == "Prompt to stderr:"

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == "x"
    assert err == "Prompt to stderr with no suffi"

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

    emulate_input("y\n")
    click.confirm("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == " "
    assert err == "Prompt to stderr [y/N]:"

    emulate_input("y\n")
    click.confirm("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == "]"
    assert err == "Prompt to stderr with no suffix [y/N"

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


def test_echo_with_capsys(capsys):
    echo("Capture me.")
    out, err = capsys.readouterr()
    assert out == "Capture me.\n"

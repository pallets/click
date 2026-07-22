import sys
from io import StringIO

import pytest

import click
from click._compat import WIN


def test_prompt_cast_default(capfd, monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO("\n"))
    value = click.prompt("value", default="100", type=int)
    capfd.readouterr()
    assert isinstance(value, int)


def test_prompt_default_round_trips_through_type(capfd, monkeypatch):
    """A default that already has the converted value type still passes
    through ``ParamType.convert``, so conversion side effects keep
    applying to defaults."""

    class DoublingType(click.ParamType[int]):
        name = "doubling"

        def convert(self, value, param, ctx):
            return int(value) * 2

    monkeypatch.setattr(sys, "stdin", StringIO("\n"))
    value = click.prompt("value", default=5, type=DoublingType())
    capfd.readouterr()
    assert value == 10


def test_prompt_default_validated_by_type(capfd, monkeypatch):
    """An out-of-range default is rejected by the type's validation and
    prompts again instead of being returned as-is."""
    monkeypatch.setattr(sys, "stdin", StringIO("\n7\n"))
    value = click.prompt("value", default=100, type=click.IntRange(0, 10))
    capfd.readouterr()
    assert value == 7


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
def test_prompts_abort(monkeypatch, capsys):
    def f(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("click.termui.hidden_prompt_func", f)

    try:
        click.prompt("Password", hide_input=True)
    except click.Abort:
        click.echo("interrupted")

    out, err = capsys.readouterr()
    # On non-Windows, prompt is passed directly to getpass, not echoed separately
    assert out == "\ninterrupted\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize(
    ("call", "expected_prompt"),
    [
        (lambda: click.prompt("Name"), "Name: "),
        (lambda: click.prompt("Pw", hide_input=True), "Pw: "),
        (lambda: click.prompt("IP", prompt_suffix="."), "IP."),
        (lambda: click.confirm("OK"), "OK [y/N]: "),
    ],
    ids=["prompt", "prompt-hidden", "prompt-custom-suffix", "confirm"],
)
def test_full_prompt_passed_to_readline(monkeypatch, call, expected_prompt):
    """On non-Windows, prompt and confirm pass the full prompt text to the
    underlying prompt function so readline handles editing correctly.

    https://github.com/pallets/click/issues/2968
    https://github.com/pallets/click/pull/2969
    """
    received = []

    def capture(text):
        received.append(text)
        return "y"

    monkeypatch.setattr("click.termui.visible_prompt_func", capture)
    monkeypatch.setattr("click.termui.hidden_prompt_func", capture)
    call()
    assert received == [expected_prompt]


def test_prompts_eof(runner):
    """If too few lines of input are given, prompt should exit, not hang."""

    @click.command
    def echo():
        for _ in range(3):
            click.echo(click.prompt("", type=int))

    # only provide two lines of input for three prompts
    result = runner.invoke(echo, input="1\n2\n")
    assert result.exit_code == 1

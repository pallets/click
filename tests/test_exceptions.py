import pytest
import click

def test_click_exception_notes(runner):
    @click.command()
    def cli():
        exc = click.ClickException("foo")
        if hasattr(BaseException, "add_note"):
            exc.add_note("bar")
            exc.add_note("baz")
        raise exc

    result = runner.invoke(cli)
    assert result.exit_code == 1
    assert "Error: foo" in result.output
    if hasattr(BaseException, "add_note"):
        assert "bar" in result.output
        assert "baz" in result.output

def test_usage_error_notes(runner):
    @click.command()
    def cli():
        exc = click.UsageError("foo")
        if hasattr(BaseException, "add_note"):
            exc.add_note("bar")
            exc.add_note("baz")
        raise exc

    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: foo" in result.output
    if hasattr(BaseException, "add_note"):
        assert "bar" in result.output
        assert "baz" in result.output

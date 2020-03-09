import pytest

import click
from click._compat import should_strip_ansi
from click._compat import WIN


def test_legacy_callbacks(runner):
    def legacy_callback(ctx, value):
        return value.upper()

    @click.command()
    @click.option("--foo", callback=legacy_callback)
    def cli(foo):
        click.echo(foo)

    with pytest.warns(DeprecationWarning, match="2-arg style"):
        result = runner.invoke(cli, ["--foo", "wat"])
        assert result.exit_code == 0
        assert "WAT" in result.output


def test_bash_func_name():
    from click._bashcomplete import get_completion_script

    script = get_completion_script("foo-bar baz_blah", "_COMPLETE_VAR", "bash").strip()
    assert script.startswith("_foo_barbaz_blah_completion()")
    assert "_COMPLETE_VAR=complete $1" in script


def test_zsh_func_name():
    from click._bashcomplete import get_completion_script

    script = get_completion_script("foo-bar", "_COMPLETE_VAR", "zsh").strip()
    assert script.startswith("#compdef foo-bar")
    assert "compdef _foo_bar_completion foo-bar;" in script
    assert "(( ! $+commands[foo-bar] )) && return 1" in script


@pytest.mark.xfail(WIN, reason="Jupyter not tested/supported on Windows")
def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream(object):
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert not should_strip_ansi(stream=JupyterKernelFakeStream())

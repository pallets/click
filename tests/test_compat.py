import click
import pytest


if click.__version__ >= '3.0':
    def test_legacy_callbacks(runner):
        def legacy_callback(ctx, value):
            return value.upper()

        @click.command()
        @click.option('--foo', callback=legacy_callback)
        def cli(foo):
            click.echo(foo)

        with pytest.warns(Warning, match='Invoked legacy parameter callback'):
            result = runner.invoke(cli, ['--foo', 'wat'])
            assert result.exit_code == 0
            assert 'WAT' in result.output


def test_bash_func_name():
    from click._bashcomplete import get_completion_script
    script = get_completion_script('foo-bar baz_blah', '_COMPLETE_VAR').strip()
    assert script.startswith('_foo_barbaz_blah_completion()')
    assert '_COMPLETE_VAR=complete $1' in script

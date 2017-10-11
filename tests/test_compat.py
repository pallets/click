import pytest

import click


if click.__version__ >= '3.0':
    def test_legacy_callbacks(runner):
        def legacy_callback(ctx, value):
            return value.upper()

        @click.command()
        @click.option('--foo', callback=legacy_callback)
        def cli(foo):
            click.echo(foo)

        with pytest.warns(Warning) as records:
            result = runner.invoke(cli, ['--foo', 'wat'])

        [warning_record] = records
        warning_message = str(warning_record.message)
        assert 'Invoked legacy parameter callback' in warning_message
        assert result.exit_code == 0
        # Depending on the pytest version, the warning message may be
        # in `result.output`.
        #
        # In pytest version 3.1 pytest started capturing warnings by default.
        # See https://docs.pytest.org/en/latest/warnings.html#warnings-capture.
        assert 'WAT' in result.output


def test_bash_func_name():
    from click._bashcomplete import get_completion_script
    script = get_completion_script('foo-bar baz_blah', '_COMPLETE_VAR').strip()
    assert script.startswith('_foo_barbaz_blah_completion()')
    assert '_COMPLETE_VAR=complete $1' in script

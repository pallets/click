import os
import sys

import pytest
import click

from click.testing import CliRunner

from click._compat import PY2, WIN

# Use the most reasonable io that users would use for the python version.
if PY2:
    from cStringIO import StringIO as ReasonableBytesIO
else:
    from io import BytesIO as ReasonableBytesIO


def test_runner():
    @click.command()
    def test():
        i = click.get_binary_stream('stdin')
        o = click.get_binary_stream('stdout')
        while 1:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input='Hello World!\n')
    assert not result.exception
    assert result.output == 'Hello World!\n'

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input='Hello World!\n')
    assert not result.exception
    assert result.output == 'Hello World!\nHello World!\n'


def test_runner_with_stream():
    @click.command()
    def test():
        i = click.get_binary_stream('stdin')
        o = click.get_binary_stream('stdout')
        while 1:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input=ReasonableBytesIO(b'Hello World!\n'))
    assert not result.exception
    assert result.output == 'Hello World!\n'

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input=ReasonableBytesIO(b'Hello World!\n'))
    assert not result.exception
    assert result.output == 'Hello World!\nHello World!\n'


def test_prompts():
    @click.command()
    @click.option('--foo', prompt=True)
    def test(foo):
        click.echo('foo=%s' % foo)

    runner = CliRunner()
    result = runner.invoke(test, input='wau wau\n')
    assert not result.exception
    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'

    @click.command()
    @click.option('--foo', prompt=True, hide_input=True)
    def test(foo):
        click.echo('foo=%s' % foo)

    runner = CliRunner()
    result = runner.invoke(test, input='wau wau\n')
    assert not result.exception
    assert result.output == 'Foo: \nfoo=wau wau\n'


def test_getchar():
    @click.command()
    def continue_it():
        click.echo(click.getchar())

    runner = CliRunner()
    result = runner.invoke(continue_it, input='y')
    assert not result.exception
    assert result.output == 'y\n'


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


@pytest.mark.skipif(WIN, reason='Test does not make sense on Windows.')
def test_with_color():
    @click.command()
    def cli():
        click.secho('hello world', fg='blue')

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == 'hello world\n'
    assert not result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == click.style('hello world', fg='blue') + '\n'
    assert not result.exception


def test_with_color_but_pause_not_blocking():
    @click.command()
    def cli():
        click.pause()

    runner = CliRunner()
    result = runner.invoke(cli, color=True)
    assert not result.exception
    assert result.output == ''


def test_exit_code_and_output_from_sys_exit():
    # See issue #362
    @click.command()
    def cli_string():
        click.echo('hello world')
        sys.exit('error')

    @click.command()
    def cli_int():
        click.echo('hello world')
        sys.exit(1)

    @click.command()
    def cli_float():
        click.echo('hello world')
        sys.exit(1.0)

    @click.command()
    def cli_no_error():
        click.echo('hello world')

    runner = CliRunner()

    result = runner.invoke(cli_string)
    assert result.exit_code == 1
    assert result.output == 'hello world\nerror\n'

    result = runner.invoke(cli_int)
    assert result.exit_code == 1
    assert result.output == 'hello world\n'

    result = runner.invoke(cli_float)
    assert result.exit_code == 1
    assert result.output == 'hello world\n1.0\n'

    result = runner.invoke(cli_no_error)
    assert result.exit_code == 0
    assert result.output == 'hello world\n'


def test_env():
    @click.command()
    def cli_env():
        click.echo('ENV=%s' % os.environ['TEST_CLICK_ENV'])

    runner = CliRunner()

    env_orig = dict(os.environ)
    env = dict(env_orig)
    assert 'TEST_CLICK_ENV' not in env
    env['TEST_CLICK_ENV'] = 'some_value'
    result = runner.invoke(cli_env, env=env)
    assert result.exit_code == 0
    assert result.output == 'ENV=some_value\n'

    assert os.environ == env_orig


def test_stderr():
    @click.command()
    def cli_stderr():
        click.echo("stdout")
        click.echo("stderr", err=True)

    runner = CliRunner(mix_stderr=False)

    result = runner.invoke(cli_stderr)

    assert result.output == 'stdout\n'
    assert result.stdout == 'stdout\n'
    assert result.stderr == 'stderr\n'

    runner_mix = CliRunner(mix_stderr=True)
    result_mix = runner_mix.invoke(cli_stderr)

    assert result_mix.output == 'stdout\nstderr\n'
    assert result_mix.stdout == 'stdout\nstderr\n'

    with pytest.raises(ValueError):
        result_mix.stderr


@pytest.mark.parametrize('args, expected_output', [
    (None, 'bar\n'),
    ([], 'bar\n'),
    ('', 'bar\n'),
    (['--foo', 'one two'], 'one two\n'),
    ('--foo "one two"', 'one two\n'),
])
def test_args(args, expected_output):

    @click.command()
    @click.option('--foo', default='bar')
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
    assert result.output == 'ok\n'

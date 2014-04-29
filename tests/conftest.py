import os
import sys
import click
import contextlib

from cStringIO import StringIO

import pytest


class EchoingStdin(object):

    def __init__(self, input, output):
        self._input = input
        self._output = output

    def __getattr__(self, x):
        return getattr(self._input, x)

    def _echo(self, rv):
        mark = False
        if rv.endswith('\xff'):
            rv = rv[:-1]
            mark = True
        self._output.write(rv)
        if mark:
            self._output.write('^D\n')
        return rv

    def read(self, n=-1):
        return self._echo(self._input.read(n))

    def readline(self, n=-1):
        return self._echo(self._input.readline(n))

    def readlines(self):
        return [self._echo(x) for x in self._input.readlines()]

    def __iter__(self):
        return iter(self._echo(x) for x in self._input)


class Result(object):

    def __init__(self, output, exit_code, exception):
        self.output = output
        self.exit_code = exit_code
        self.exception = exception

    @property
    def okay(self):
        return self.exception is None


class CliRunner(object):

    @contextlib.contextmanager
    def isolation(self, input=None, env=None):
        if isinstance(input, unicode):
            input = input.encode('utf-8')
        input = StringIO(input or '')
        output = StringIO()
        sys.stdin = EchoingStdin(input, output)
        sys.stdin.encoding = 'utf-8'

        def visible_input(prompt=None):
            sys.stdout.write(prompt or '')
            val = input.readline().rstrip('\r\n')
            sys.stdout.write(val + '\n')
            sys.stdout.flush()
            return val

        def hidden_input(prompt=None):
            sys.stdout.write((prompt or '') + '\n')
            sys.stdout.flush()
            return input.readline().rstrip('\r\n')

        old_stdout = sys.stdout
        sys.stdout = output
        old_stderr = sys.stderr
        sys.stderr = output
        old_visible_prompt_func = click.helpers.visible_prompt_func
        old_hidden_prompt_func = click.helpers.hidden_prompt_func
        click.helpers.visible_prompt_func = visible_input
        click.helpers.hidden_prompt_func = hidden_input

        old_env = {}
        try:
            if env:
                for key, value in env.iteritems():
                    old_env[key] = os.environ.get(value)
                    os.environ[key] = value
            yield output
        finally:
            for key, value in old_env.iteritems():
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            click.helpers.visible_prompt_func = old_visible_prompt_func
            click.helpers.hidden_prompt_func = old_hidden_prompt_func

    def invoke(self, cli, args):
        with self.isolation() as out:
            exception = None
            exit_code = 0

            try:
                cli.main(args=args, prog_name=cli.name or 'root')
            except SystemExit as e:
                if e.code != 0:
                    exception = e
                exit_code = e.code
            except Exception as e:
                exception = e
                exit_code = -1
            output = out.getvalue().decode('utf-8')

        return Result(output=output, exit_code=exit_code,
                      exception=exception)


@pytest.fixture(scope='function')
def runner(request):
    return CliRunner()

import os
import sys
import click
import shutil
import tempfile
import contextlib

import pytest

PY2 = sys.version_info[0] == 2
if PY2:
    from cStringIO import StringIO
    iteritems = lambda x: x.iteritems()
else:
    import io
    iteritems = lambda x: iter(x.items())


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


class CliRunner(object):

    @contextlib.contextmanager
    def isolation(self, input=None, env=None):
        if input is not None and not isinstance(input, bytes):
            input = input.encode('utf-8')

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        if PY2:
            input = StringIO(input or '')
            output = StringIO()
            sys.stdin = EchoingStdin(input, output)
            sys.stdin.encoding = 'utf-8'
            sys.stdout = sys.stderr = output
        else:
            real_input = io.BytesIO(input)
            output = io.BytesIO()
            input = io.TextIOWrapper(real_input, encoding='utf-8')
            sys.stdin = EchoingStdin(real_input, output)
            sys.stdout = sys.stderr = io.TextIOWrapper(output,
                                                       encoding='utf-8')

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

        old_visible_prompt_func = click.termui.visible_prompt_func
        old_hidden_prompt_func = click.termui.hidden_prompt_func
        click.termui.visible_prompt_func = visible_input
        click.termui.hidden_prompt_func = hidden_input

        old_env = {}
        try:
            if env:
                for key, value in iteritems(env):
                    old_env[key] = os.environ.get(value)
                    os.environ[key] = value
            yield output
        finally:
            for key, value in iteritems(old_env):
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            click.termui.visible_prompt_func = old_visible_prompt_func
            click.termui.hidden_prompt_func = old_hidden_prompt_func

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
            output = out.getvalue().decode('utf-8').replace('\r\n', '\n')

        return Result(output=output, exit_code=exit_code,
                      exception=exception)

    @contextlib.contextmanager
    def isolated_filesystem(self):
        cwd = os.getcwd()
        t = tempfile.mkdtemp()
        os.chdir(t)
        try:
            yield
        finally:
            os.chdir(cwd)
            try:
                shutil.rmtree(t)
            except (OSError, IOError):
                pass


@pytest.fixture(scope='function')
def runner(request):
    return CliRunner()

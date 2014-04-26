import os
import sys
import click
import shutil
import tempfile
import contextlib

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from docutils import nodes
from docutils.statemachine import ViewList

from sphinx.domains import Domain
from sphinx.util.compat import Directive


class EchoingStdin(object):

    def __init__(self, input, output):
        self._input = input
        self._output = output

    def __getattr__(self, x):
        return getattr(self._input, x)

    def read(self, n=-1):
        rv = self._input.read(n)
        self._output.write(rv)
        return rv

    def readline(self, n=-1):
        rv = self._input.readline(n)
        self._output.write(rv)
        return rv

    def readlines(self):
        rv = self._input.readlines()
        for line in rv:
            self._output.write(rv)
        return rv

    def __iter__(self):
        for x in self._input:
            self._output.write(x)
            yield x


@contextlib.contextmanager
def isolation(input=None, env=None):
    if click.PY2 and isinstance(input, unicode):
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

    sys.stdout = output
    sys.stderr = output
    old_visible_prompt_func = click.visible_prompt_func
    old_hidden_prompt_func = click.hidden_prompt_func
    click.visible_prompt_func = visible_input
    click.hidden_prompt_func = hidden_input

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
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        click.visible_prompt_func = old_visible_prompt_func
        click.hidden_prompt_func = old_hidden_prompt_func


@contextlib.contextmanager
def isolated_filesystem():
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


class ExampleRunner(object):

    def __init__(self):
        self.namespace = {
            'click': click,
        }

    def declare(self, source):
        code = compile(source, '<docs>', 'exec')
        eval(code, self.namespace)

    def run(self, source):
        code = compile(source, '<docs>', 'exec')
        buffer = []

        def invoke(cmd, args=None, prog_name=None, prog_prefix='python ',
                   input=None, env=None, auto_envvar_prefix=None):
            if env:
                for key, value in sorted(env.items()):
                    if ' ' in value:
                        value = '"%s"' % value
                    buffer.append('$ export %s=%s' % (key, value))
            args = args or []
            if prog_name is None:
                prog_name = cmd.name.replace('_', '-') + '.py'
            buffer.append(('$ %s%s %s' % (
                prog_prefix,
                prog_name,
                ' '.join(('"%s"' % x) if ' ' in x else x for x in args)
            )).rstrip())
            if isinstance(input, (tuple, list)):
                input = '\n'.join(input) + '\n'
            with isolation(input=input, env=env) as output:
                try:
                    cmd.main(args=args, prog_name=prog_name,
                             auto_envvar_prefix=auto_envvar_prefix)
                except SystemExit:
                    pass
                buffer.extend(output.getvalue().splitlines())

        def println(text=''):
            buffer.append(text)

        eval(code, self.namespace, {
            'invoke': invoke,
            'println': println,
            'isolated_filesystem': isolated_filesystem,
        })
        return buffer

    def close(self):
        pass


def parse_rst(state, content_offset, doc):
    node = nodes.section()
    # hack around title style bookkeeping
    surrounding_title_styles = state.memo.title_styles
    surrounding_section_level = state.memo.section_level
    state.memo.title_styles = []
    state.memo.section_level = 0
    state.nested_parse(doc, content_offset, node, match_titles=1)
    state.memo.title_styles = surrounding_title_styles
    state.memo.section_level = surrounding_section_level
    return node.children


def get_example_runner(document):
    runner = getattr(document, 'click_example_runner', None)
    if runner is None:
        runner = document.click_example_runner = ExampleRunner()
    return runner


class ExampleDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        doc = ViewList()
        runner = get_example_runner(self.state.document)
        try:
            runner.declare('\n'.join(self.content))
        except:
            runner.close()
            raise
        doc.append('.. sourcecode:: python', '')
        doc.append('', '')
        for line in self.content:
            doc.append(' ' + line, '')
        return parse_rst(self.state, self.content_offset, doc)


class RunExampleDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        doc = ViewList()
        runner = get_example_runner(self.state.document)
        try:
            rv = runner.run('\n'.join(self.content))
        except:
            runner.close()
            raise
        doc.append('.. sourcecode:: text', '')
        doc.append('', '')
        for line in rv:
            doc.append(' ' + line, '')
        return parse_rst(self.state, self.content_offset, doc)


class ClickDomain(Domain):
    name = 'click'
    label = 'Click'
    directives = {
        'example':  ExampleDirective,
        'run':      RunExampleDirective,
    }


def delete_example_runner_state(app, doctree):
    runner = getattr(doctree, 'click_example_runner', None)
    if runner is not None:
        runner.close()
        del doctree.click_example_runner


def setup(app):
    app.add_domain(ClickDomain)

    app.connect('doctree-read', delete_example_runner_state)

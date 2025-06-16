import contextlib
import shlex
import subprocess
import sys
import tempfile
from functools import partial

import click
from click.testing import CliRunner
from click.testing import EchoingStdin
from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx.domains import Domain


class EofEchoingStdin(EchoingStdin):
    """Like :class:`click.testing.EchoingStdin` but adds a visible
    ``^D`` in place of the EOT character (``\x04``).

    :meth:`ExampleRunner.invoke` adds ``\x04`` when
    ``terminate_input=True``.
    """

    def _echo(self, rv):
        eof = rv[-1] == b"\x04"[0]

        if eof:
            rv = rv[:-1]

        if not self._paused:
            self._output.write(rv)

            if eof:
                self._output.write(b"^D\n")

        return rv


@contextlib.contextmanager
def patch_modules():
    """Patch modules to work better with :meth:`ExampleRunner.invoke`.

    ``subprocess.call` output is redirected to ``click.echo`` so it
    shows up in the example output.
    """
    old_call = subprocess.call

    def dummy_call(*args, **kwargs):
        with tempfile.TemporaryFile("wb+") as f:
            kwargs["stdout"] = f
            kwargs["stderr"] = f
            rv = subprocess.Popen(*args, **kwargs).wait()
            f.seek(0)
            click.echo(f.read().decode("utf-8", "replace").rstrip())
        return rv

    subprocess.call = dummy_call

    try:
        yield
    finally:
        subprocess.call = old_call


class ExampleRunner(CliRunner):
    def __init__(self):
        super().__init__(echo_stdin=True)
        self.namespace = {"click": click, "__file__": "dummy.py"}

    @contextlib.contextmanager
    def isolation(self, *args, **kwargs):
        iso = super().isolation(*args, **kwargs)

        with iso as streams:
            try:
                buffer = sys.stdin.buffer
            except AttributeError:
                buffer = sys.stdin

            # FIXME: We need to replace EchoingStdin with our custom
            # class that outputs "^D". At this point we know sys.stdin
            # has been patched so it's safe to reassign the class.
            # Remove this once EchoingStdin is overridable.
            buffer.__class__ = EofEchoingStdin
            yield streams

    def invoke(
        self,
        cli,
        args=None,
        prog_name=None,
        input=None,
        terminate_input=False,
        env=None,
        _output_lines=None,
        **extra,
    ):
        """Like :meth:`CliRunner.invoke` but displays what the user
        would enter in the terminal for env vars, command args, and
        prompts.

        :param terminate_input: Whether to display "^D" after a list of
            input.
        :param _output_lines: A list used internally to collect lines to
            be displayed.
        """
        output_lines = _output_lines if _output_lines is not None else []

        if env:
            for key, value in sorted(env.items()):
                value = shlex.quote(value)
                output_lines.append(f"$ export {key}={value}")

        args = args or []

        if prog_name is None:
            prog_name = cli.name.replace("_", "-")

        output_lines.append(f"$ {prog_name} {shlex.join(args)}".rstrip())
        # remove "python" from command
        prog_name = prog_name.rsplit(" ", 1)[-1]

        if isinstance(input, (tuple, list)):
            input = "\n".join(input) + "\n"

            if terminate_input:
                input += "\x04"

        result = super().invoke(
            cli=cli, args=args, input=input, env=env, prog_name=prog_name, **extra
        )
        output_lines.extend(result.output.splitlines())
        return result

    def declare_example(self, source):
        """Execute the given code, adding it to the runner's namespace."""
        with patch_modules():
            code = compile(source, "<docs>", "exec")
            exec(code, self.namespace)

    def run_example(self, source):
        """Run commands by executing the given code, returning the lines
        of input and output. The code should be a series of the
        following functions:

        *   :meth:`invoke`: Invoke a command, adding env vars, input,
            and output to the output.
        *   ``println(text="")``: Add a line of text to the output.
        *   :meth:`isolated_filesystem`: A context manager that changes
            to a temporary directory while executing the block.
        """
        code = compile(source, "<docs>", "exec")
        buffer = []
        invoke = partial(self.invoke, _output_lines=buffer)

        def println(text=""):
            buffer.append(text)

        exec(
            code,
            self.namespace,
            {
                "invoke": invoke,
                "println": println,
                "isolated_filesystem": self.isolated_filesystem,
            },
        )
        return buffer

    def close(self):
        """Clean up the runner once the document has been read."""
        pass


def get_example_runner(document):
    """Get or create the :class:`ExampleRunner` instance associated with
    a document.
    """
    runner = getattr(document, "click_example_runner", None)
    if runner is None:
        runner = document.click_example_runner = ExampleRunner()
    return runner


class DeclareExampleDirective(Directive):
    """Add the source contained in the directive's content to the
    document's :class:`ExampleRunner`, to be run using
    :class:`RunExampleDirective`.

    See :meth:`ExampleRunner.declare_example`.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        doc = ViewList()
        runner = get_example_runner(self.state.document)

        try:
            runner.declare_example("\n".join(self.content))
        except BaseException:
            runner.close()
            raise

        doc.append(".. sourcecode:: python", "")
        doc.append("", "")

        for line in self.content:
            doc.append(" " + line, "")

        node = nodes.section()
        self.state.nested_parse(doc, self.content_offset, node)
        return node.children


class RunExampleDirective(Directive):
    """Run commands from :class:`DeclareExampleDirective` and display
    the input and output.

    See :meth:`ExampleRunner.run_example`.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        doc = ViewList()
        runner = get_example_runner(self.state.document)

        try:
            rv = runner.run_example("\n".join(self.content))
        except BaseException:
            runner.close()
            raise

        doc.append(".. sourcecode:: shell-session", "")
        doc.append("", "")

        for line in rv:
            doc.append(" " + line, "")

        node = nodes.section()
        self.state.nested_parse(doc, self.content_offset, node)
        return node.children


class ClickDomain(Domain):
    name = "click"
    label = "Click"
    directives = {"example": DeclareExampleDirective, "run": RunExampleDirective}

    def merge_domaindata(self, docnames, otherdata):
        # Needed to support parallel build.
        # Not using self.data -- nothing to merge.
        pass


def delete_example_runner_state(app, doctree):
    """Close and remove the :class:`ExampleRunner` instance once the
    document has been read.
    """
    runner = getattr(doctree, "click_example_runner", None)

    if runner is not None:
        runner.close()
        del doctree.click_example_runner


def setup(app):
    app.add_domain(ClickDomain)
    app.connect("doctree-read", delete_example_runner_state)

import click

from click.testing import CliRunner

from click._compat import PY2

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

import click

from click.testing import CLIRunner

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

    runner = CLIRunner()
    result = runner.invoke(test, input='Hello World!\n')
    assert not result.exception
    assert result.output == 'Hello World!\n'

    runner = CLIRunner(echo_stdin=True)
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

    runner = CLIRunner()
    result = runner.invoke(test, input=ReasonableBytesIO(b'Hello World!\n'))
    assert not result.exception
    assert result.output == 'Hello World!\n'

    runner = CLIRunner(echo_stdin=True)
    result = runner.invoke(test, input=ReasonableBytesIO(b'Hello World!\n'))
    assert not result.exception
    assert result.output == 'Hello World!\nHello World!\n'


def test_prompts():
    @click.command()
    @click.option('--foo', prompt=True)
    def test(foo):
        click.echo('foo=%s' % foo)

    runner = CLIRunner()
    result = runner.invoke(test, input='wau wau\n')
    assert not result.exception
    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'

    @click.command()
    @click.option('--foo', prompt=True, hide_input=True)
    def test(foo):
        click.echo('foo=%s' % foo)

    runner = CLIRunner()
    result = runner.invoke(test, input='wau wau\n')
    assert not result.exception
    assert result.output == 'Foo: \nfoo=wau wau\n'


def test_getchar():
    @click.command()
    def continue_it():
        click.echo(click.getchar())

    runner = CLIRunner()
    result = runner.invoke(continue_it, input='y')
    assert not result.exception
    assert result.output == 'y\n'

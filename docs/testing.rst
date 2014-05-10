Testing Click Applications
==========================

.. currentmodule:: click.testing

For basic testing Click provides the :mod:`click.testing` module which
provides test functionality that helps you invoke command line
applications and check their behavior.

These tools really only should be used for testing as they are changing
the whole interpreter state for simplicity and they are not in any way
thread safe!

Basic Testing
-------------

The basic functionality for testing click applications is the
:class:`CliRunner` which can invoke commands as command line scripts.  The
:meth:`CliRunner.invoke` method runs the command line script in isolation
and captures the output as both bytes and binary data.

The return value is a :class:`Result` object which has the captured output
data, exit code and optional exception attached.

Example::

    import click
    from click.testing import CliRunner

    def test_hello_world():
        @click.command()
        @click.argument('name')
        def hello(name):
            click.echo('Hello %s!' % name)

        runner = CliRunner()
        result = runner.invoke(hello, ['Peter'])
        assert result.exit_code == 0
        assert result.output == 'Hello Peter!\n'

File System Isolation
---------------------

For basic command line tools that want to operate with the file system the
:meth:`CliRunner.isolated_filesystem` method comes in useful which sets up
an empty folder and changes the current working directory to.

Example::

    import click
    from click.testing import CliRunner

    def test_hello_world():
        @click.command()
        @click.argument('f', type=click.File())
        def cat(f):
            click.echo(f.read())

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('hello.txt') as f:
                f.write('Hello World!')

            result = runner.invoke(cat, ['hello.txt'])
            assert result.exit_code == 0
            assert result.output == 'Hello World!\n'

Testing Click Applications
==========================

.. currentmodule:: click.testing

For basic testing, Click provides the :mod:`click.testing` module which
provides test functionality that helps you invoke command line
applications and check their behavior.

These tools should really only be used for testing as they change
the entire interpreter state for simplicity and are not in any way
thread-safe!

Basic Testing
-------------

The basic functionality for testing Click applications is the
:class:`CliRunner` which can invoke commands as command line scripts.  The
:meth:`CliRunner.invoke` method runs the command line script in isolation
and captures the output as both bytes and binary data.

The return value is a :class:`Result` object, which has the captured output
data, exit code, and optional exception attached:

.. code-block:: python
   :caption: hello.py

   import click

   @click.command()
   @click.argument('name')
   def hello(name):
      click.echo(f'Hello {name}!')

.. code-block:: python
   :caption: test_hello.py

   from click.testing import CliRunner
   from hello import hello

   def test_hello_world():
     runner = CliRunner()
     result = runner.invoke(hello, ['Peter'])
     assert result.exit_code == 0
     assert result.output == 'Hello Peter!\n'

For subcommand testing, a subcommand name must be specified in the `args` parameter of :meth:`CliRunner.invoke` method:

.. code-block:: python
   :caption: sync.py

   import click

   @click.group()
   @click.option('--debug/--no-debug', default=False)
   def cli(debug):
      click.echo(f"Debug mode is {'on' if debug else 'off'}")

   @cli.command()
   def sync():
      click.echo('Syncing')

.. code-block:: python
   :caption: test_sync.py

   from click.testing import CliRunner
   from sync import cli

   def test_sync():
     runner = CliRunner()
     result = runner.invoke(cli, ['--debug', 'sync'])
     assert result.exit_code == 0
     assert 'Debug mode is on' in result.output
     assert 'Syncing' in result.output

Additional keyword arguments passed to ``.invoke()`` will be used to construct the initial Context object.
For example, if you want to run your tests against a fixed terminal width you can use the following::

    runner = CliRunner()
    result = runner.invoke(cli, ['--debug', 'sync'], terminal_width=60)

File System Isolation
---------------------

For basic command line tools with file system operations, the
:meth:`CliRunner.isolated_filesystem` method is useful for setting the
current working directory to a new, empty folder.

.. code-block:: python
   :caption: cat.py

   import click

   @click.command()
   @click.argument('f', type=click.File())
   def cat(f):
      click.echo(f.read())

.. code-block:: python
   :caption: test_cat.py

   from click.testing import CliRunner
   from cat import cat

   def test_cat():
      runner = CliRunner()
      with runner.isolated_filesystem():
         with open('hello.txt', 'w') as f:
             f.write('Hello World!')

         result = runner.invoke(cat, ['hello.txt'])
         assert result.exit_code == 0
         assert result.output == 'Hello World!\n'

Pass ``temp_dir`` to control where the temporary directory is created.
The directory will not be removed by Click in this case. This is useful
to integrate with a framework like Pytest that manages temporary files.

.. code-block:: python

    def test_keep_dir(tmp_path):
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            ...


Input Streams
-------------

The test wrapper can also be used to provide input data for the input
stream (stdin).  This is very useful for testing prompts, for instance:

.. code-block:: python
   :caption: prompt.py

   import click

   @click.command()
   @click.option('--foo', prompt=True)
   def prompt(foo):
      click.echo(f"foo={foo}")

.. code-block:: python
   :caption: test_prompt.py

   from click.testing import CliRunner
   from prompt import prompt

   def test_prompts():
      runner = CliRunner()
      result = runner.invoke(prompt, input='wau wau\n')
      assert not result.exception
      assert result.output == 'Foo: wau wau\nfoo=wau wau\n'

Note that prompts will be emulated so that they write the input data to
the output stream as well.  If hidden input is expected then this
obviously does not happen.

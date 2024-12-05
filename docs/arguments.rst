.. _arguments:

Arguments
=========

.. currentmodule:: click

Arguments are:

*   Are positional in nature.
*   Similar to a limited version of :ref:`options <options>` that can take an arbitrary number of inputs
*   :ref:`Documented manually <documenting-arguments>`.

Useful and often used kwargs are:

*   ``default``: Passes a default.
*   ``nargs``: Sets the number of arguments. Set to -1 to take an arbitrary number.

Basic Arguments
---------------

A minimal :class:`click.Argument` solely takes one string argument: the name of the argument. This will assume the argument is required, has no default, and is of the type ``str``.

Example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename: str):
        """Print FILENAME."""
        click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, args=['foo.txt'])


An argument may be assigned a :ref:`parameter type <parameter-types>`. If no type is provided, the type of the default value is used. If no default value is provided, the type is assumed to be :data:`STRING`.

.. admonition:: Note on Required Arguments

   It is possible to make an argument required by setting ``required=True``.  It is not recommended since we think command line tools should gracefully degrade into becoming no ops.  We think this because command line tools are often invoked with wildcard inputs and they should not error out if the wildcard is empty.

Multiple Arguments
-----------------------------------

To set the number of argument use the ``nargs`` kwarg. It can be set to any positive integer and -1. Setting it to -1, makes the number of arguments arbitrary (which is called variadic) and can only be used once. The arguments are then packed as a tuple and passed to the function.

.. click:example::

    @click.command()
    @click.argument('src', nargs=1)
    @click.argument('dsts', nargs=-1)
    def copy(src: str, dsts: tuple[str, ...]):
        """Move file SRC to DST."""
        for destination in dsts:
            click.echo(f"Copy {src} to folder {destination}")

And from the command line:

.. click:run::

    invoke(copy, args=['foo.txt', 'usr/david/foo.txt', 'usr/mitsuko/foo.txt'])

.. admonition:: Note on Handling Files

    This is not how you should handle files and files paths. This merely used as a simple example. See :ref:`handling-files` to learn more about how to handle files in parameters.

Argument Escape Sequences
---------------------------

If you want to process arguments that look like options, like a file named ``-foo.txt`` or ``--foo.txt`` , you must pass the ``--`` separator first. After you pass the ``--``, you may only pass arguments. This is a common feature for POSIX command line tools.

Example usage:

.. click:example::

    @click.command()
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['--', '-foo.txt', 'bar.txt'])

If you don't like the ``--`` marker, you can set ignore_unknown_options to True to avoid checking unknown options:

.. click:example::

    @click.command(context_settings={"ignore_unknown_options": True})
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['-foo.txt', 'bar.txt'])


.. _environment-variables:

Environment Variables
---------------------

Arguments can use environment variables. To do so, pass the name(s) of the environment variable(s) via `envvar` in ``click.argument``.

Checking one environment variable:

.. click:example::

    @click.command()
    @click.argument('src', envvar='SRC', type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        # Writing the file in the filesystem.
        with open('hello.txt', 'w') as f:
            f.write('Hello World!')
        invoke(echo, env={'SRC': 'hello.txt'})


Checking multiple environment variables:

.. click:example::

    @click.command()
    @click.argument('src', envvar=['SRC', 'SRC_2'], type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        # Writing the file in the filesystem.
        with open('hello.txt', 'w') as f:
            f.write('Hello World from second variable!')
        invoke(echo, env={'SRC_2': 'hello.txt'})

.. _arguments:

Arguments
=========

.. currentmodule:: click



*   Are positional in nature
*   Are very much like a limited version of :ref:`options <options>`
*   But also can take an arbitrary number of inputs
*   Must be :ref:`documented manually <documenting-arguments>`

Useful and often used kwargs are:

*   ``default`` : Passes a default
*   ``nargs`` : Sets the number of arguments. Set to -1 to take an arbitrary number.

Basic Argument
---------------

A minimal :class:`click.Argument` takes the name of function argument. If you just pass it this, it assumes 1 argument, required, no default and string type.

Example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['foo.txt'])


Not sure if should include : If no type is provided, the type of the default value is used, and if no default value is provided, the type is assumed to be STRING.

Multiple Arguments
-----------------------------------

To set the number of argument use the ``nargs`` kwarg. It can be set to any positive integer and -1. Setting it to -1, makes the number of arguments arbitrary (which is called variadic) and can only be used once. The arguments are then packed as a tuple and passed to the function.

.. click:example::

    @click.command()
    @click.argument('src', nargs=1)
    @click.argument('dsts', nargs=-1)
    def copy(src, dsts):
        """Move file SRC to DST."""
        for destination in dsts:
            click.echo(f"Copy {src} to folder {destination}")

And what it looks like:

.. click:run::

    invoke(copy, args=['foo.txt', 'usr/david/foo.txt', 'usr/mitsuko/foo.txt'])

Note this example is not how you would handle files and files paths, since it passes them in as strings. For more see :ref:`handling-files`.

.. admonition:: Note on Required Arguments

   It is not recommended, but you may make at least one argument required by setting ``required=True``.  It is not recommended since we think command line tools should gracefully degrade into becoming noops.  We think this because command line tools are often invoked with wildcard inputs and they should not error out if the wildcard is empty.

Argument Escape Sequences
---------------------------

If you want to process arguments that look like options, like a file named ``-foo.txt``, you must pass the ``--`` separator first. After you pass the ``--``, you may only pass arguments. This is a common feature for POSIX command line tools.

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

This feature is not recommended since it be confusing to users. Arguments can only pull environment variables from ? explicitly named environment variables. In that case, it can also be a list of different environment variables where the first one is picked. ?

Example usage:

.. click:example::

    @click.command()
    @click.argument('src', envvar='SRC', type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!')
        invoke(echo, env={'SRC': 'hello.txt'})

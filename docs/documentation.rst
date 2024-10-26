Documenting Scripts
===================

.. currentmodule:: click

Click makes it very easy to document your command line tools.  First of
all, it automatically generates help pages for you.  While these are
currently not customizable in terms of their layout, all of the text
can be changed.

Help Texts
----------

Commands and options accept help arguments.  In the case of commands, the
docstring of the function is automatically used if provided.

Simple example:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        """This script prints hello NAME COUNT times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

And what it looks like:

.. click:run::

    invoke(hello, args=['--help'])


.. _documenting-arguments:

Documenting Arguments
~~~~~~~~~~~~~~~~~~~~~

:func:`click.argument` does not take a ``help`` parameter. This is to
follow the general convention of Unix tools of using arguments for only
the most necessary things, and to document them in the command help text
by referring to them by name.

You might prefer to reference the argument in the description:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['--help'])

Or you might prefer to explicitly provide a description of the argument:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME.

        FILENAME is the name of the file to check.
        """
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['--help'])

For more examples, see the examples in :doc:`/arguments`.


Preventing Rewrapping
---------------------

The default behavior of Click is to rewrap text based on the width of the
terminal, to a maximum 80 characters. In some circumstances, this can become
a problem. The main issue is when showing code examples, where newlines are
significant.

Rewrapping can be disabled on a per-paragraph basis by adding a line with
solely the ``\b`` escape marker in it.  This line will be removed from the
help text and rewrapping will be disabled.

Example:

.. click:example::

    @click.command()
    def cli():
        """First paragraph.

        This is a very long second paragraph and as you
        can see wrapped very early in the source text
        but will be rewrapped to the terminal width in
        the final output.

        \b
        This is
        a paragraph
        without rewrapping.

        And this is a paragraph
        that will be rewrapped again.
        """

And what it looks like:

.. click:run::

    invoke(cli, args=['--help'])

To change the maximum width, pass ``max_content_width`` when calling the command.

.. code-block:: python

    cli(max_content_width=120)


.. _doc-meta-variables:

Truncating Help Texts
---------------------

Click gets command help text from function docstrings.  However if you
already use docstrings to document function arguments you may not want
to see :param: and :return: lines in your help text.

You can use the ``\f`` escape marker to have Click truncate the help text
after the marker.

Example:

.. click:example::

    @click.command()
    @click.pass_context
    def cli(ctx):
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.
        \f

        :param click.core.Context ctx: Click context.
        """

And what it looks like:

.. click:run::

    invoke(cli, args=['--help'])


Meta Variables
--------------

Options and parameters accept a ``metavar`` argument that can change the
meta variable in the help page.  The default version is the parameter name
in uppercase with underscores, but can be annotated differently if
desired.  This can be customized at all levels:

.. click:example::

    @click.command(options_metavar='<options>')
    @click.option('--count', default=1, help='number of greetings',
                  metavar='<int>')
    @click.argument('name', metavar='<name>')
    def hello(count, name):
        """This script prints hello <name> <int> times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

Example:

.. click:run::

    invoke(hello, args=['--help'])


Command Short Help
------------------

For commands, a short help snippet is generated.  By default, it's the first
sentence of the help message of the command, unless it's too long.  This can
also be overridden:

.. click:example::

    @click.group()
    def cli():
        """A simple command line tool."""

    @cli.command('init', short_help='init the repo')
    def init():
        """Initializes the repository."""

    @cli.command('delete', short_help='delete the repo')
    def delete():
        """Deletes the repository."""

And what it looks like:

.. click:run::

    invoke(cli, prog_name='repo.py')

Command Epilog Help
-------------------

The help epilog is like the help string but it's printed at the end of the help
page after everything else. Useful for showing example command usages or
referencing additional help resources.

.. click:example::

    @click.command(epilog='Check out our docs at https://click.palletsprojects.com/ for more details')
    def init():
        """Initializes the repository."""

And what it looks like:

.. click:run::

    invoke(init, prog_name='repo.py', args=['--help'])

Help Parameter Customization
----------------------------

.. versionadded:: 2.0

The help parameter is implemented in Click in a very special manner.
Unlike regular parameters it's automatically added by Click for any
command and it performs automatic conflict resolution.  By default it's
called ``--help``, but this can be changed.  If a command itself implements
a parameter with the same name, the default help parameter stops accepting
it.  There is a context setting that can be used to override the names of
the help parameters called :attr:`~Context.help_option_names`.

This example changes the default parameters to ``-h`` and ``--help``
instead of just ``--help``:

.. click:example::

    CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

    @click.command(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

And what it looks like:

.. click:run::

    invoke(cli, ['-h'])

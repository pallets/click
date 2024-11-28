Help Pages
===================

.. currentmodule:: click

Click makes it very easy to document your command line tools.  For most things Click automatically generates help pages for you.  By design the layout is not customizable but the text is.

Help Texts
----------

Commands and options accept help arguments.  In the case of commands, the
docstring of the function is automatically used if provided.

Simple example:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.option('--name', help='a name')
    def hello(count, name=False):
        """This script prints hello NAME COUNT times."""
        for x in range(count):
            if name:
                click.echo(f"Hello {name}!")
            else:
                click.echo("Hello!")

And what it looks like:

.. click:run::

    invoke(hello, args=['--help'])


.. _documenting-arguments:

Command Short Help
------------------

For commands, a short help snippet is generated. By default, it's the first
sentence of the docstring. If it is too long, then it will show as much as it can on one line and end with ``...``.  The short help snippet can also be overridden with the kwarg ``short_help``:

.. click:example::

    @click.group()
    def cli():
        """A simple command line tool."""

    @cli.command('init', short_help='init the repo')
    def init():
        """Initializes the repository."""

And what it looks like:

.. click:run::

    invoke(cli, args=['--help'])

Command Epilog Help
-------------------

The help epilog is like the help string but it's printed at the end of the help page after everything else. Useful for showing example command usages or
referencing additional help resources.

.. click:example::

    @click.command(epilog='Check out our docs at https://click.palletsprojects.com/ for more details')
    def init():
        """Initializes the repository."""

And what it looks like:

.. click:run::

    invoke(init, args=['--help'])

Documenting Arguments
----------------------

:class:`click.argument` does not take a ``help`` parameter. This follows the Unix Command Line Tools convention of using arguments only for necessary things and documenting them in the command help text
by name. For Python that means including them in docstrings.

A brief example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['--help'])

Or more explicitly:

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

Click's Wrapping Behavior
----------------------------
Click's default wrapping ignores single new lines and rewraps the text based on the width of the
terminal, to a maximum 80 characters. In the example notice how the second grouping of three lines is rewrapped into a single paragraph.

.. click:example::

    @click.command()
    def cli():
        """
        This is a very long second paragraph and as you
        can see wrapped very early in the source text
        but will be rewrapped to the terminal width in
        the final output.

        This is
        a paragraph
        that is compacted.
        """

And what it looks like:

.. click:run::

    invoke(cli, args=['--help'])

Escaping Click's Wrapping
---------------------------
Sometimes Click's wrapping can be a problem, such as when showing code examples where newlines are significant. This behavior can be escaped on a per-paragraph basis by adding a line with only ``\b`` . The ``\b`` is removed from the rendered help text.

Example:

.. click:example::

    @click.command()
    def cli():
        """First paragraph.

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

To change the rendering maximum width, pass ``max_content_width`` when calling the command.

.. code-block:: python

    cli(max_content_width=120)

.. _doc-meta-variables:

Truncating Help Texts
---------------------

Click gets :class:`Command` help text from the docstring. If you do not want to include part of the docstring, add the ``\f`` escape marker to have Click truncate the help text after the marker.

Example:

.. click:example::

    @click.command()
    @click.pass_context
    def cli(ctx):
        """First paragraph.
        \f

        :param click.core.Context ctx: Click context.
        """

And what it looks like:

.. click:run::

    invoke(cli, args=['--help'])


Variable Placeholders
-----------------------

The default placeholder variable (meta variable) in the help pages is the parameter name in uppercase with underscores. This can be changed for Options and Parameters with the ``options_metavar`` and  ``metavar`` kwargs.

.. click:example::

    # This controls entry on the usage line.
    @click.command(options_metavar='[[options]]')
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

Help Parameter Customization
----------------------------
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

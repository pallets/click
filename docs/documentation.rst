Documenting Scripts
===================

Click makes it very easy to document your command line tools.  First of
all it automatically generates help pages for you.  While these are
currently not customizable in layout, all the texts can be changed.

Help Texts
----------

Commands and options accept help arguments.  In case of commands the doc
string of the function is automatically used if provided.

Simple example:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        """This script prints hello NAME COUNT times."""
        for x in range(count):
            click.echo('Hello %s!' % name)

And what it looks like:

.. click:run::

    invoke(hello, args=['--help'])

Arguments cannot be documented this way.  This is to follow general
convention of Unix tools to use arguments only for the most necessary
things and to document them in the introduction text by referring to them
by name.

Preventing Rewrapping
---------------------

The default behavior of click is to rewrap text to work correctly for the
width of the terminal.  In some circumstances this can become a problem.
The main issue is showing code examples where newlines are significant.

Rewrapping can be disabled on a per-paragraph case by adding a line with
just the ``\b`` escape marker in.  This line will be removed in the help
text but rewrapping will be disabled.

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


Meta Vars
---------

Options and parameters accept a ``metavar`` argument that can change the
meta variable in the help page.  The default version is the parameter name
in uppercase with underscores and sometimes annotated differently if
optional.  This can be customized at all levels:

.. click:example::

    @click.command(options_metavar='<options>')
    @click.option('--count', default=1, help='number of greetings',
                  metavar='<int>')
    @click.argument('name', metavar='<name>')
    def hello(count, name):
        """This script prints hello <name> <int> times."""
        for x in range(count):
            click.echo('Hello %s!' % name)

Example:

.. click:run::

    invoke(hello, args=['--help'])
                

Command Short Help
------------------

For commands a short help is generated.  By default it's the first part
(until the first dot) of the help message of the command unless it's too
long.  This can also be overridden:

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

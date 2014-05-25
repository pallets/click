Quickstart
==========

.. currentmodule:: click

You can get the library directly from PyPI::

    pip install click

Screencast and Examples
-----------------------

There is a screencast available which shows the basic API of click and
how to build simple applications with it.  It also explores how to build
commands with subcommands.

*   `Building Command Line Applications with Click
    <https://www.youtube.com/watch?v=kNke39OZ2k0>`_

Examples of Click applications can be found in the documentation as well
as in the github repository together with readme files:

*   ``inout``: `File input and output
    <https://github.com/mitsuhiko/click/tree/master/examples/inout>`_
*   ``naval``: `Port of docopt naval example
    <https://github.com/mitsuhiko/click/tree/master/examples/naval>`_
*   ``aliases``: `Command alias example
    <https://github.com/mitsuhiko/click/tree/master/examples/aliases>`_
*   ``repo``: `Git/hg like command line interface
    <https://github.com/mitsuhiko/click/tree/master/examples/repo>`_
*   ``complex``: `Complex example with plugin loading
    <https://github.com/mitsuhiko/click/tree/master/examples/complex>`_
*   ``validation``: `Custom parameter validation example
    <https://github.com/mitsuhiko/click/tree/master/examples/validation>`_

Basic Concepts
--------------

Click is based on declaring commands through decorators.  Internally there
is a non-decorator interface for advanced use cases but it's discouraged
for high-level usage.

A function becomes a click command line tool by decorating it through
:func:`click.command`.  In the most simple version just decorating a
function with this decorator will make it into a callable script:

.. click:example::

    import click

    @click.command()
    def hello():
        click.echo('Hello World!')

What's happening is that the decorator converts the function into a
:class:`Command` which then can be invoked::

    if __name__ == '__main__':
        hello()

And what it looks like:

.. click:run::

    invoke(hello, args=[])

And the corresponding help page:

.. click:run::

    invoke(hello, args=['--help'])

Echoing
-------

Why does this example use :func:`echo` instead of the regular
:func:`print` function?  The answer to this question is that click
attempts to support both Python 2 and Python 3 the same way and to be very
robust even when the environment is misconfigured.  Click wants to be
functional at least on a basic level even if everything is completely
broken.

What this means is that the :func:`echo` function applies some error
correction in case the terminal is misconfigured instead of dying with an
:exc:`UnicodeError`.

If you don't need this, you can also use the `print()` construct /
function.

Nesting Commands
----------------

Commands can be attached to other commands of type :class:`Group`.  This
allows arbitrary nesting of scripts.  As an example here is a script that
implements two commands for managing databases:

.. click:example::

    @click.group()
    def cli():
        pass

    @click.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(initdb)
    cli.add_command(dropdb)

As you can see the :func:`group` decorator works like the :func:`command`
decorator but creates a :class:`Group` object instead which can be given
multiple subcommands that can be attached with
:meth:`Group.add_command`.

For simple scripts it's also possible to automatically attach and create a
command by using the :meth:`Group.command` decorator instead.  The above
script can be written like this then:

.. click:example::

    @click.group()
    def cli():
        pass

    @cli.command()
    def initdb():
        click.echo('Initialized the database')

    @cli.command()
    def dropdb():
        click.echo('Dropped the database')

Adding Parameters
-----------------

To add parameters the :func:`option` and :func:`argument` decorators:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        for x in range(count):
            click.echo('Hello %s!' % name)

What it looks like:

.. click:run::

    invoke(hello, args=['--help'])

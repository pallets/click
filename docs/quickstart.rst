Quickstart
==========

.. currentmodule:: click

You can get the library directly from PyPI::

    pip install click

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
        print('Hello World!')

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
        print('Initialized the database')

    @click.command()
    def dropdb():
        print('Dropped the database')

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
        print('Initialized the database')

    @cli.command()
    def dropdb():
        print('Dropped the database')

Adding Parameters
-----------------

To add parameters the :func:`option` and :func:`argument` decorators:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        for x in range(count):
            print('Hello %s!' % name)

What it looks like:

.. click:run::

    invoke(hello, args=['--help'])

Welcome to the Click Documentation
==================================

click is a Python package for creating beautiful command line interfaces
in a composable way with as little amount of code as necessary.  It's the
"Command Line Interface Creation Kit".  It's highly configurable but comes
with good defaults out of the box.

It aims at making writing command line tools fun and quick without causing
user frustration at not being able to implement an intended CLI API.

Click in three points:

-   arbitrary nesting of commands
-   automatic help page generation
-   supports lazy loading of subcommands at runtime

What does it look like?  A simple example can be this:

.. click:example::

    import click

    @click.command()
    @click.option('--count', default=1, help='Number of greetings.')
    @click.option('--name', prompt='Your name',
                  help='The person to greet.')
    def hello(count, name):
        """Simple program that greets NAME for a total of COUNT times."""
        for x in range(count):
            click.echo('Hello %s!' % name)

    if __name__ == '__main__':
        hello()

And what it looks like:

.. click:run::

    invoke(hello, ['--count=3'], input='John\n')

And it gives you nicely formatted help pages:

.. click:run::

    invoke(hello, ['--help'])

You can get the library directly from PyPI::

    pip install click

Documentation Contents
----------------------

This part of the documentation guides you through all the usage patterns
of the library.

.. toctree::
   :maxdepth: 2

   why
   quickstart
   parameters
   options
   arguments
   commands
   prompts
   documentation
   setuptools
   complex
   advanced
   testing
   utils
   python3

API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api

Other Documents
---------------

.. toctree::
   :maxdepth: 2

   changelog
   license

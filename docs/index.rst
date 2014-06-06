Welcome to the Click Documentation
==================================

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.  It's the "Command
Line Interface Creation Kit".  It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing frustration caused by the inability to implement an
intended CLI API.

Click in three points:

-   arbitrary nesting of commands
-   automatic help page generation
-   supports lazy loading of subcommands at runtime

What does it look like?  Here is an example of a simple click program:

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

And what it looks like when run:

.. click:run::

    invoke(hello, ['--count=3'], input='John\n')

It automatically generates nicely formatted help pages:

.. click:run::

    invoke(hello, ['--help'])

You can get the library directly from PyPI::

    pip install click

Documentation Contents
----------------------

This part of the documentation guides you through all of the library's
usage patterns.

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
   bashcomplete
   python3

API Reference
-------------

If you are looking for information on a specific function, class, or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api

Miscellaneous Pages
-------------------

.. toctree::
   :maxdepth: 2

   changelog
   upgrading
   license

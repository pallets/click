click
=====

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

What does it look like?  A simple example can be this::

    import click

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.option('--name', prompt='Your name',
                  help='the person to greet', required=True)
    def hello(count, name):
        for x in range(count):
            print('Hello %s!' % name)

    if __name__ == '__main__':
        hello()

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

API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api

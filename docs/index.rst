.. rst-class:: hide-header

Welcome to Click
================

.. image:: _static/click-logo.png
    :align: center
    :scale: 50%
    :target: https://palletsprojects.com/p/click/

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.  It's the "Command
Line Interface Creation Kit".  It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to implement
an intended CLI API.

Click in three points:

-   arbitrary nesting of commands
-   automatic help page generation
-   supports lazy loading of subcommands at runtime

What does it look like?  Here is an example of a simple Click program:

.. click:example::

    import click

    @click.command()
    @click.option('--count', default=1, help='Number of greetings.')
    @click.option('--name', prompt='Your name',
                  help='The person to greet.')
    def hello(count, name):
        """Simple program that greets NAME for a total of COUNT times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

    if __name__ == '__main__':
        hello()

And what it looks like when run:

.. click:run::

    invoke(hello, ['--count=3'], prog_name='python hello.py', input='John\n')

It automatically generates nicely formatted help pages:

.. click:run::

    invoke(hello, ['--help'], prog_name='python hello.py')

You can get the library directly from PyPI::

    pip install click

Documentation
-------------

This part of the documentation guides you through all of the library's
usage patterns.

.. toctree::
   :maxdepth: 2

   why
   quickstart
   virtualenv
   setuptools
   parameters
   options
   arguments
   handling_files
   commands
   prompts
   documentation
   complex
   advanced
   testing
   utils
   shell-completion
   exceptions
   unicode-support
   wincmd

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

   contrib
   upgrading
   license
   changes

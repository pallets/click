\$ click\_
==========

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.  It's the "Command
Line Interface Creation Kit".  It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to
implement an intended CLI API.

Click in three points:

-   arbitrary nesting of commands
-   automatic help page generation
-   supports lazy loading of subcommands at runtime


Installing
----------

Install and update using `pip`_:

.. code-block:: text

    $ pip install click

Click supports Python 3.4 and newer, Python 2.7, and PyPy.

.. _pip: https://pip.pypa.io/en/stable/quickstart/


A Simple Example
----------------

What does it look like? Here is an example of a simple Click program:

.. code-block:: python

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

.. code-block:: text

    $ python hello.py --count=3
    Your name: John
    Hello John!
    Hello John!
    Hello John!


Donate
------

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, `please
donate today`_.

.. _please donate today: https://palletsprojects.com/donate


Links
-----

*   Website: https://palletsprojects.com/p/click/
*   Documentation: https://click.palletsprojects.com/
*   License: `BSD <https://github.com/pallets/click/blob/master/LICENSE>`_
*   Releases: https://pypi.org/project/click/
*   Code: https://github.com/pallets/click
*   Issue tracker: https://github.com/pallets/click/issues
*   Test status:

    *   Linux, Mac: https://travis-ci.org/pallets/click
    *   Windows: https://ci.appveyor.com/project/pallets/click

*   Test coverage: https://codecov.io/gh/pallets/click

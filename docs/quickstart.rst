Quickstart
==========

.. currentmodule:: click

You can get the library directly from PyPI::

    pip install click

The installation into a :ref:`virtualenv` is heavily recommended.

.. _virtualenv:

virtualenv
----------

Virtualenv is probably what you want to use for developing Click
applications.

What problem does virtualenv solve?  Chances are that you want to use it
for other projects besides your Click script.  But the more projects you
have, the more likely it is that you will be working with different
versions of Python itself, or at least different versions of Python
libraries.  Let's face it: quite often libraries break backwards
compatibility, and it's unlikely that any serious application will have
zero dependencies.  So what do you do if two or more of your projects have
conflicting dependencies?

Virtualenv to the rescue!  Virtualenv enables multiple side-by-side
installations of Python, one for each project.  It doesn't actually
install separate copies of Python, but it does provide a clever way to
keep different project environments isolated.  Let's see how virtualenv
works.

If you are on Mac OS X or Linux::

    $ sudo pip install virtualenv

One of these will probably install virtualenv on your system.  Maybe it's even
in your package manager.  If you use Ubuntu, try::

    $ sudo apt-get install python-virtualenv

If you are on Windows (or none of the above methods worked) you must install
``pip`` first.  For more information about this, see `installing pip`_.
Once you have it installed, run the ``pip`` command from above, but without
the `sudo` prefix.

.. _installing pip: https://pip.readthedocs.io/en/latest/installing.html

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and a `venv`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing setuptools, pip............done.

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . venv/bin/activate

If you are a Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

And if you want to go back to the real world, use the following command::

    $ deactivate

After doing this, the prompt of your shell should be as familiar as before.

Now, let's move on. Enter the following command to get Click activated in your
virtualenv::

    $ pip install Click

A few seconds later and you are good to go.

Screencast and Examples
-----------------------

There is a screencast available which shows the basic API of Click and
how to build simple applications with it.  It also explores how to build
commands with subcommands.

*   `Building Command Line Applications with Click
    <https://www.youtube.com/watch?v=kNke39OZ2k0>`_

Examples of Click applications can be found in the documentation as well
as in the GitHub repository together with readme files:

*   ``inout``: `File input and output
    <https://github.com/pallets/click/tree/master/examples/inout>`_
*   ``naval``: `Port of docopt naval example
    <https://github.com/pallets/click/tree/master/examples/naval>`_
*   ``aliases``: `Command alias example
    <https://github.com/pallets/click/tree/master/examples/aliases>`_
*   ``repo``: `Git-/Mercurial-like command line interface
    <https://github.com/pallets/click/tree/master/examples/repo>`_
*   ``complex``: `Complex example with plugin loading
    <https://github.com/pallets/click/tree/master/examples/complex>`_
*   ``validation``: `Custom parameter validation example
    <https://github.com/pallets/click/tree/master/examples/validation>`_
*   ``colors``: `Colorama ANSI color support
    <https://github.com/pallets/click/tree/master/examples/colors>`_
*   ``termui``: `Terminal UI functions demo
    <https://github.com/pallets/click/tree/master/examples/termui>`_
*   ``imagepipe``: `Multi command chaining demo
    <https://github.com/pallets/click/tree/master/examples/imagepipe>`_

Basic Concepts - Creating a Command
-----------------------------------

Click is based on declaring commands through decorators.  Internally, there
is a non-decorator interface for advanced use cases, but it's discouraged
for high-level usage.

A function becomes a Click command line tool by decorating it through
:func:`click.command`.  At its simplest, just decorating a function
with this decorator will make it into a callable script:

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

    invoke(hello, args=[], prog_name='python hello.py')

And the corresponding help page:

.. click:run::

    invoke(hello, args=['--help'], prog_name='python hello.py')

Echoing
-------

Why does this example use :func:`echo` instead of the regular
:func:`print` function?  The answer to this question is that Click
attempts to support both Python 2 and Python 3 the same way and to be very
robust even when the environment is misconfigured.  Click wants to be
functional at least on a basic level even if everything is completely
broken.

What this means is that the :func:`echo` function applies some error
correction in case the terminal is misconfigured instead of dying with an
:exc:`UnicodeError`.

As an added benefit, starting with Click 2.0, the echo function also
has good support for ANSI colors.  It will automatically strip ANSI codes
if the output stream is a file and if colorama is supported, ANSI colors
will also work on Windows. Note that in Python 2, the :func:`echo` function
does not parse color code information from bytearrays. See :ref:`ansi-colors`
for more information.

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

As you can see, the :func:`group` decorator works like the :func:`command`
decorator, but creates a :class:`Group` object instead which can be given
multiple subcommands that can be attached with :meth:`Group.add_command`.

For simple scripts, it's also possible to automatically attach and create a
command by using the :meth:`Group.command` decorator instead.  The above
script can instead be written like this:

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

You would then invoke the :class:`Group` in your setuptools entry points or
other invocations::

    if __name__ == '__main__':
        cli()

Adding Parameters
-----------------

To add parameters, use the :func:`option` and :func:`argument` decorators:

.. click:example::

    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        for x in range(count):
            click.echo('Hello %s!' % name)

What it looks like:

.. click:run::

    invoke(hello, args=['--help'], prog_name='python hello.py')

.. _switching-to-setuptools:

Switching to Setuptools
-----------------------

In the code you wrote so far there is a block at the end of the file which
looks like this: ``if __name__ == '__main__':``.  This is traditionally
how a standalone Python file looks like.  With Click you can continue
doing that, but there are better ways through setuptools.

There are two main (and many more) reasons for this:

The first one is that setuptools automatically generates executable
wrappers for Windows so your command line utilities work on Windows too.

The second reason is that setuptools scripts work with virtualenv on Unix
without the virtualenv having to be activated.  This is a very useful
concept which allows you to bundle your scripts with all requirements into
a virtualenv.

Click is perfectly equipped to work with that and in fact the rest of the
documentation will assume that you are writing applications through
setuptools.

I strongly recommend to have a look at the :ref:`setuptools-integration`
chapter before reading the rest as the examples assume that you will
be using setuptools.

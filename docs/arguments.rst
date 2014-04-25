Arguments
=========

.. currentmodule:: click

Arguments work similar to options but are positional.  They also only
support subset of the features of options due to their syntactical nature.
Click also will not attempt to document arguments for you and wants you to
document them manually to avoid ugly looking help pages.

Basic Arguments
---------------

The most basic option is a simple string arguments of one value.  If no
type is provided the type of the default value is used.  If no default
value is provided the type is assumed to be :data:`STRING`.

Example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        print(filename)

And what it looks like::

    $ python touch.py foo.txt
    foo.txt

Variadic Arguments
------------------

The second most common version is variadic arguments where a specific (or
unlimited) number of arguments is accepted.  This can be controlled with
the ``nargs`` parameter.  If it's set to ``-1`` then an unlimited number
of arguments is accepted.

The value is then passed as a tuple.  Note that only one argument really
can be set to ``nargs=-1`` and right now only the last.

Example::

    @click.command()
    @click.argument('files', nargs=-1)
    def touch(files):
        for file in files:
            print(file)

And what it looks like::

    $ python touch.py foo.txt bar.txt
    foo.txt
    bar.txt

.. _file-args:

File Arguments
--------------

Since all the examples have already worked with file names it makes sense
to explain how to deal with files properly.  Command line tools are more
fun if they work with files the unix way which is to accept ``-`` as
special file that refers to stdin/stdout.

Click supports this through the :class:`click.File` type which
intelligently handles files for you.  It also deals with unicode and bytes
correctly for all versions of Python so your script stays very portable.

Example::

    @click.command()
    @click.argument('input', type=click.File('rb'))
    @click.argument('output', type=click.File('wb'))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

And what it does::

    $ python inout.py - hello.txt
    hello
    ^D
    $ python inout.py hello.txt -
    hello

Environment Variables
---------------------

Like options, arguments can also get values from an environment variable.
Unlike options however this is only supported for explicitly named
environment variables.

Example usage::

    @click.command()
    @click.argument('--src', envvar='SRC', type=click.File('r'))
    def echo(src):
        print(src.read())

    if __name__ == '__main__':
        echo()

And from the command line::

    $ export SRC=hello.txt
    $ python echo.py
    Hello!

In that case it can also be a list of different environment variables
where the first one is picked.

Generally this feature is not recommended because it can cause a lot of
confusion to the user.

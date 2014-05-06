Arguments
=========

.. currentmodule:: click

Arguments work similar to options but are positional.  They also only
support a subset of the features of options due to their syntactical nature.
Click also will not attempt to document arguments for you and wants you to
document them manually to avoid ugly looking help pages.

Basic Arguments
---------------

The most basic option is a simple string argument of one value.  If no
type is provided the type of the default value is used.  If no default
value is provided the type is assumed to be :data:`STRING`.

Example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['foo.txt'])

Variadic Arguments
------------------

The second most common version is variadic arguments where a specific (or
unlimited) number of arguments is accepted.  This can be controlled with
the ``nargs`` parameter.  If it's set to ``-1`` then an unlimited number
of arguments is accepted.

The value is then passed as a tuple.  Note that only one argument can be
set to ``nargs=-1`` as this will eat up all arguments.

Example:

.. click:example::

    @click.command()
    @click.argument('src', nargs=-1)
    @click.argument('dst', nargs=1)
    def copy(src, dst):
        for fn in src:
            click.echo('move %s to folder %s' % (fn, dst))

And what it looks like:

.. click:run::

    invoke(copy, args=['foo.txt', 'bar.txt', 'my_folder'])

.. _file-args:

File Arguments
--------------

Since all the examples have already worked with file names it makes sense
to explain how to deal with files properly.  Command line tools are more
fun if they work with files the unix way which is to accept ``-`` as a
special file that refers to stdin/stdout.

Click supports this through the :class:`click.File` type which
intelligently handles files for you.  It also deals with unicode and bytes
correctly for all versions of Python so your script stays very portable.

Example:

.. click:example::

    @click.command()
    @click.argument('input', type=click.File('rb'))
    @click.argument('output', type=click.File('wb'))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

And what it does:

.. click:run::

    with isolated_filesystem():
        invoke(inout, args=['-', 'hello.txt'], input=['hello'],
               terminate_input=True)
        invoke(inout, args=['hello.txt', '-'])

File Opening Safety
-------------------

The :class:`FileType` type has one problem it needs to deal with and that
is to decide when to open a file.  The default behavior is to be
"intelligent" about it.  What this means is that it will open stdin/stdout
and files opened for reading immediately.  This will directly give the
user feedback when a file cannot be opened.  But it will only open files
for writing the first time an IO operation is performed by wrapping the
file automatically in a special wrapper.

This behavior can be forced by passing ``lazy=True`` or ``lazy=False`` to
the constructor.  If the file is openened lazily it will fail on first IO
operation by raising an :exc:`FileError`.

Since files opened for writing will typically immediatley empty the file,
the lazy mode should really only be disabled if the developer is 100% sure
that this is intended behavior.

Environment Variables
---------------------

Like options, arguments can also get values from an environment variable.
Unlike options however this is only supported for explicitly named
environment variables.

Example usage:

.. click:example::

    @click.command()
    @click.argument('src', envvar='SRC', type=click.File('r'))
    def echo(src):
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!')
        invoke(echo, env={'SRC': 'hello.txt'})

In that case it can also be a list of different environment variables
where the first one is picked.

Generally this feature is not recommended because it can cause a lot of
confusion to the user.

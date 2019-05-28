.. _arguments:

Arguments
=========

.. currentmodule:: click

Arguments work similarly to :ref:`options <options>` but are positional.
They also only support a subset of the features of options due to their
syntactical nature. Click will also not attempt to document arguments for
you and wants you to :ref:`document them manually <documenting-arguments>`
in order to avoid ugly help pages.

Basic Arguments
---------------

The most basic option is a simple string argument of one value.  If no
type is provided, the type of the default value is used, and if no default
value is provided, the type is assumed to be :data:`STRING`.

Example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

And what it looks like:

.. click:run::

    invoke(touch, args=['foo.txt'])

Variadic Arguments
------------------

The second most common version is variadic arguments where a specific (or
unlimited) number of arguments is accepted.  This can be controlled with
the ``nargs`` parameter.  If it is set to ``-1``, then an unlimited number
of arguments is accepted.

The value is then passed as a tuple.  Note that only one argument can be
set to ``nargs=-1``, as it will eat up all arguments.

Example:

.. click:example::

    @click.command()
    @click.argument('src', nargs=-1)
    @click.argument('dst', nargs=1)
    def copy(src, dst):
        """Move file SRC to DST."""
        for fn in src:
            click.echo('move %s to folder %s' % (fn, dst))

And what it looks like:

.. click:run::

    invoke(copy, args=['foo.txt', 'bar.txt', 'my_folder'])

Note that this is not how you would write this application.  The reason
for this is that in this particular example the arguments are defined as
strings.  Filenames, however, are not strings!  They might be on certain
operating systems, but not necessarily on all.  For better ways to write
this, see the next sections.

.. admonition:: Note on Non-Empty Variadic Arguments

   If you come from ``argparse``, you might be missing support for setting
   ``nargs`` to ``+`` to indicate that at least one argument is required.

   This is supported by setting ``required=True``.  However, this should
   not be used if you can avoid it as we believe scripts should gracefully
   degrade into becoming noops if a variadic argument is empty.  The
   reason for this is that very often, scripts are invoked with wildcard
   inputs from the command line and they should not error out if the
   wildcard is empty.

.. _file-args:

File Arguments
--------------

Since all the examples have already worked with filenames, it makes sense
to explain how to deal with files properly.  Command line tools are more
fun if they work with files the Unix way, which is to accept ``-`` as a
special file that refers to stdin/stdout.

Click supports this through the :class:`click.File` type which
intelligently handles files for you.  It also deals with Unicode and bytes
correctly for all versions of Python so your script stays very portable.

Example:

.. click:example::

    @click.command()
    @click.argument('input', type=click.File('rb'))
    @click.argument('output', type=click.File('wb'))
    def inout(input, output):
        """Copy contents of INPUT to OUTPUT."""
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

File Path Arguments
-------------------

In the previous example, the files were opened immediately.  But what if
we just want the filename?  The naïve way is to use the default string
argument type.  However, remember that Click is Unicode-based, so the string
will always be a Unicode value.  Unfortunately, filenames can be Unicode or
bytes depending on which operating system is being used.  As such, the type
is insufficient.

Instead, you should be using the :class:`Path` type, which automatically
handles this ambiguity.  Not only will it return either bytes or Unicode
depending on what makes more sense, but it will also be able to do some
basic checks for you such as existence checks.

Example:

.. click:example::

    @click.command()
    @click.argument('filename', type=click.Path(exists=True))
    def touch(filename):
        """Print FILENAME if the file exists."""
        click.echo(click.format_filename(filename))

And what it does:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!\n')
        invoke(touch, args=['hello.txt'])
        println()
        invoke(touch, args=['missing.txt'])


File Opening Safety
-------------------

The :class:`FileType` type has one problem it needs to deal with, and that
is to decide when to open a file.  The default behavior is to be
"intelligent" about it.  What this means is that it will open stdin/stdout
and files opened for reading immediately.  This will give the user direct
feedback when a file cannot be opened, but it will only open files
for writing the first time an IO operation is performed by automatically
wrapping the file in a special wrapper.

This behavior can be forced by passing ``lazy=True`` or ``lazy=False`` to
the constructor.  If the file is opened lazily, it will fail its first IO
operation by raising an :exc:`FileError`.

Since files opened for writing will typically immediately empty the file,
the lazy mode should only be disabled if the developer is absolutely sure
that this is intended behavior.

Forcing lazy mode is also very useful to avoid resource handling
confusion.  If a file is opened in lazy mode, it will receive a
``close_intelligently`` method that can help figure out if the file
needs closing or not.  This is not needed for parameters, but is
necessary for manually prompting with the :func:`prompt` function as you
do not know if a stream like stdout was opened (which was already open
before) or a real file that needs closing.

Starting with Click 2.0, it is also possible to open files in atomic mode by
passing ``atomic=True``.  In atomic mode, all writes go into a separate
file in the same folder, and upon completion, the file will be moved over to
the original location.  This is useful if a file regularly read by other
users is modified.

Environment Variables
---------------------

Like options, arguments can also grab values from an environment variable.
Unlike options, however, this is only supported for explicitly named
environment variables.

Example usage:

.. click:example::

    @click.command()
    @click.argument('src', envvar='SRC', type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!')
        invoke(echo, env={'SRC': 'hello.txt'})

In that case, it can also be a list of different environment variables
where the first one is picked.

Generally, this feature is not recommended because it can cause the user
a lot of confusion.

Option-Like Arguments
---------------------

Sometimes, you want to process arguments that look like options.  For
instance, imagine you have a file named ``-foo.txt``.  If you pass this as
an argument in this manner, Click will treat it as an option.

To solve this, Click does what any POSIX style command line script does,
and that is to accept the string ``--`` as a separator for options and
arguments.  After the ``--`` marker, all further parameters are accepted as
arguments.

Example usage:

.. click:example::

    @click.command()
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['--', '-foo.txt', 'bar.txt'])

If you don't like the ``--`` marker, you can set ignore_unknown_options to
True to avoid checking unknown options:

.. click:example::

    @click.command(context_settings={"ignore_unknown_options": True})
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['-foo.txt', 'bar.txt'])


.. _handling-files:

Handling Files
================

.. currentmodule:: click

File and files paths are often passed in as arguments.

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
argument type. The :class:`Path` type has several checks available which raise nice
errors if they fail, such as existence. Filenames in these error messages are formatted
with :func:`format_filename`, so any undecodable bytes will be printed nicely.

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

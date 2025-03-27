.. _handling-files:

Handling Files
================

.. currentmodule:: click

Click has built in features to support file and file path handling. The examples use arguments but the same principle applies to options as well.

.. _file-args:

File Arguments
-----------------

Click supports working with files with the :class:`File` type. Some notable features are:

*   Support for   ``-`` to mean a special file that refers to stdin when used for reading, and stdout when used for writing. This is a common pattern for POSIX command line utilities.
*   Deals with ``str`` and ``bytes`` correctly for all versions of Python.

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

And from the command line:

.. click:run::

    with isolated_filesystem():
        invoke(inout, args=['-', 'hello.txt'], input=['hello'],
               terminate_input=True)
        invoke(inout, args=['hello.txt', '-'])

File Path Arguments
----------------------

For handling paths, the :class:`Path` type is better than a ``str``. Some notable features are:

*   The ``exists`` argument will verify whether the path exists.
*	``readable``, ``writable``, and ``executable`` can perform permission checks.
*	``file_okay`` and ``dir_okay`` allow specifying whether files/directories are accepted.
*   Error messages are nicely formatted using :func:`format_filename` so any undecodable bytes will be printed nicely.

See :class:`Path` for all features.

Example:

.. click:example::

    @click.command()
    @click.argument('filename', type=click.Path(exists=True))
    def touch(filename):
        """Print FILENAME if the file exists."""
        click.echo(click.format_filename(filename))

And from the command line:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!\n')
        invoke(touch, args=['hello.txt'])
        println()
        invoke(touch, args=['missing.txt'])


File Opening Behaviors
-----------------------------

The :class:`File` type attempts to be "intelligent" about when to open a file. Stdin/stdout and files opened for reading will be opened immediately. This will give the user direct feedback when a file cannot be opened. Files opened for writing will only be open on the first IO operation. This is done by automatically wrapping the file in a special wrapper.

File open behavior can be controlled by the boolean kwarg ``lazy``. If a file is opened lazily:

*   A failure at first IO operation will happen by raising an :exc:`FileError`.
*   It can help minimize resource handling confusion.  If a file is opened in lazy mode, it will call :meth:`LazyFile.close_intelligently` to help figure out if the file needs closing or not. This is not needed for parameters, but is necessary for manually prompting. For manual prompts with the :func:`prompt` function you do not know if a stream like stdout was opened (which was already open before) or a real file was opened (that needs closing).

Since files opened for writing will typically empty the file, the lazy mode should only be disabled if the developer is absolutely sure that this is intended behavior.

It is also possible to open files in atomic mode by passing ``atomic=True``.  In atomic mode, all writes go into a separate file in the same folder, and upon completion, the file will be moved over to the original location.  This is useful if a file regularly read by other users is modified.

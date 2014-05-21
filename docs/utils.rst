Utilities
=========

.. currentmodule:: click

Besides the functionality that click provides to interface with argument
parsing and handling, it also provides a bunch of addon functionality that
is useful for writing command line utilities.


Printing to Stdout
------------------

The most obvious helper is the :func:`echo` function which in many ways
works like the Python print statement or function.  The main difference is
that it works the same on Python 2 and 3 and it intelligently detects
misconfigured output streams and will never fail (except on Python 3, for
more information see :ref:`python3-limitations`).

Example::

    import click

    click.echo('Hello World!')

Most importantly it can print both unicode and binary data, unlike the
builtin ``print`` function on Python 3 which cannot output any bytes.  It
will however emit a trailing newline by default which needs to be
supressed by passing ``nl=False``::

    click.echo(b'\xe2\x98\x83', nl=False)


Printing Filenames
------------------

Because filenames might not be unicode formatting them can be a bit
tricky.  Generally this is easier on Python 2 than 3 as you can just write
the bytes to stdout with the print function, but at least on Python 3 you
will need to always operate in unicode.

The way this works with click is through the :func:`format_filename`
function.  It does a best effort conversion of the filename to Unicode and
will never fail.  This makes it possible to use these filenames in the
context of a full unicode string.

Example::

    click.echo('Path: %s' % click.format_filename(b'foo.txt'))


Standard Streams
----------------

For command line utilities it's very important to get access to input and
output streams reliably.  Python generally provides access to these
streams through ``sys.stdout`` and friends, but unfortunately there are
API differences between 2.x and 3.x.  Especially in regards to how these
streams respond to unicode and binary data there are wide differences.

Because of this click provides the :func:`get_binary_stream` and
:func:`get_text_stream` which produce consistent results with different
Python versions and for widely misconfigured terminals.

The end result is that these functions will always return a functional
stream object (except in very odd cases on Python 3, see
:ref:`python3-limitations`).

Example::

    import click

    stdin_text = click.get_text_stream('stdin')
    stdout_binary = click.get_binary_stream('stdout')

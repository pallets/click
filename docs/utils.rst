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


ANSI Colors
-----------

.. versionadded:: 2.0

Starting with click 2.0 the :func:`echo` function gained a bit of extra
functionality to deal with ANSI colors.  This functionality is only
available if `colorama`_ is installed.  If it is installed then ANSI codes
are intelligently handled.

Primarily this means that:

-   click's echo function will automatically strip ANSI color codes if the
    stream is not connected to a terminal.
-   the echo function will transparently connect to the terminal on
    Windows and translate ANSI codes to terminal API calls.  This means
    that colors will work on Windows the same way they do on other
    operating systems.

Click will automatically detect when `colorama` is available and use it.
You do not have to call ``colorama.init()``.  In fact, it's strongly
recommended you not doing that as colorama will change the default output
streams which is not a good idea.

To install colorama run this command::

    $ pip install colorama


.. _colorama: https://pypi.python.org/pypi/colorama


Printing Filenames
------------------

Because filenames might not be unicode, formatting them can be a bit
tricky.  Generally this is easier on Python 2 than on 3 as you can just
write the bytes to stdout with the print function, but at least on Python
3 you will need to always operate in unicode.

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


Finding Application Folders
---------------------------

.. versionadded:: 2.0

Very often you want to open a config file that belongs to your
application.  However different operationg systems store these config
files by their policy in different places.  Click provides a
:func:`get_app_dir` function which returns the most appropriate location
for per user config files for your application depending on the OS.

Example usage::

    import os
    import click
    import ConfigParser

    APP_NAME = 'My Application'

    def read_config():
        cfg = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
        parser = ConfigParser.RawConfigParser()
        parser.read([cfg])
        rv = {}
        for section in parser.sections():
            for key, value in parser.items(section):
                rv['%s.%s' % (section, key)] = value
        return rv


Showing Progress Bars
---------------------

.. versionadded:: 2.0

Sometimes you have command line scripts that need to process a lot of data
but you want to quickly show the user some progress about how long that
will take.  Click supports simple progress bar rendering for that through
the :func:`progressbar` function.

The basic usage is very simple: the idea is that you have an iterable that
you want to operate on.  For each item in the iterable it might take some
time to do processing.  So say you have a loop like this::

    for user in all_the_users_to_process:
        modify_the_user(user)

To hook this up with an automatically updating progress bar all you need
to do is to change the code to this::

    import click

    with click.progressbar(all_the_users_to_process) as bar:
        for user in bar:
            modify_the_user(user)

Click will then automatically print a progress bar to the terminal and
calculate the remaining time for you.  The calculation of remaining time
requires that the iterable has a length.  If it does not have a length,
but you know the length, you can explicitly provide it::

    with click.progressbar(all_the_users_to_process,
                           length=number_of_users) as bar:
        for user in bar:
            modify_the_user(user)

Another useful feature is to associate a label with the progress bar which
will be shown before next to the progress bar::

    with click.progressbar(all_the_users_to_process,
                           label='Modifying user accounts',
                           length=number_of_users) as bar:
        for user in bar:
            modify_the_user(user)

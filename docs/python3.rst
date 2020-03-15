Python 3 Support
================

.. currentmodule:: click

Click supports Python 3, but like all other command line utility libraries,
it suffers from the Unicode text model in Python 3.  All examples in the
documentation were written so that they could run on both Python 2.x and
Python 3.4 or higher.

.. _python3-limitations:

Python 3 Limitations
--------------------

At the moment, Click suffers from a few problems with Python 3:

*   The command line in Unix traditionally is in bytes, not Unicode.  While
    there are encoding hints for all of this, there are generally some
    situations where this can break.  The most common one is SSH
    connections to machines with different locales.

    Misconfigured environments can currently cause a wide range of Unicode
    problems in Python 3 due to the lack of support for roundtripping
    surrogate escapes.  This will not be fixed in Click itself!

    For more information see :ref:`python3-surrogates`.

*   Standard input and output in Python 3 is opened in Unicode mode by
    default.  Click has to reopen the stream in binary mode in certain
    situations.  Because there is no standardized way to do this, this
    might not always work.  Primarily this can become a problem when
    testing command-line applications.

    This is not supported::

        sys.stdin = io.StringIO('Input here')
        sys.stdout = io.StringIO()

    Instead you need to do this::

        input = 'Input here'
        in_stream = io.BytesIO(input.encode('utf-8'))
        sys.stdin = io.TextIOWrapper(in_stream, encoding='utf-8')
        out_stream = io.BytesIO()
        sys.stdout = io.TextIOWrapper(out_stream, encoding='utf-8')

    Remember that in that case, you need to use ``out_stream.getvalue()``
    and not ``sys.stdout.getvalue()`` if you want to access the buffer
    contents as the wrapper will not forward that method.

Python 2 and 3 Differences
--------------------------

Click attempts to minimize the differences between Python 2 and Python 3
by following best practices for both languages.

In Python 2, the following is true:

*   ``sys.stdin``, ``sys.stdout``, and ``sys.stderr`` are opened in binary
    mode, but under some circumstances they support Unicode output.  Click
    attempts to not subvert this but provides support for forcing streams
    to be Unicode-based.
*   ``sys.argv`` is always byte-based.  Click will pass bytes to all
    input types and convert as necessary.  The :class:`STRING` type
    automatically will decode properly the input value into a string by
    trying the most appropriate encodings.
*   When dealing with files, Click will never go through the Unicode APIs
    and will instead use the operating system's byte APIs to open the
    files.

In Python 3, the following is true:

*   ``sys.stdin``, ``sys.stdout`` and ``sys.stderr`` are by default
    text-based.  When Click needs a binary stream, it attempts to discover
    the underlying binary stream.  See :ref:`python3-limitations` for how
    this works.
*   ``sys.argv`` is always Unicode-based.  This also means that the native
    type for input values to the types in Click is Unicode, and not bytes.

    This causes problems if the terminal is incorrectly set and Python
    does not figure out the encoding.  In that case, the Unicode string
    will contain error bytes encoded as surrogate escapes.
*   When dealing with files, Click will always use the Unicode file system
    API calls by using the operating system's reported or guessed
    filesystem encoding.  Surrogates are supported for filenames, so it
    should be possible to open files through the :class:`File` type even
    if the environment is misconfigured.

.. _python3-surrogates:

Python 3 Surrogate Handling
---------------------------

Click in Python 3 does all the Unicode handling in the standard library
and is subject to its behavior.  In Python 2, Click does all the Unicode
handling itself, which means there are differences in error behavior.

The most glaring difference is that in Python 2, Unicode will "just work",
while in Python 3, it requires extra care.  The reason for this is that in
Python 3, the encoding detection is done in the interpreter, and on Linux
and certain other operating systems, its encoding handling is problematic.

The biggest source of frustration is that Click scripts invoked by
init systems (sysvinit, upstart, systemd, etc.), deployment tools (salt,
puppet), or cron jobs (cron) will refuse to work unless a Unicode locale is
exported.

If Click encounters such an environment it will prevent further execution
to force you to set a locale.  This is done because Click cannot know
about the state of the system once it's invoked and restore the values
before Python's Unicode handling kicked in.

If you see something like this error in Python 3::

    Traceback (most recent call last):
      ...
    RuntimeError: Click will abort further execution because Python 3 was
      configured to use ASCII as encoding for the environment. Either switch
      to Python 2 or consult the Python 3 section of the docs for
      mitigation steps.

.. note::

    In Python 3.7 and later you will no longer get a ``RuntimeError`` in
    many cases thanks to :pep:`538` and :pep:`540`, which changed the
    default assumption in unconfigured environments.

You are dealing with an environment where Python 3 thinks you are
restricted to ASCII data.  The solution to these problems is different
depending on which locale your computer is running in.

For instance, if you have a German Linux machine, you can fix the problem
by exporting the locale to ``de_DE.utf-8``::

    export LC_ALL=de_DE.utf-8
    export LANG=de_DE.utf-8

If you are on a US machine, ``en_US.utf-8`` is the encoding of choice.  On
some newer Linux systems, you could also try ``C.UTF-8`` as the locale::

    export LC_ALL=C.UTF-8
    export LANG=C.UTF-8

On some systems it was reported that `UTF-8` has to be written as `UTF8`
and vice versa.  To see which locales are supported you can invoke
``locale -a``::

    locale -a

You need to do this before you invoke your Python script.  If you are
curious about the reasons for this, you can join the discussions in the
Python 3 bug tracker:

*   `ASCII is a bad filesystem default encoding
    <https://bugs.python.org/issue13643#msg149941>`_
*   `Use surrogateescape as default error handler
    <https://bugs.python.org/issue19977>`_
*   `Python 3 raises Unicode errors in the C locale
    <https://bugs.python.org/issue19846>`_
*   `LC_CTYPE=C:  pydoc leaves terminal in an unusable state
    <https://bugs.python.org/issue21398>`_ (this is relevant to Click
    because the pager support is provided by the stdlib pydoc module)

Note (Python 3.7 onwards): Even though your locale may not be properly
configured, Python 3.7 Click will not raise the above exception because Python
3.7 programs are better at choosing default locales.  This doesn't change the
general issue that your locale may be misconfigured.

Unicode Literals
----------------

Starting with Click 5.0 there will be a warning for the use of the
``unicode_literals`` future import in Python 2.  This has been done due to
the negative consequences of this import with regards to unintentionally
causing bugs due to introducing Unicode data to APIs that are incapable of
handling them.  For some examples of this issue, see the discussion on
this github issue: `python-future#22
<https://github.com/PythonCharmers/python-future/issues/22>`_.

If you use ``unicode_literals`` in any file that defines a Click command
or that invokes a click command you will be given a warning.  You are
strongly encouraged to not use ``unicode_literals`` and instead use
explicit ``u`` prefixes for your Unicode strings.

If you do want to ignore the warning and continue using
``unicode_literals`` on your own peril, you can disable the warning as
follows::

    import click
    click.disable_unicode_literals_warning = True

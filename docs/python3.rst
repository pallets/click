Python 3 Support
================

.. currentmodule:: click

Click supports Python 3 but like all other command line utility libraries,
it suffers from the Unicode text model in Python 3.  All examples in the
documentation were written so that they run on both Python 2.x and
Python 3.3 or higher.

At the moment the strong recommendation is to use Python 2 for these
utilities unless Python 3 is a hard requirement.

.. _python3-limitations:

Python 3 Limitations
--------------------

At the moment click suffers from a few problems on Python 3:

*   The command line in Unix traditionally is in bytes and not unicode.
    While there are encoding hints for all of this, there are generally
    some situations where this can break.  The most common one is SSH
    connections to machines with different locales.

    Misconfigured environments can currently cause a wide range of unicode
    problems on Python 3 due to the lack of support for roundtripping
    surrogate escapes.  This will be fixed on a case-by-case basis going
    forward.

*   Standard input and output on Python 3 is opened in unicode mode by
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

    Remember that in that case you need to use ``out_stream.getvalue()``
    and not ``sys.stdout.getvalue()`` if you want to access the buffer
    contents as the wrapper will not forward that method.

Python 2 / 3 Differences
------------------------

Click attempts to minimize the differences between Python 2 and Python 3
by following the best practices for both languages.

On Python 2 the following is true:

*   ``sys.stdin``, ``sys.stdout``, and ``sys.stderr`` are opened in binary
    mode but under some circumstances they support unicode output.  Click
    attempts to not subvert this but provides support for forcing streams
    to be unicode-based.
*   ``sys.argv`` is always bytes-based.  Click will pass bytes to all
    input types and convert as necessary.  The :class:`STRING` type
    automatically will decode properly the input value into a string by
    trying the most appropriate encodings.
*   When dealing with files, click will never go through the unicode APIs
    and will instead use the operating system's byte APIs to open the
    files.

On Python 3 the following is true:

*   ``sys.stdin``, ``sys.stdout`` and ``sys.stderr`` are by default
    text-based.  When click needs a binary stream, it attempts to discover
    the underlying binary stream.  See :ref:`python3-limitations` for how
    this works.
*   ``sys.argv`` is always unicode-based.  This also means that the native
    type for input values to the types in click is unicode and not bytes.

    This causes problems when the terminal is incorrectly set and Python
    does not figure out the encoding.  In that case the unicode string
    will contain error bytes encoded as surrogate escapes.
*   When dealing with files, click will always use the unicode file system
    API calls by using the operating system's reported or guessed
    filesystem encoding.  Surrogates are supported for filenames, so it
    should be possible to open files through the :class:`File` type even
    if the environment is misconfigured.

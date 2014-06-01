import os
import sys
from collections import deque

from ._compat import text_type, open_stream, get_streerror, string_types, \
     PY2, binary_streams, text_streams, filename_to_ui, \
     auto_wrap_for_ansi, strip_ansi, isatty, _default_text_stdout, \
     is_bytes

if not PY2:
    from ._compat import _find_binary_writer


echo_native_types = string_types + (bytes, bytearray)


def _posixify(name):
    return '-'.join(name.split()).lower()


def unpack_args(args, nargs_spec):
    """Given an iterable of arguments and an iterable of nargs specifications
    it returns a tuple with all the unpacked arguments at the first index
    and all remaining arguments as the second.

    The nargs specification is the number of arguments that should be consumed
    or `-1` to indicate that this position should eat up all the remainders.

    Missing items are filled with `None`.

    Examples:

    >>> unpack_args(range(6), [1, 2, 1, -1])
    ((0, (1, 2), 3, (4, 5)), [])
    >>> unpack_args(range(6), [1, 2, 1])
    ((0, (1, 2), 3), [4, 5])
    >>> unpack_args(range(6), [-1])
    (((0, 1, 2, 3, 4, 5),), [])
    >>> unpack_args(range(6), [1, 1])
    ((0, 1), [2, 3, 4, 5])
    """
    args = deque(args)
    nargs_spec = deque(nargs_spec)
    rv = []
    spos = None

    def _fetch(c):
        try:
            return (spos is not None and c.pop() or c.popleft())
        except IndexError:
            return None

    while nargs_spec:
        nargs = _fetch(nargs_spec)
        if nargs == 1:
            rv.append(_fetch(args))
        elif nargs > 1:
            x = [_fetch(args) for _ in range(nargs)]
            # If we're reversed we're pulling in the arguments in reverse
            # so we need to turn them around.
            if spos is not None:
                x.reverse()
            rv.append(tuple(x))
        elif nargs < 0:
            if spos is not None:
                raise TypeError('Cannot have two nargs < 0')
            spos = len(rv)
            rv.append(None)

    # spos is the position of the wildcard (star).  If it's not None
    # we fill it with the remainder.
    if spos is not None:
        rv[spos] = tuple(args)
        args = []

    return rv, list(args)


def safecall(func):
    """Wraps a function so that it swallows exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
    return wrapper


def make_str(value):
    """Converts a value into a valid string."""
    if isinstance(value, bytes):
        try:
            return value.decode(sys.getfilesystemencoding())
        except UnicodeError:
            return value.decode('utf-8', 'replace')
    return text_type(value)


def make_default_short_help(help, max_length=45):
    words = help.split()
    total_length = 0
    result = []
    done = False

    for word in words:
        if '.' in word:
            word = word.split('.', 1)[0] + '.'
            done = True
        new_length = result and 1 + len(word) or len(word)
        if total_length + new_length > max_length:
            result.append('...')
            done = True
        else:
            if result:
                result.append(' ')
            result.append(word)
        if done:
            break
        total_length += new_length

    return ''.join(result)


class LazyFile(object):
    """A lazy file works like a regular file but it does not fully open
    the file but it does perform some basic checks early to see if the
    filename parameter does make sense.  This is useful for safely opening
    files for writing.
    """

    def __init__(self, filename, mode='r', encoding=None, errors='strict',
                 atomic=False):
        self.name = filename
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.atomic = atomic

        if filename == '-':
            self._f, self.should_close = open_stream(filename, mode,
                                                     encoding, errors)
        else:
            if 'r' in mode:
                # Open and close the file in case we're opening it for
                # reading so that we can catch at least some errors in
                # some cases early.
                open(filename, mode).close()
            self._f = None
            self.should_close = True

    def __getattr__(self, name):
        return getattr(self.open(), name)

    def __repr__(self):
        if self._f is not None:
            return repr(self._f)
        return '<unopened file %r %s>' % (self.name, self.mode)

    def open(self):
        """Opens the file if it's not yet open.  This call might fail with
        a :exc:`FileError`.  Not handling this error will produce an error
        that click shows.
        """
        if self._f is not None:
            return self._f
        try:
            rv, self.should_close = open_stream(self.name, self.mode,
                                                self.encoding,
                                                self.errors,
                                                atomic=self.atomic)
        except (IOError, OSError) as e:
            from .exceptions import FileError
            raise FileError(self.name, hint=get_streerror(e))
        self._f = rv
        return rv

    def close(self):
        """Closes the underlying file, no matter what."""
        if self._f is not None:
            self._f.close()

    def close_intelligently(self):
        """This function only closes the file if it was opened by the lazy
        file wrapper.  For instance this will never close stdin.
        """
        if self.should_close:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close_intelligently()


def echo(message=None, file=None, nl=True):
    """Prints a message plus a newline to the given file or stdout.  On
    first sight this looks like the print function but it has improved
    support for handling unicode and binary data that does not fail no
    matter how badly configured the system is.

    Primarily it means that you can print binary data as well as unicode
    data on both 2.x and 3.x to the given file in the most appropriate way
    possible.  This is a very carefree function as in that it will try its
    best to not fail.

    In addition to that if `colorama`_ is installed the echo function will
    also support clever handling of ANSI codes.  Essentially it will then
    do the following:

    -   add transparent handling of ANSI color codes on Windows.
    -   hide ANSI codes automatically if the destination file is not a
        terminal.

    .. _colorama: http://pypi.python.org/pypi/colorama

    .. versionchanged:: 2.0
       Starting with version 2.0 of click, the echo function will work
       with colorama if it's installed.

    :param message: the message to print
    :param file: the file to write to (defaults to ``stdout``)
    :param nl: if set to `True` (the default) a newline is printed afterwards.
    """
    if file is None:
        file = _default_text_stdout()

    # Convert non bytes/text into the native string type.
    if message is not None and not isinstance(message, echo_native_types):
        message = text_type(message)

    # If there is a message, and we're on python 3, and the value looks
    # like bytes we manually need to find the binary stream and write the
    # message in there.  This is done separately so that most stream
    # types will work as you would expect.  Eg: you can write to StringIO
    # for other cases.
    if message and not PY2 and is_bytes(message):
        binary_file = _find_binary_writer(file)
        if binary_file is not None:
            file.flush()
            binary_file.write(message)
            if nl:
                binary_file.write(b'\n')
            binary_file.flush()
            return

    # ANSI style support.  If there is no message or we are dealing with
    # bytes nothing is happening.  If we are connected to a file we want
    # to strip colors.  If we have support for wrapping streams (windows
    # through colorama) we want to do that.
    if message and not is_bytes(message):
        if not isatty(file):
            message = strip_ansi(message)
        elif auto_wrap_for_ansi is not None:
            file = auto_wrap_for_ansi(file)

    if message:
        file.write(message)
    if nl:
        file.write('\n')
    file.flush()


def get_binary_stream(name):
    """Returns a system stream for byte processing.  This essentially
    returns the stream from the sys module with the given name but it
    solves some compatibility issues between different Python versions.
    Primarily this function is necessary for getting binary streams on
    Python 3.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    """
    opener = binary_streams.get(name)
    if opener is None:
        raise TypeError('Unknown standard stream %r' % name)
    return opener()


def get_text_stream(name, encoding=None, errors='strict'):
    """Returns a system stream for text processing.  This usually returns
    a wrapped stream around a binary stream returned from
    :func:`get_binary_stream` but it also can take shortcuts on Python 3
    for already correctly configured streams.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    :param encoding: overrides the detected default encoding.
    :param errors: overrides the default error mode.
    """
    opener = text_streams.get(name)
    if opener is None:
        raise TypeError('Unknown standard stream %r' % name)
    return opener(encoding, errors)


def format_filename(filename, shorten=False):
    """Formats a filename for user display.  The main purpose of this
    function is to ensure that the filename can be displayed at all.  This
    will decode the filename to unicode if necessary in a way that it will
    not fail.  Optionally it can shorten the filename to not include the
    full path to the filename.

    :param filename: formats a filename for UI display.  This will also convert
                     the filename into unicode without failing.
    :param shorten: this optionally shortens the filename to strip of the
                    path that leads up to it.
    """
    if shorten:
        filename = os.path.basename(filename)
    return filename_to_ui(filename)


def get_app_dir(app_name, roaming=True, force_posix=False):
    r"""Returns the config folder for the application.  The default behavior
    is to return whatever is most appropriate for the operating system.

    To give you an idea, for an app called ``"Foo Bar"`` something like
    the following folders could be returned:

    Mac OS X:
      ``~/Library/Application Support/Foo Bar``
    Mac OS X (POSIX):
      ``~/.foo-bar``
    Unix:
      ``~/.config/foo-bar``
    Unix (POSIX):
      ``~/.foo-bar``
    Win XP (roaming):
      ``C:\Documents and Settings\<user>\Local Settings\Application Data\Foo Bar``
    Win XP (not roaming):
      ``C:\Documents and Settings\<user>\Application Data\Foo Bar``
    Win 7 (roaming):
      ``C:\Users\<user>\AppData\Roaming\Foo Bar``
    Win 7 (not roaming):
      ``C:\Users\<user>\AppData\Local\Foo Bar``

    .. versionadded:: 2.0

    :param app_name: the application name.  This should be properly capitalized
                     and can contain whitespace.
    :param roaming: controls if the folder should be roaming or not on windows.
                    Has no affect otherwise.
    :param force_posix: if this is set to `True` then on any posix system the
                        folder will be stored in the home folder with a leading
                        dot instead of the XDG config home or darwin's
                        application support folder.
    """
    if sys.platform.startswith('win'):
        key = roaming and 'APPDATA' or 'LOCALAPPDATA'
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser('~')
        return os.path.join(folder, app_name)
    if force_posix:
        return os.path.join(os.path.expanduser('~/.' + _posixify(app_name)))
    if sys.platform == 'darwin':
        return os.path.join(os.path.expanduser(
            '~/Library/Application Support'), app_name)
    return os.path.join(
        os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')),
        _posixify(app_name))

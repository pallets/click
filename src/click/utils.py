import os
import sys

from ._compat import _default_text_stderr
from ._compat import _default_text_stdout
from ._compat import _find_binary_writer
from ._compat import auto_wrap_for_ansi
from ._compat import binary_streams
from ._compat import filename_to_ui
from ._compat import get_filesystem_encoding
from ._compat import get_strerror
from ._compat import is_bytes
from ._compat import open_stream
from ._compat import should_strip_ansi
from ._compat import strip_ansi
from ._compat import text_streams
from ._compat import WIN
from .globals import resolve_color_default


echo_native_types = (str, bytes, bytearray)


def _posixify(name):
    return "-".join(name.split()).lower()


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
            return value.decode(get_filesystem_encoding())
        except UnicodeError:
            return value.decode("utf-8", "replace")
    return str(value)


def make_default_short_help(help, max_length=45):
    """Return a condensed version of help string."""
    line_ending = help.find("\n\n")
    if line_ending != -1:
        help = help[:line_ending]
    words = help.split()
    total_length = 0
    result = []
    done = False

    for word in words:
        if word[-1:] == ".":
            done = True
        new_length = 1 + len(word) if result else len(word)
        if total_length + new_length > max_length:
            result.append("...")
            done = True
        else:
            if result:
                result.append(" ")
            result.append(word)
        if done:
            break
        total_length += new_length

    return "".join(result)


class LazyFile:
    """A lazy file works like a regular file but it does not fully open
    the file but it does perform some basic checks early to see if the
    filename parameter does make sense.  This is useful for safely opening
    files for writing.
    """

    def __init__(
        self, filename, mode="r", encoding=None, errors="strict", atomic=False
    ):
        self.name = filename
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.atomic = atomic

        if filename == "-":
            self._f, self.should_close = open_stream(filename, mode, encoding, errors)
        else:
            if "r" in mode:
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
        return f"<unopened file '{self.name}' {self.mode}>"

    def open(self):
        """Opens the file if it's not yet open.  This call might fail with
        a :exc:`FileError`.  Not handling this error will produce an error
        that Click shows.
        """
        if self._f is not None:
            return self._f
        try:
            rv, self.should_close = open_stream(
                self.name, self.mode, self.encoding, self.errors, atomic=self.atomic
            )
        except OSError as e:  # noqa: E402
            from .exceptions import FileError

            raise FileError(self.name, hint=get_strerror(e))
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

    def __iter__(self):
        self.open()
        return iter(self._f)


class KeepOpenFile:
    def __init__(self, file):
        self._file = file

    def __getattr__(self, name):
        return getattr(self._file, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        pass

    def __repr__(self):
        return repr(self._file)

    def __iter__(self):
        return iter(self._file)


def echo(message=None, file=None, nl=True, err=False, color=None):
    """Prints a message plus a newline to the given file or stdout.  On
    first sight, this looks like the print function, but it has improved
    support for handling Unicode and binary data that does not fail no
    matter how badly configured the system is.

    Primarily it means that you can print binary data as well as Unicode
    data on both 2.x and 3.x to the given file in the most appropriate way
    possible.  This is a very carefree function in that it will try its
    best to not fail.  As of Click 6.0 this includes support for unicode
    output on the Windows console.

    In addition to that, if `colorama`_ is installed, the echo function will
    also support clever handling of ANSI codes.  Essentially it will then
    do the following:

    -   add transparent handling of ANSI color codes on Windows.
    -   hide ANSI codes automatically if the destination file is not a
        terminal.

    .. _colorama: https://pypi.org/project/colorama/

    .. versionchanged:: 6.0
       As of Click 6.0 the echo function will properly support unicode
       output on the windows console.  Not that click does not modify
       the interpreter in any way which means that `sys.stdout` or the
       print statement or function will still not provide unicode support.

    .. versionchanged:: 2.0
       Starting with version 2.0 of Click, the echo function will work
       with colorama if it's installed.

    .. versionadded:: 3.0
       The `err` parameter was added.

    .. versionchanged:: 4.0
       Added the `color` flag.

    :param message: the message to print
    :param file: the file to write to (defaults to ``stdout``)
    :param err: if set to true the file defaults to ``stderr`` instead of
                ``stdout``.  This is faster and easier than calling
                :func:`get_text_stderr` yourself.
    :param nl: if set to `True` (the default) a newline is printed afterwards.
    :param color: controls if the terminal supports ANSI colors or not.  The
                  default is autodetection.
    """
    if file is None:
        if err:
            file = _default_text_stderr()
        else:
            file = _default_text_stdout()

    # Convert non bytes/text into the native string type.
    if message is not None and not isinstance(message, echo_native_types):
        message = str(message)

    if nl:
        message = message or ""
        if isinstance(message, str):
            message += "\n"
        else:
            message += b"\n"

    # If there is a message and the value looks like bytes, we manually
    # need to find the binary stream and write the message in there.
    # This is done separately so that most stream types will work as you
    # would expect. Eg: you can write to StringIO for other cases.
    if message and is_bytes(message):
        binary_file = _find_binary_writer(file)
        if binary_file is not None:
            file.flush()
            binary_file.write(message)
            binary_file.flush()
            return

    # ANSI-style support.  If there is no message or we are dealing with
    # bytes nothing is happening.  If we are connected to a file we want
    # to strip colors.  If we are on windows we either wrap the stream
    # to strip the color or we use the colorama support to translate the
    # ansi codes to API calls.
    if message and not is_bytes(message):
        color = resolve_color_default(color)
        if should_strip_ansi(file, color):
            message = strip_ansi(message)
        elif WIN:
            if auto_wrap_for_ansi is not None:
                file = auto_wrap_for_ansi(file)
            elif not color:
                message = strip_ansi(message)

    if message:
        file.write(message)
    file.flush()


def get_binary_stream(name):
    """Returns a system stream for byte processing.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    """
    opener = binary_streams.get(name)
    if opener is None:
        raise TypeError(f"Unknown standard stream '{name}'")
    return opener()


def get_text_stream(name, encoding=None, errors="strict"):
    """Returns a system stream for text processing.  This usually returns
    a wrapped stream around a binary stream returned from
    :func:`get_binary_stream` but it also can take shortcuts for already
    correctly configured streams.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    :param encoding: overrides the detected default encoding.
    :param errors: overrides the default error mode.
    """
    opener = text_streams.get(name)
    if opener is None:
        raise TypeError(f"Unknown standard stream '{name}'")
    return opener(encoding, errors)


def open_file(
    filename, mode="r", encoding=None, errors="strict", lazy=False, atomic=False
):
    """This is similar to how the :class:`File` works but for manual
    usage.  Files are opened non lazy by default.  This can open regular
    files as well as stdin/stdout if ``'-'`` is passed.

    If stdin/stdout is returned the stream is wrapped so that the context
    manager will not close the stream accidentally.  This makes it possible
    to always use the function like this without having to worry to
    accidentally close a standard stream::

        with open_file(filename) as f:
            ...

    .. versionadded:: 3.0

    :param filename: the name of the file to open (or ``'-'`` for stdin/stdout).
    :param mode: the mode in which to open the file.
    :param encoding: the encoding to use.
    :param errors: the error handling for this file.
    :param lazy: can be flipped to true to open the file lazily.
    :param atomic: in atomic mode writes go into a temporary file and it's
                   moved on close.
    """
    if lazy:
        return LazyFile(filename, mode, encoding, errors, atomic=atomic)
    f, should_close = open_stream(filename, mode, encoding, errors, atomic=atomic)
    if not should_close:
        f = KeepOpenFile(f)
    return f


def get_os_args():
    """Returns the argument part of ``sys.argv``, removing the first
    value which is the name of the script.

    .. deprecated:: 8.0
        Will be removed in 8.1. Access ``sys.argv[1:]`` directly
        instead.
    """
    import warnings

    warnings.warn(
        "'get_os_args' is deprecated and will be removed in 8.1. Access"
        " 'sys.argv[1:]' directly instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return sys.argv[1:]


def format_filename(filename, shorten=False):
    """Formats a filename for user display.  The main purpose of this
    function is to ensure that the filename can be displayed at all.  This
    will decode the filename to unicode if necessary in a way that it will
    not fail.  Optionally, it can shorten the filename to not include the
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

    To give you an idea, for an app called ``"Foo Bar"``, something like
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
    :param roaming: controls if the folder should be roaming or not on Windows.
                    Has no affect otherwise.
    :param force_posix: if this is set to `True` then on any POSIX system the
                        folder will be stored in the home folder with a leading
                        dot instead of the XDG config home or darwin's
                        application support folder.
    """
    if WIN:
        key = "APPDATA" if roaming else "LOCALAPPDATA"
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser("~")
        return os.path.join(folder, app_name)
    if force_posix:
        return os.path.join(os.path.expanduser(f"~/.{_posixify(app_name)}"))
    if sys.platform == "darwin":
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"), app_name
        )
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        _posixify(app_name),
    )


class PacifyFlushWrapper:
    """This wrapper is used to catch and suppress BrokenPipeErrors resulting
    from ``.flush()`` being called on broken pipe during the shutdown/final-GC
    of the Python interpreter. Notably ``.flush()`` is always called on
    ``sys.stdout`` and ``sys.stderr``. So as to have minimal impact on any
    other cleanup code, and the case where the underlying file is not a broken
    pipe, all calls and attributes are proxied.
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def flush(self):
        try:
            self.wrapped.flush()
        except OSError as e:
            import errno

            if e.errno != errno.EPIPE:
                raise

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr)


def _detect_program_name(path=None, _main=sys.modules["__main__"]):
    """Determine the command used to run the program, for use in help
    text. If a file or entry point was executed, the file name is
    returned. If ``python -m`` was used to execute a module or package,
    ``python -m name`` is returned.

    This doesn't try to be too precise, the goal is to give a concise
    name for help text. Files are only shown as their name without the
    path. ``python`` is only shown for modules, and the full path to
    ``sys.executable`` is not shown.

    :param path: The Python file being executed. Python puts this in
        ``sys.argv[0]``, which is used by default.
    :param _main: The ``__main__`` module. This should only be passed
        during internal testing.

    .. versionadded:: 8.0
        Based on command args detection in the Werkzeug reloader.

    :meta private:
    """
    if not path:
        path = sys.argv[0]

    # The value of __package__ indicates how Python was called. It may
    # not exist if a setuptools script is installed as an egg. It may be
    # set incorrectly for entry points created with pip on Windows.
    if getattr(_main, "__package__", None) is None or (
        os.name == "nt"
        and _main.__package__ == ""
        and not os.path.exists(path)
        and os.path.exists(f"{path}.exe")
    ):
        # Executed a file, like "python app.py".
        return os.path.basename(path)

    # Executed a module, like "python -m example".
    # Rewritten by Python from "-m script" to "/path/to/script.py".
    # Need to look at main module to determine how it was executed.
    py_module = _main.__package__
    name = os.path.splitext(os.path.basename(path))[0]

    # A submodule like "example.cli".
    if name != "__main__":
        py_module = f"{py_module}.{name}"

    return f"python -m {py_module.lstrip('.')}"

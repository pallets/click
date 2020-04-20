# This module is based on the excellent work by Adam Bartoš who
# provided a lot of what went into the implementation here in
# the discussion to issue1602 in the Python bug tracker.
#
# There are some general differences in regards to how this works
# compared to the original patches as we do not need to patch
# the entire interpreter but just work in our little world of
# echo and prompt.
import ctypes
import io
import time
from ctypes import byref
from ctypes import c_char
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_ssize_t
from ctypes import c_ulong
from ctypes import c_void_p
from ctypes import POINTER
from ctypes import py_object
from ctypes import windll
from ctypes import WINFUNCTYPE
from ctypes.wintypes import DWORD
from ctypes.wintypes import HANDLE
from ctypes.wintypes import LPCWSTR
from ctypes.wintypes import LPWSTR

import msvcrt

from ._compat import _NonClosingTextIOWrapper

try:
    from ctypes import pythonapi
except ImportError:
    pythonapi = None
else:
    PyObject_GetBuffer = pythonapi.PyObject_GetBuffer
    PyBuffer_Release = pythonapi.PyBuffer_Release


c_ssize_p = POINTER(c_ssize_t)

kernel32 = windll.kernel32
GetStdHandle = kernel32.GetStdHandle
ReadConsoleW = kernel32.ReadConsoleW
WriteConsoleW = kernel32.WriteConsoleW
GetConsoleMode = kernel32.GetConsoleMode
GetLastError = kernel32.GetLastError
GetCommandLineW = WINFUNCTYPE(LPWSTR)(("GetCommandLineW", windll.kernel32))
CommandLineToArgvW = WINFUNCTYPE(POINTER(LPWSTR), LPCWSTR, POINTER(c_int))(
    ("CommandLineToArgvW", windll.shell32)
)
LocalFree = WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p)(
    ("LocalFree", windll.kernel32)
)


STDIN_HANDLE = GetStdHandle(-10)
STDOUT_HANDLE = GetStdHandle(-11)
STDERR_HANDLE = GetStdHandle(-12)


PyBUF_SIMPLE = 0
PyBUF_WRITABLE = 1

ERROR_SUCCESS = 0
ERROR_NOT_ENOUGH_MEMORY = 8
ERROR_OPERATION_ABORTED = 995

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

EOF = b"\x1a"
MAX_BYTES_WRITTEN = 32767


class Py_buffer(ctypes.Structure):
    _fields_ = [
        ("buf", c_void_p),
        ("obj", py_object),
        ("len", c_ssize_t),
        ("itemsize", c_ssize_t),
        ("readonly", c_int),
        ("ndim", c_int),
        ("format", c_char_p),
        ("shape", c_ssize_p),
        ("strides", c_ssize_p),
        ("suboffsets", c_ssize_p),
        ("internal", c_void_p),
    ]


# On PyPy we cannot get buffers so our ability to operate here is
# severely limited.
if pythonapi is None:
    get_buffer = None
else:

    def get_buffer(obj, writable=False):
        buf = Py_buffer()
        flags = PyBUF_WRITABLE if writable else PyBUF_SIMPLE
        PyObject_GetBuffer(py_object(obj), byref(buf), flags)
        try:
            buffer_type = c_char * buf.len
            return buffer_type.from_address(buf.buf)
        finally:
            PyBuffer_Release(byref(buf))


class _WindowsConsoleRawIOBase(io.RawIOBase):
    def __init__(self, handle):
        self.handle = handle

    def isatty(self):
        io.RawIOBase.isatty(self)
        return True


class _WindowsConsoleReader(_WindowsConsoleRawIOBase):
    def readable(self):
        return True

    def readinto(self, b):
        bytes_to_be_read = len(b)
        if not bytes_to_be_read:
            return 0
        elif bytes_to_be_read % 2:
            raise ValueError(
                "cannot read odd number of bytes from UTF-16-LE encoded console"
            )

        buffer = get_buffer(b, writable=True)
        code_units_to_be_read = bytes_to_be_read // 2
        code_units_read = c_ulong()

        rv = ReadConsoleW(
            HANDLE(self.handle),
            buffer,
            code_units_to_be_read,
            byref(code_units_read),
            None,
        )
        if GetLastError() == ERROR_OPERATION_ABORTED:
            # wait for KeyboardInterrupt
            time.sleep(0.1)
        if not rv:
            raise OSError(f"Windows error: {GetLastError()}")

        if buffer[0] == EOF:
            return 0
        return 2 * code_units_read.value


class _WindowsConsoleWriter(_WindowsConsoleRawIOBase):
    def writable(self):
        return True

    @staticmethod
    def _get_error_message(errno):
        if errno == ERROR_SUCCESS:
            return "ERROR_SUCCESS"
        elif errno == ERROR_NOT_ENOUGH_MEMORY:
            return "ERROR_NOT_ENOUGH_MEMORY"
        return f"Windows error {errno}"

    def write(self, b):
        bytes_to_be_written = len(b)
        buf = get_buffer(b)
        code_units_to_be_written = min(bytes_to_be_written, MAX_BYTES_WRITTEN) // 2
        code_units_written = c_ulong()

        WriteConsoleW(
            HANDLE(self.handle),
            buf,
            code_units_to_be_written,
            byref(code_units_written),
            None,
        )
        bytes_written = 2 * code_units_written.value

        if bytes_written == 0 and bytes_to_be_written > 0:
            raise OSError(self._get_error_message(GetLastError()))
        return bytes_written


class ConsoleStream:
    def __init__(self, text_stream, byte_stream):
        self._text_stream = text_stream
        self.buffer = byte_stream

    @property
    def name(self):
        return self.buffer.name

    def write(self, x):
        if isinstance(x, str):
            return self._text_stream.write(x)
        try:
            self.flush()
        except Exception:
            pass
        return self.buffer.write(x)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def __getattr__(self, name):
        return getattr(self._text_stream, name)

    def isatty(self):
        return self.buffer.isatty()

    def __repr__(self):
        return "<ConsoleStream name={!r} encoding={!r}>".format(
            self.name, self.encoding
        )


class WindowsChunkedWriter:
    """
    Wraps a stream (such as stdout), acting as a transparent proxy for all
    attribute access apart from method 'write()' which we wrap to write in
    limited chunks due to a Windows limitation on binary console streams.
    """

    def __init__(self, wrapped):
        # double-underscore everything to prevent clashes with names of
        # attributes on the wrapped stream object.
        self.__wrapped = wrapped

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

    def write(self, text):
        total_to_write = len(text)
        written = 0

        while written < total_to_write:
            to_write = min(total_to_write - written, MAX_BYTES_WRITTEN)
            self.__wrapped.write(text[written : written + to_write])
            written += to_write


def _get_text_stdin(buffer_stream):
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedReader(_WindowsConsoleReader(STDIN_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return ConsoleStream(text_stream, buffer_stream)


def _get_text_stdout(buffer_stream):
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedWriter(_WindowsConsoleWriter(STDOUT_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return ConsoleStream(text_stream, buffer_stream)


def _get_text_stderr(buffer_stream):
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedWriter(_WindowsConsoleWriter(STDERR_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return ConsoleStream(text_stream, buffer_stream)


_stream_factories = {
    0: _get_text_stdin,
    1: _get_text_stdout,
    2: _get_text_stderr,
}


def _is_console(f):
    if not hasattr(f, "fileno"):
        return False

    try:
        fileno = f.fileno()
    except OSError:
        return False

    handle = msvcrt.get_osfhandle(fileno)
    return bool(GetConsoleMode(handle, byref(DWORD())))


def _get_windows_console_stream(f, encoding, errors):
    if (
        get_buffer is not None
        and encoding in {"utf-16-le", None}
        and errors in {"strict", None}
        and _is_console(f)
    ):
        func = _stream_factories.get(f.fileno())
        if func is not None:
            f = getattr(f, "buffer", None)

            if f is None:
                return None

            return func(f)

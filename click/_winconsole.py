# -*- coding: utf-8 -*-
# This module is based on the excellent work by Adam Bartoš who
# provided a lot of what went into the implementation here in
# the discussion to issue1602 in the Python bug tracker.
#
# There are some general differences in regards to how this works
# compared to the original patches as we do not need to patch
# the entire interpreter but just work in our little world of
# echo and prmopt.

import io
import sys
import ctypes
from click._compat import _NonClosingTextIOWrapper, text_type
from ctypes import byref, POINTER, pythonapi, c_int, c_char, c_char_p, \
     c_void_p, py_object, c_ssize_t, c_ulong, windll, WINFUNCTYPE
from ctypes.wintypes import LPWSTR, LPCWSTR


PY2 = sys.version_info[0] == 2

c_ssize_p = POINTER(c_ssize_t)

PyObject_GetBuffer = pythonapi.PyObject_GetBuffer
PyBuffer_Release = pythonapi.PyBuffer_Release

kernel32 = windll.kernel32
GetStdHandle = kernel32.GetStdHandle
ReadConsoleW = kernel32.ReadConsoleW
WriteConsoleW = kernel32.WriteConsoleW
GetLastError = kernel32.GetLastError
GetCommandLineW = WINFUNCTYPE(LPWSTR)(
    ('GetCommandLineW', windll.kernel32))
CommandLineToArgvW = WINFUNCTYPE(
    POINTER(LPWSTR), LPCWSTR, POINTER(c_int))(
        ('CommandLineToArgvW', windll.shell32))


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

EOF = b'\x1a'
MAX_BYTES_WRITTEN = 32767


class Py_buffer(ctypes.Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('obj', py_object),
        ('len', c_ssize_t),
        ('itemsize', c_ssize_t),
        ('readonly', c_int),
        ('ndim', c_int),
        ('format', c_char_p),
        ('shape', c_ssize_p),
        ('strides', c_ssize_p),
        ('suboffsets', c_ssize_p),
        ('internal', c_void_p)
    ]

    if PY2:
        _fields_.insert(-1, ('smalltable', c_ssize_t * 2))


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
        super(WindowsConsoleRawIOBase, self).isatty()
        return True


class _WindowsConsoleReader(_WindowsConsoleRawIOBase):

    def readable(self):
        return True

    def readinto(self, b):
        bytes_to_be_read = len(b)
        if not bytes_to_be_read:
            return 0
        elif bytes_to_be_read % 2:
            raise ValueError('cannot read odd number of bytes from '
                             'UTF-16-LE encoded console')

        buffer = get_buffer(b, writable=True)
        code_units_to_be_read = bytes_to_be_read // 2
        code_units_read = c_ulong()

        rv = ReadConsoleW(self.handle, buffer, code_units_to_be_read,
                          byref(code_units_read), None)
        if GetLastError() == ERROR_OPERATION_ABORTED:
            # wait for KeyboardInterrupt
            time.sleep(0.1)
        if not rv:
            raise OSError('Windows error: %s' % GetLastError())

        if buffer[0] == EOF:
            return 0
        return 2 * code_units_read.value


class _WindowsConsoleWriter(_WindowsConsoleRawIOBase):

    def writable(self):
        return True

    @staticmethod
    def _get_error_message(errno):
        if errno == ERROR_SUCCESS:
            return 'ERROR_SUCCESS'
        elif errno == ERROR_NOT_ENOUGH_MEMORY:
            return 'ERROR_NOT_ENOUGH_MEMORY'
        return 'Windows error %s' % errno

    def write(self, b):
        bytes_to_be_written = len(b)
        buf = get_buffer(b)
        code_units_to_be_written = min(bytes_to_be_written,
                                       MAX_BYTES_WRITTEN) // 2
        code_units_written = c_ulong()

        WriteConsoleW(self.handle, buf, code_units_to_be_written,
                      byref(code_units_written), None)
        bytes_written = 2 * code_units_written.value

        if bytes_written == 0 and bytes_to_be_written > 0:
            raise OSError(self._get_error_message(GetLastError()))
        return bytes_written


class ConsoleStream(object):

    def __init__(self, text_stream, byte_stream):
        self._text_stream = text_stream
        self.buffer = byte_stream

    @property
    def name(self):
        return self.buffer.name

    def write(self, x):
        if isinstance(x, text_type):
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
        return '<ConsoleStream name=%r encoding=%r>' % (
            self.name,
            self.encoding,
        )


def _get_text_stdin():
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedReader(_WindowsConsoleReader(STDIN_HANDLE)),
        'utf-16-le', 'strict', line_buffering=True)
    return ConsoleStream(text_stream, sys.stdin)


def _get_text_stdout():
    text_stream = _NonClosingTextIOWrapper(
        _WindowsConsoleWriter(STDOUT_HANDLE),
        'utf-16-le', 'strict', line_buffering=True)
    return ConsoleStream(text_stream, sys.stdout)


def _get_text_stderr():
    text_stream = _NonClosingTextIOWrapper(
        _WindowsConsoleWriter(STDERR_HANDLE),
        'utf-16-le', 'strict', line_buffering=True)
    return ConsoleStream(text_stream, sys.stderr)


def _get_windows_argv():
    argc = c_int(0)
    argv_unicode = CommandLineToArgvW(GetCommandLineW(), byref(argc))
    argv = [argv_unicode[i] for i in range(0, argc.value)]

    if not hasattr(sys, 'frozen'):
        argv = argv[1:]
        while len(argv) > 0:
            arg = argv[0]
            if not arg.startswith('-') or arg == '-':
                break
            argv = argv[1:]
            if arg == '-m':
                break
            if arg == '-c':
                argv[0] = u'-c'
                break

    return argv


_stream_factories = {
    0: _get_text_stdin,
    1: _get_text_stdout,
    2: _get_text_stderr,
}


def _get_windows_console_stream(f, encoding, errors):
    if encoding in ('utf-16-le', None) \
       and errors in ('strict', None) and \
       hasattr(f, 'isatty') and f.isatty():
        func = _stream_factories.get(f.fileno())
        if func is not None:
            return func()

import re
import io
import sys
import codecs


PY2 = sys.version_info[0] == 2


def _make_text_stream(stream, encoding, errors):
    if encoding is None:
        encoding = get_best_encoding(stream)
    if errors is None:
        errors = 'replace'
    return _NonClosingTextIOWrapper(stream, encoding, errors,
                                    line_buffering=True)


def is_ascii_encoding(encoding):
    """Checks if a given encoding is ascii."""
    try:
        return codecs.lookup(encoding).name == 'ascii'
    except LookupError:
        return False


def get_best_encoding(stream):
    """Returns the default stream encoding if not found."""
    rv = getattr(stream, 'encoding', None) or sys.getdefaultencoding()
    if is_ascii_encoding(rv):
        return 'utf-8'
    return rv


class _NonClosingTextIOWrapper(io.TextIOWrapper):

    def __init__(self, stream, encoding, errors, **extra):
        io.TextIOWrapper.__init__(self, _FixupStream(stream),
                                  encoding, errors, **extra)

    # The io module is already a place where Python 2 got the
    # python 3 text behavior forced on, so we need to unbreak
    # it to look like python 2 stuff.
    if PY2:
        def write(self, x):
            return io.TextIOWrapper.write(self, unicode(x))

        def writelines(self, lines):
            lines = map(unicode, lines)
            return io.TextIOWrapper.writelines(self, lines)

    def __del__(self):
        try:
            self.detach()
        except Exception:
            pass


class _FixupStream(object):
    """The new io interface needs more from streams than streams
    traditionally implement.  As such this fixup stuff is necessary in
    some circumstances.
    """

    def __init__(self, stream):
        self._stream = stream

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def read1(self, size):
        f = getattr(self._stream, 'read1', None)
        if f is not None:
            return f(size)
        return self._stream.read(size)

    def readable(self):
        x = getattr(self._stream, 'readable', None)
        if x is not None:
            return x
        try:
            self._stream.read(0)
        except Exception:
            return False
        return True

    def writable(self):
        x = getattr(self._stream, 'writable', None)
        if x is not None:
            return x
        try:
            self._stream.write('')
        except Exception:
            try:
                self._stream.write(b'')
            except Exception:
                return False
        return True

    def seekable(self):
        x = getattr(self._stream, 'seekable', None)
        if x is not None:
            return x
        try:
            self._stream.seek(self._stream.tell())
        except Exception:
            return False
        return True


if PY2:
    text_type = unicode
    bytes = str
    raw_input = raw_input
    string_types = (str, unicode)
    iteritems = lambda x: x.iteritems()

    _identifier_re = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    def isidentifier(x):
        return _identifier_re.search(x) is not None

    def get_binary_stdin():
        return sys.stdin

    def get_binary_stdout():
        return sys.stdout

    def get_binary_stderr():
        return sys.stderr

    def get_text_stdin(encoding=None, errors=None):
        return _make_text_stream(sys.stdin, encoding, errors)

    def get_text_stdout(encoding=None, errors=None):
        return _make_text_stream(sys.stdout, encoding, errors)

    def get_text_stderr(encoding=None, errors=None):
        return _make_text_stream(sys.stderr, encoding, errors)

    def filename_to_ui(value):
        if isinstance(value, bytes):
            value = value.decode(sys.getfilesystemencoding(), 'replace')
        return value
else:
    import io
    text_type = str
    raw_input = input
    string_types = (str,)
    isidentifier = lambda x: x.isidentifier()
    iteritems = lambda x: iter(x.items())

    def _is_binary_reader(stream, default=False):
        try:
            return isinstance(stream.read(0), bytes)
        except Exception:
            return default
            # This happens in some cases where the stream was already
            # closed.  In this case we assume the defalt.

    def _is_binary_writer(stream, default=False):
        try:
            stream.write(b'')
        except Exception:
            try:
                stream.write('')
                return False
            except Exception:
                pass
            return default
        return True

    def _find_binary_reader(stream):
        # We need to figure out if the given stream is already binary.
        # This can happen because the official docs recommend detatching
        # the streams to get binary streams.  Some code might do this, so
        # we need to deal with this case explicitly.
        is_binary = _is_binary_reader(stream, False)

        if is_binary:
            return stream

        buf = getattr(stream, 'buffer', None)
        # Same situation here, this time we assume that the buffer is
        # actually binary in case it's closed.
        if buf is not None and _is_binary_reader(buf, True):
            return buf

    def _find_binary_writer(stream):
        # We need to figure out if the given stream is already binary.
        # This can happen because the official docs recommend detatching
        # the streams to get binary streams.  Some code might do this, so
        # we need to deal with this case explicitly.
        if _is_binary_writer(stream, False):
            return stream

        buf = getattr(stream, 'buffer', None)

        # Same situation here, this time we assume that the buffer is
        # actually binary in case it's closed.
        if buf is not None and _is_binary_writer(buf, True):
            return buf

    def _stream_is_misconfigured(stream):
        """A stream is misconfigured if it's encoding is ASCII."""
        return is_ascii_encoding(getattr(stream, 'encoding', None))

    def _is_compatible_text_stream(stream, encoding, errors):
        stream_encoding = getattr(stream, 'encoding', None)
        stream_errors = getattr(stream, 'errors', None)

        # Perfect match.
        if stream_encoding == encoding and stream_errors == errors:
            return True

        # Otherwise it's only a compatible stream if we did not ask for
        # an encoding.
        if encoding is None:
            return stream_encoding is not None

        return False

    def _force_correct_text_reader(text_reader, encoding, errors):
        if _is_binary_reader(text_reader, False):
            binary_reader = text_reader
        else:
            # If there is no target encoding set we need to verify that the
            # reader is actually not misconfigured.
            if encoding is None and not _stream_is_misconfigured(text_reader):
                return text_reader

            if _is_compatible_text_stream(text_reader, encoding, errors):
                return text_reader

            # If the reader has no encoding we try to find the underlying
            # binary reader for it.  If that fails because the environment is
            # misconfigured, we silently go with the same reader because this
            # is too common to happen.  In that case mojibake is better than
            # exceptions.
            binary_reader = _find_binary_reader(text_reader)
            if binary_reader is None:
                return text_reader

        # At this point we default the errors to replace instead of strict
        # because nobody handles those errors anyways and at this point
        # we're so fundamentally fucked that nothing can repair it.
        if errors is None:
            errors = 'replace'
        return _make_text_stream(binary_reader, encoding, errors)

    def _force_correct_text_writer(text_writer, encoding, errors):
        if _is_binary_writer(text_writer, False):
            binary_writer = text_writer
        else:
            # If there is no target encoding set we need to verify that the
            # writer is actually not misconfigured.
            if encoding is None and not _stream_is_misconfigured(text_writer):
                return text_writer

            if _is_compatible_text_stream(text_writer, encoding, errors):
                return text_writer

            # If the writer has no encoding we try to find the underlying
            # binary writer for it.  If that fails because the environment is
            # misconfigured, we silently go with the same writer because this
            # is too common to happen.  In that case mojibake is better than
            # exceptions.
            binary_writer = _find_binary_writer(text_writer)
            if binary_writer is None:
                return text_writer

        # At this point we default the errors to replace instead of strict
        # because nobody handles those errors anyways and at this point
        # we're so fundamentally fucked that nothing can repair it.
        if errors is None:
            errors = 'replace'
        return _make_text_stream(binary_writer, encoding, errors)

    def get_binary_stdin():
        reader = _find_binary_reader(sys.stdin)
        if reader is None:
            raise RuntimeError('Was not able to determine binary '
                               'stream for sys.stdin.')
        return reader

    def get_binary_stdout():
        writer = _find_binary_writer(sys.stdout)
        if writer is None:
            raise RuntimeError('Was not able to determine binary '
                               'stream for sys.stdout.')
        return writer

    def get_binary_stderr():
        writer = _find_binary_writer(sys.stderr)
        if writer is None:
            raise RuntimeError('Was not able to determine binary '
                               'stream for sys.stderr.')
        return writer

    def get_text_stdin(encoding=None, errors=None):
        return _force_correct_text_reader(sys.stdin, encoding, errors)

    def get_text_stdout(encoding=None, errors=None):
        return _force_correct_text_writer(sys.stdout, encoding, errors)

    def get_text_stderr(encoding=None, errors=None):
        return _force_correct_text_writer(sys.stderr, encoding, errors)

    def filename_to_ui(value):
        if isinstance(value, bytes):
            value = value.decode(sys.getfilesystemencoding(), 'replace')
        else:
            value = value.encode('utf-8', 'surrogateescape') \
                .decode('utf-8', 'replace')
        return value


def get_streerror(e, default=None):
    if hasattr(e, 'strerror'):
        msg = e.strerror
    else:
        if default is not None:
            msg = default
        else:
            msg = str(e)
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8', 'replace')
    return msg


def open_stream(filename, mode='r', encoding=None, errors='strict'):
    if filename != '-':
        if encoding is not None:
            return io.open(filename, mode, encoding=encoding,
                           errors=errors), True
        return open(filename, mode), True
    if 'w' in mode:
        if 'b' in mode:
            return get_binary_stdout(), False
        return get_text_stdout(encoding=encoding, errors=errors), False
    if 'b' in mode:
        return get_binary_stdin(), False
    return get_text_stdin(encoding=encoding, errors=errors), False


binary_streams = {
    'stdin': get_binary_stdin,
    'stdout': get_binary_stdout,
    'stderr': get_binary_stderr,
}

text_streams = {
    'stdin': get_text_stdin,
    'stdout': get_text_stdout,
    'stderr': get_text_stderr,
}

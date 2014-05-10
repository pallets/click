import sys
import re
import codecs


def _wrap_stream_for_codec(f, encoding=None, errors='strict'):
    if encoding is None:
        encoding = 'utf-8'
    info = codecs.lookup(encoding)
    f = codecs.StreamReaderWriter(f, info.streamreader,
                                  info.streamwriter,
                                  errors)
    f.encoding = encoding
    return f


PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    bytes = str
    raw_input = raw_input
    string_types = (str, unicode)
    iteritems = lambda x: x.iteritems()

    _identifier_re = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    def isidentifier(x):
        return _identifier_re.search(x) is not None

    def open_stream(filename, mode='r', encoding=None, errors='strict'):
        if filename != '-':
            if encoding is not None:
                return codecs.open(filename, mode, encoding, errors), True
            return open(filename, mode), True
        if 'w' in mode:
            f = sys.stdout
            if encoding is not None:
                f = _wrap_stream_for_codec(f, encoding, errors)
        else:
            f = sys.stdin
            if 'b' not in mode:
                if encoding is None:
                    encoding = sys.stdin.encoding
                f = _wrap_stream_for_codec(f, encoding, errors)
        return f, False

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

    def _make_binary_stream(f, stream_name):
        buf = getattr(f, 'buffer', None)
        if buf is not None and isinstance(buf, io.BufferedReader):
            return buf
        raise TypeError('%s is a stream that does not give access to its '
                        'underlying binary stream.  Please do not set '
                        'sys.stdout directly to a StringIO object or '
                        'something similar.' % stream_name)

    def open_stream(filename, mode='r', encoding=None, errors='strict'):
        if filename != '-':
            if encoding is not None:
                return open(filename, mode, encoding=encoding,
                            errors=errors), True
            return open(filename, mode), True

        if 'w' in mode:
            f = sys.stdout
            if encoding is not None or 'b' in mode:
                f = _make_binary_stream(f, 'stdout')
                if encoding is not None:
                    f = _wrap_stream_for_codec(f, encoding, errors)
        else:
            f = sys.stdin
            if 'b' in mode:
                f = _make_binary_stream(f, 'stdin')
                if encoding is not None:
                    f = _wrap_stream_for_codec(f, encoding, errors)

        return f, False

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

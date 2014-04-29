import sys
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
else:
    import io
    text_type = str
    raw_input = input
    string_types = (str,)

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

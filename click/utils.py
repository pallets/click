import sys
import codecs
from collections import deque

from ._compat import text_type


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


def is_ascii_encoding(encoding):
    """Checks if a given encoding is ascii."""
    try:
        return codecs.lookup(encoding).name == 'ascii'
    except LookupError:
        return False


def get_best_encoding(stream):
    """Returns the best encoding that should be used for a stream."""
    enc = getattr(stream, 'encoding', None)
    if enc is None or is_ascii_encoding(enc):
        return 'utf-8'
    return enc


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

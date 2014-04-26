import sys

from ._compat import PY2, text_type


def safecall(func):
    """Wraps a function so that it swallows exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
    return wrapper


def echo(message=None, file=None):
    """Prints a message to the given file or stdout."""
    if file is None:
        file = sys.stdout
    if message:
        if PY2 and isinstance(message, text_type):
            message = message.encode(getattr(file, 'encoding', None)
                                     or 'utf-8', 'replace')
        file.write(message)
    file.write('\n')
    file.flush()

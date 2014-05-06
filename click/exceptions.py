from ._compat import PY2, filename_to_ui
from .utils import echo


class ClickException(Exception):
    """An exception that click can handle and show to the user.."""

    #: The exit code for this exception
    exit_code = 1

    def __init__(self, message):
        if PY2:
            Exception.__init__(self, message.encode('utf-8'))
        else:
            Exception.__init__(self, message)
        self.message = message

    def show(self, file=None):
        echo('Error: %s' % self.message)


class UsageError(ClickException):
    """An internal exception that signals a usage error.  This typically
    aborts any further handling.
    """
    exit_code = 2

    def __init__(self, message, ctx=None):
        ClickException.__init__(self, message)
        self.ctx = ctx

    def show(self, file=None):
        echo(self.ctx.get_usage() + '\n', file=file)
        echo('Error: %s' % self.message, file=file)


class FileError(ClickException):
    """Raised if a file cannot be opened."""

    def __init__(self, filename, hint=None):
        ui_filename = filename_to_ui(filename)
        if hint is None:
            hint = 'unknown error'
        message = 'Could not open file %s: %s' % (filename, hint)
        ClickException.__init__(self, message)
        self.ui_filename = ui_filename
        self.filename = filename


class Abort(RuntimeError):
    """An internal signalling exception that signals click to abort."""

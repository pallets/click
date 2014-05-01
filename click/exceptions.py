from ._compat import PY2


class UsageError(Exception):
    """An internal exception that signals a usage error.  This typically
    aborts any further handling.
    """

    def __init__(self, message, ctx=None):
        if PY2:
            Exception.__init__(self, message.encode('utf-8'))
        else:
            Exception.__init__(self, message)
        self.message = message
        self.ctx = ctx


class Abort(RuntimeError):
    """An internal signalling exception that signals click to abort."""

import sys
import uuid

from ._compat import open_stream, text_type
from .exceptions import UsageError
from .utils import safecall


class ParamType(object):
    """Helper for converting values through types.  The following is
    necessary for a valid type:

    *   it needs a name
    *   it needs to pass through None unchanged
    *   it needs to convert from a string
    *   it needs to convert its result type through unchanged
        (eg: needs to be idempotent)
    *   it needs to be able to deal with param and context being none.
        This can be the case when the object is used with prompt
        inputs.
    """

    #: the descriptive name of this type
    name = None

    def __call__(self, value, param=None, ctx=None):
        if value is not None:
            return self.convert(value, param, ctx)

    def get_metavar(self, param):
        """Returns the metavar default for this param if it provides one."""

    def convert(self, param, ctx, value):
        """Converts the value.  This is not invoked for values that are
        `None` (the missing value).
        """
        return value

    def fail(self, message, param=None, ctx=None):
        """Helper method to fail with an invalid value message."""
        if param is None:
            message = 'Invalid value: %s' % message
        else:
            names = ' / '.join(param.opts) or param.name
            message = 'Invalid value for "%s": %s' % (names, message)
        raise UsageError(message, ctx=ctx)


class FuncParamType(ParamType):

    def __init__(self, func):
        self.name = func.__name__
        self.func = func

    def convert(self, value, param, ctx):
        try:
            return self.func(value)
        except ValueError:
            try:
                value = unicode(value)
            except UnicodeError:
                value = str(value).decode('utf-8', 'replace')
            self.fail(value, param, ctx)


class StringParamType(ParamType):
    name = 'string'

    def convert(self, value, param, ctx):
        if isinstance(value, bytes):
            try:
                if sys.stdin.encoding is not None:
                    value = value.decode(sys.stdin.encoding)
            except UnicodeError:
                try:
                    value = value.decode(sys.getfilesystemencoding())
                except UnicodeError:
                    value = value.decode('utf-8', 'replace')
            return value
        return value

    def __repr__(self):
        return 'STRING'


class Choice(ParamType):
    """The choice type allows a value to checked against a fixed set of
    supported values.  All of these values have to be integers.

    See :ref:`choice-opts` for an example.
    """
    name = 'choice'

    def __init__(self, choices):
        self.choices = choices

    def get_metavar(self, param):
        return '[%s]' % '|'.join(self.choices)

    def convert(self, value, param, ctx):
        if value in self.choices:
            return value
        self.fail('invalid choice: %s. (choose from %s)' %
                  (value, ', '.join(self.choices)), param, ctx)

    def __repr__(self):
        return 'Choice(%r)' % list(self.choices)


class IntParamType(ParamType):
    name = 'integer'

    def convert(self, value, param, ctx):
        try:
            return int(value)
        except ValueError:
            self.fail('%s is not a valid integer' % value, param, ctx)

    def __repr__(self):
        return 'INT'


class IntRange(IntParamType):
    """A parameter that works similar to :data:`click.INT` but restricts
    the value to fit into a range.  The default behavior is to fail if the
    value falls outside the range, but it can also be silently clamped
    between the two edges.

    See :ref:`ranges` for an example.
    """
    name = 'integer range'

    def __init__(self, min=None, max=None, clamp=False):
        self.min = min
        self.max = max
        self.clamp = clamp

    def convert(self, value, param, ctx):
        rv = IntParamType.convert(self, value, param, ctx)
        if self.clamp:
            if self.min is not None and rv < self.min:
                return self.min
            if self.max is not None and rv > self.max:
                return self.max
        if self.min is not None and rv < self.min or \
           self.max is not None and rv > self.max:
            if self.min is None:
                self.fail('%s is bigger than the maximum valid value '
                          '%s.' % (rv, self.max), param, ctx)
            elif self.max is None:
                self.fail('%s is smaller than the minimum valid value '
                          '%s.' % (rv, self.min), param, ctx)
            else:
                self.fail('%s is not in the valid range of %s to %s.'
                          % (rv, self.min, self.max), param, ctx)
        return rv

    def __repr__(self):
        return 'IntRange(%r, %r)' % (self.min, self.max)


class BoolParamType(ParamType):
    name = 'boolean'

    def convert(self, value, param, ctx):
        if isinstance(value, bool):
            return bool(value)
        value = value.lower()
        if value in ('true', '1', 'yes', 'y'):
            return True
        elif value in ('false', '0', 'no', 'n'):
            return False
        self.fail('%s is not a valid boolean' % value, param, ctx)

    def __repr__(self):
        return 'BOOL'


class FloatParamType(ParamType):
    name = 'float'

    def convert(self, value, param, ctx):
        try:
            return float(value)
        except ValueError:
            self.fail('%s is not a valid floating point value' %
                      value, param, ctx)

    def __repr__(self):
        return 'FLOAT'


class UUIDParameterType(ParamType):
    name = 'uuid'

    def convert(self, value, param, ctx):
        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail('%s is not a valid UUID value' % value, param, ctx)

    def __repr__(self):
        return 'UUID'


class File(ParamType):
    """Declares a parameter to be a file for reading or writing.  The file
    is automatically closed once the context tears down (after the command
    finished working).

    Files can be opened for reading or writing.  The special value ``-``
    indicates stdin or stdout depending on the mode.

    By default the file is opened for reading text data but it can also be
    opened in binary mode or for writing.  The encoding parameter can be used
    to force a specific encoding.

    See :ref:`file-args` for more information.
    """
    name = 'filename'

    def __init__(self, mode='r', encoding=None, errors='strict'):
        self.mode = mode
        self.encoding = encoding
        self.errors = errors

    def convert(self, value, param, ctx):
        try:
            if hasattr(value, 'read') or hasattr(value, 'write'):
                return value
            f, was_opened = open_stream(value, self.mode, self.encoding,
                                        self.errors)
            # If a context is provided we automatically close the file
            # at the end of the context execution (or flush out).  If a
            # context does not exist it's the caller's responsibility to
            # properly close the file.  This for instance happens when the
            # type is used with prompts.
            if ctx is not None:
                if was_opened:
                    ctx.call_on_close(safecall(f.close))
                else:
                    ctx.call_on_close(safecall(f.flush))
            return f
        except (IOError, OSError) as e:
            if isinstance(value, bytes):
                value = value.decode(sys.getfilesystemencoding(), 'replace')
            if hasattr(e, 'strerror'):
                msg = e.strerror
            else:
                msg = str(e)
            if isinstance(msg, bytes):
                msg = msg.decode('utf-8', 'replace')
            self.fail('Could not open file %s: %s' % (value, msg),
                      param, ctx)


def convert_type(ty, default=None):
    """Converts a callable or python ty into the most appropriate param
    ty.
    """
    if isinstance(ty, ParamType):
        return ty
    guessed_type = False
    if ty is None and default is not None:
        ty = type(default)
        guessed_type = True
    if ty is text_type or ty is str or ty is None:
        return STRING
    if ty is int:
        return INT
    # Booleans are only okay if not guessed.  This is done because for
    # flags the default value is actually a bit of a lie in that it
    # indicates which of the flags is the one we want.  See get_default()
    # for more information.
    if ty is bool and not guessed_type:
        return BOOL
    if ty is float:
        return FLOAT
    if guessed_type:
        return STRING
    return FuncParamType(ty)


#: A unicode string parameter type which is the implicit default.  This
#: can also be selected by using ``str`` as type.
STRING = StringParamType()

#: An integer parameter.  This can also be selected by using ``int`` as
#: type.
INT = IntParamType()

#: A floating point value parameter.  This can also be selected by using
#: ``float`` as type.
FLOAT = FloatParamType()

#: A boolean parameter.  This is the default for boolean flags.  This can
#: also be selected by using ``bool`` as a type.
BOOL = BoolParamType()

#: A UUID parameter.
UUID = UUIDParameterType()

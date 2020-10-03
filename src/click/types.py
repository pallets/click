import os
import stat
from datetime import datetime

from ._compat import _get_argv_encoding
from ._compat import filename_to_ui
from ._compat import get_filesystem_encoding
from ._compat import get_strerror
from ._compat import open_stream
from .exceptions import BadParameter
from .utils import LazyFile
from .utils import safecall


class ParamType:
    """Represents the type of a parameter. Validates and converts values
    from the command line or Python into the correct type.

    To implement a custom type, subclass and implement at least the
    following:

    -   The :attr:`name` class attribute must be set.
    -   Calling an instance of the type with ``None`` must return
        ``None``. This is already implemented by default.
    -   :meth:`convert` must convert string values to the correct type.
    -   :meth:`convert` must accept values that are already the correct
        type.
    -   It must be able to convert a value if the ``ctx`` and ``param``
        arguments are ``None``. This can occur when converting prompt
        input.
    """

    is_composite = False

    #: the descriptive name of this type
    name = None

    #: if a list of this type is expected and the value is pulled from a
    #: string environment variable, this is what splits it up.  `None`
    #: means any whitespace.  For all parameters the general rule is that
    #: whitespace splits them up.  The exception are paths and files which
    #: are split by ``os.path.pathsep`` by default (":" on Unix and ";" on
    #: Windows).
    envvar_list_splitter = None

    def to_info_dict(self):
        """Gather information that could be useful for a tool generating
        user-facing documentation.

        Use :meth:`click.Context.to_info_dict` to traverse the entire
        CLI structure.

        .. versionadded:: 8.0
        """
        # The class name without the "ParamType" suffix.
        param_type = type(self).__name__.partition("ParamType")[0]
        param_type = param_type.partition("ParameterType")[0]
        return {"param_type": param_type, "name": self.name}

    def __call__(self, value, param=None, ctx=None):
        if value is not None:
            return self.convert(value, param, ctx)

    def get_metavar(self, param):
        """Returns the metavar default for this param if it provides one."""

    def get_missing_message(self, param):
        """Optionally might return extra information about a missing
        parameter.

        .. versionadded:: 2.0
        """

    def convert(self, value, param, ctx):
        """Convert the value to the correct type. This is not called if
        the value is ``None`` (the missing value).

        This must accept string values from the command line, as well as
        values that are already the correct type. It may also convert
        other compatible types.

        The ``param`` and ``ctx`` arguments may be ``None`` in certain
        situations, such as when converting prompt input.

        If the value cannot be converted, call :meth:`fail` with a
        descriptive message.

        :param value: The value to convert.
        :param param: The parameter that is using this type to convert
            its value. May be ``None``.
        :param ctx: The current context that arrived at this value. May
            be ``None``.
        """
        return value

    def split_envvar_value(self, rv):
        """Given a value from an environment variable this splits it up
        into small chunks depending on the defined envvar list splitter.

        If the splitter is set to `None`, which means that whitespace splits,
        then leading and trailing whitespace is ignored.  Otherwise, leading
        and trailing splitters usually lead to empty items being included.
        """
        return (rv or "").split(self.envvar_list_splitter)

    def fail(self, message, param=None, ctx=None):
        """Helper method to fail with an invalid value message."""
        raise BadParameter(message, ctx=ctx, param=param)

    def shell_complete(self, ctx, param, args, incomplete):
        """Return a list of
        :class:`~click.shell_completion.CompletionItem` objects for the
        incomplete value. Most types do not provide completions, but
        some do, and this allows custom types to provide custom
        completions as well.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param args: List of complete args before the incomplete value.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        return []


class CompositeParamType(ParamType):
    is_composite = True

    @property
    def arity(self):
        raise NotImplementedError()


class FuncParamType(ParamType):
    def __init__(self, func):
        self.name = func.__name__
        self.func = func

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict["func"] = self.func
        return info_dict

    def convert(self, value, param, ctx):
        try:
            return self.func(value)
        except ValueError:
            try:
                value = str(value)
            except UnicodeError:
                value = value.decode("utf-8", "replace")

            self.fail(value, param, ctx)


class UnprocessedParamType(ParamType):
    name = "text"

    def convert(self, value, param, ctx):
        return value

    def __repr__(self):
        return "UNPROCESSED"


class StringParamType(ParamType):
    name = "text"

    def convert(self, value, param, ctx):
        if isinstance(value, bytes):
            enc = _get_argv_encoding()
            try:
                value = value.decode(enc)
            except UnicodeError:
                fs_enc = get_filesystem_encoding()
                if fs_enc != enc:
                    try:
                        value = value.decode(fs_enc)
                    except UnicodeError:
                        value = value.decode("utf-8", "replace")
                else:
                    value = value.decode("utf-8", "replace")
            return value
        return value

    def __repr__(self):
        return "STRING"


class Choice(ParamType):
    """The choice type allows a value to be checked against a fixed set
    of supported values. All of these values have to be strings.

    You should only pass a list or tuple of choices. Other iterables
    (like generators) may lead to surprising results.

    The resulting value will always be one of the originally passed choices
    regardless of ``case_sensitive`` or any ``ctx.token_normalize_func``
    being specified.

    See :ref:`choice-opts` for an example.

    :param case_sensitive: Set to false to make choices case
        insensitive. Defaults to true.
    """

    name = "choice"

    def __init__(self, choices, case_sensitive=True):
        self.choices = choices
        self.case_sensitive = case_sensitive

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict["choices"] = self.choices
        info_dict["case_sensitive"] = self.case_sensitive
        return info_dict

    def get_metavar(self, param):
        choices_str = "|".join(self.choices)

        # Use curly braces to indicate a required argument.
        if param.required and param.param_type_name == "argument":
            return f"{{{choices_str}}}"

        # Use square braces to indicate an option or optional argument.
        return f"[{choices_str}]"

    def get_missing_message(self, param):
        choice_str = ",\n\t".join(self.choices)
        return f"Choose from:\n\t{choice_str}"

    def convert(self, value, param, ctx):
        # Match through normalization and case sensitivity
        # first do token_normalize_func, then lowercase
        # preserve original `value` to produce an accurate message in
        # `self.fail`
        normed_value = value
        normed_choices = {choice: choice for choice in self.choices}

        if ctx is not None and ctx.token_normalize_func is not None:
            normed_value = ctx.token_normalize_func(value)
            normed_choices = {
                ctx.token_normalize_func(normed_choice): original
                for normed_choice, original in normed_choices.items()
            }

        if not self.case_sensitive:
            normed_value = normed_value.casefold()
            normed_choices = {
                normed_choice.casefold(): original
                for normed_choice, original in normed_choices.items()
            }

        if normed_value in normed_choices:
            return normed_choices[normed_value]

        self.fail(
            f"invalid choice: {value}. (choose from {', '.join(self.choices)})",
            param,
            ctx,
        )

    def __repr__(self):
        return f"Choice({list(self.choices)})"

    def shell_complete(self, ctx, param, args, incomplete):
        """Complete choices that start with the incomplete value.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param args: List of complete args before the incomplete value.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        str_choices = map(str, self.choices)
        return [CompletionItem(c) for c in str_choices if c.startswith(incomplete)]


class DateTime(ParamType):
    """The DateTime type converts date strings into `datetime` objects.

    The format strings which are checked are configurable, but default to some
    common (non-timezone aware) ISO 8601 formats.

    When specifying *DateTime* formats, you should only pass a list or a tuple.
    Other iterables, like generators, may lead to surprising results.

    The format strings are processed using ``datetime.strptime``, and this
    consequently defines the format strings which are allowed.

    Parsing is tried using each format, in order, and the first format which
    parses successfully is used.

    :param formats: A list or tuple of date format strings, in the order in
                    which they should be tried. Defaults to
                    ``'%Y-%m-%d'``, ``'%Y-%m-%dT%H:%M:%S'``,
                    ``'%Y-%m-%d %H:%M:%S'``.
    """

    name = "datetime"

    def __init__(self, formats=None):
        self.formats = formats or ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict["formats"] = self.formats
        return info_dict

    def get_metavar(self, param):
        return f"[{'|'.join(self.formats)}]"

    def _try_to_convert_date(self, value, format):
        try:
            return datetime.strptime(value, format)
        except ValueError:
            return None

    def convert(self, value, param, ctx):
        # Exact match
        for format in self.formats:
            dtime = self._try_to_convert_date(value, format)
            if dtime:
                return dtime

        self.fail(
            f"invalid datetime format: {value}. (choose from {', '.join(self.formats)})"
        )

    def __repr__(self):
        return "DateTime"


class _NumberParamTypeBase(ParamType):
    _number_class = None

    def convert(self, value, param, ctx):
        try:
            return self._number_class(value)
        except ValueError:
            self.fail(f"{value} is not a valid {self.name}", param, ctx)


class _NumberRangeBase(_NumberParamTypeBase):
    def __init__(self, min=None, max=None, min_open=False, max_open=False, clamp=False):
        self.min = min
        self.max = max
        self.min_open = min_open
        self.max_open = max_open
        self.clamp = clamp

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict.update(
            min=self.min,
            max=self.max,
            min_open=self.min_open,
            max_open=self.max_open,
            clamp=self.clamp,
        )
        return info_dict

    def convert(self, value, param, ctx):
        import operator

        rv = super().convert(value, param, ctx)
        lt_min = self.min is not None and (
            operator.le if self.min_open else operator.lt
        )(rv, self.min)
        gt_max = self.max is not None and (
            operator.ge if self.max_open else operator.gt
        )(rv, self.max)

        if self.clamp:
            if lt_min:
                return self._clamp(self.min, 1, self.min_open)

            if gt_max:
                return self._clamp(self.max, -1, self.max_open)

        if lt_min or gt_max:
            self.fail(f"{rv} is not in the range {self._describe_range()}.", param, ctx)

        return rv

    def _clamp(self, bound, dir, open):
        """Find the valid value to clamp to bound in the given
        direction.

        :param bound: The boundary value.
        :param dir: 1 or -1 indicating the direction to move.
        :param open: If true, the range does not include the bound.
        """
        raise NotImplementedError

    def _describe_range(self):
        """Describe the range for use in help text."""
        if self.min is None:
            op = "<" if self.max_open else "<="
            return f"x{op}{self.max}"

        if self.max is None:
            op = ">" if self.min_open else ">="
            return f"x{op}{self.min}"

        lop = "<" if self.min_open else "<="
        rop = "<" if self.max_open else "<="
        return f"{self.min}{lop}x{rop}{self.max}"

    def __repr__(self):
        clamp = " clamped" if self.clamp else ""
        return f"<{type(self).__name__} {self._describe_range()}{clamp}>"


class IntParamType(_NumberParamTypeBase):
    name = "integer"
    _number_class = int

    def __repr__(self):
        return "INT"


class IntRange(_NumberRangeBase, IntParamType):
    """Restrict an :data:`click.INT` value to a range of accepted
    values. See :ref:`ranges`.

    If ``min`` or ``max`` are not passed, any value is accepted in that
    direction. If ``min_open`` or ``max_open`` are enabled, the
    corresponding boundary is not included in the range.

    If ``clamp`` is enabled, a value outside the range is clamped to the
    boundary instead of failing.

    .. versionchanged:: 8.0
        Added the ``min_open`` and ``max_open`` parameters.
    """

    name = "integer range"

    def _clamp(self, bound, dir, open):
        if not open:
            return bound

        return bound + dir


class FloatParamType(_NumberParamTypeBase):
    name = "float"
    _number_class = float

    def __repr__(self):
        return "FLOAT"


class FloatRange(_NumberRangeBase, FloatParamType):
    """Restrict a :data:`click.FLOAT` value to a range of accepted
    values. See :ref:`ranges`.

    If ``min`` or ``max`` are not passed, any value is accepted in that
    direction. If ``min_open`` or ``max_open`` are enabled, the
    corresponding boundary is not included in the range.

    If ``clamp`` is enabled, a value outside the range is clamped to the
    boundary instead of failing. This is not supported if either
    boundary is marked ``open``.

    .. versionchanged:: 8.0
        Added the ``min_open`` and ``max_open`` parameters.
    """

    name = "float range"

    def __init__(self, min=None, max=None, min_open=False, max_open=False, clamp=False):
        super().__init__(
            min=min, max=max, min_open=min_open, max_open=max_open, clamp=clamp
        )

        if (min_open or max_open) and clamp:
            raise TypeError("Clamping is not supported for open bounds.")

    def _clamp(self, bound, dir, open):
        if not open:
            return bound

        # Could use Python 3.9's math.nextafter here, but clamping an
        # open float range doesn't seem to be particularly useful. It's
        # left up to the user to write a callback to do it if needed.
        raise RuntimeError("Clamping is not supported for open bounds.")


class BoolParamType(ParamType):
    name = "boolean"

    def convert(self, value, param, ctx):
        if isinstance(value, bool):
            return bool(value)
        value = value.lower()
        if value in {"1", "true", "t", "yes", "y", "on"}:
            return True
        elif value in {"0", "false", "f", "no", "n", "off"}:
            return False
        self.fail(f"{value!r} is not a valid boolean value.", param, ctx)

    def __repr__(self):
        return "BOOL"


class UUIDParameterType(ParamType):
    name = "uuid"

    def convert(self, value, param, ctx):
        import uuid

        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail(f"{value} is not a valid UUID value", param, ctx)

    def __repr__(self):
        return "UUID"


class File(ParamType):
    """Declares a parameter to be a file for reading or writing.  The file
    is automatically closed once the context tears down (after the command
    finished working).

    Files can be opened for reading or writing.  The special value ``-``
    indicates stdin or stdout depending on the mode.

    By default, the file is opened for reading text data, but it can also be
    opened in binary mode or for writing.  The encoding parameter can be used
    to force a specific encoding.

    The `lazy` flag controls if the file should be opened immediately or upon
    first IO. The default is to be non-lazy for standard input and output
    streams as well as files opened for reading, `lazy` otherwise. When opening a
    file lazily for reading, it is still opened temporarily for validation, but
    will not be held open until first IO. lazy is mainly useful when opening
    for writing to avoid creating the file until it is needed.

    Starting with Click 2.0, files can also be opened atomically in which
    case all writes go into a separate file in the same folder and upon
    completion the file will be moved over to the original location.  This
    is useful if a file regularly read by other users is modified.

    See :ref:`file-args` for more information.
    """

    name = "filename"
    envvar_list_splitter = os.path.pathsep

    def __init__(
        self, mode="r", encoding=None, errors="strict", lazy=None, atomic=False
    ):
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.lazy = lazy
        self.atomic = atomic

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict.update(mode=self.mode, encoding=self.encoding)
        return info_dict

    def resolve_lazy_flag(self, value):
        if self.lazy is not None:
            return self.lazy
        if value == "-":
            return False
        elif "w" in self.mode:
            return True
        return False

    def convert(self, value, param, ctx):
        try:
            if hasattr(value, "read") or hasattr(value, "write"):
                return value

            lazy = self.resolve_lazy_flag(value)

            if lazy:
                f = LazyFile(
                    value, self.mode, self.encoding, self.errors, atomic=self.atomic
                )
                if ctx is not None:
                    ctx.call_on_close(f.close_intelligently)
                return f

            f, should_close = open_stream(
                value, self.mode, self.encoding, self.errors, atomic=self.atomic
            )
            # If a context is provided, we automatically close the file
            # at the end of the context execution (or flush out).  If a
            # context does not exist, it's the caller's responsibility to
            # properly close the file.  This for instance happens when the
            # type is used with prompts.
            if ctx is not None:
                if should_close:
                    ctx.call_on_close(safecall(f.close))
                else:
                    ctx.call_on_close(safecall(f.flush))
            return f
        except OSError as e:  # noqa: B014
            self.fail(
                f"Could not open file: {filename_to_ui(value)}: {get_strerror(e)}",
                param,
                ctx,
            )

    def shell_complete(self, ctx, param, args, incomplete):
        """Return a special completion marker that tells the completion
        system to use the shell to provide file path completions.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param args: List of complete args before the incomplete value.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        return [CompletionItem(incomplete, type="file")]


class Path(ParamType):
    """The path type is similar to the :class:`File` type but it performs
    different checks.  First of all, instead of returning an open file
    handle it returns just the filename.  Secondly, it can perform various
    basic checks about what the file or directory should be.

    .. versionchanged:: 6.0
       `allow_dash` was added.

    :param exists: if set to true, the file or directory needs to exist for
                   this value to be valid.  If this is not required and a
                   file does indeed not exist, then all further checks are
                   silently skipped.
    :param file_okay: controls if a file is a possible value.
    :param dir_okay: controls if a directory is a possible value.
    :param writable: if true, a writable check is performed.
    :param readable: if true, a readable check is performed.
    :param resolve_path: if this is true, then the path is fully resolved
                         before the value is passed onwards.  This means
                         that it's absolute and symlinks are resolved.  It
                         will not expand a tilde-prefix, as this is
                         supposed to be done by the shell only.
    :param allow_dash: If this is set to `True`, a single dash to indicate
                       standard streams is permitted.
    :param path_type: optionally a string type that should be used to
                      represent the path.  The default is `None` which
                      means the return value will be either bytes or
                      unicode depending on what makes most sense given the
                      input data Click deals with.
    """

    envvar_list_splitter = os.path.pathsep

    def __init__(
        self,
        exists=False,
        file_okay=True,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=False,
        allow_dash=False,
        path_type=None,
    ):
        self.exists = exists
        self.file_okay = file_okay
        self.dir_okay = dir_okay
        self.writable = writable
        self.readable = readable
        self.resolve_path = resolve_path
        self.allow_dash = allow_dash
        self.type = path_type

        if self.file_okay and not self.dir_okay:
            self.name = "file"
            self.path_type = "File"
        elif self.dir_okay and not self.file_okay:
            self.name = "directory"
            self.path_type = "Directory"
        else:
            self.name = "path"
            self.path_type = "Path"

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict.update(
            exists=self.exists,
            file_okay=self.file_okay,
            dir_okay=self.dir_okay,
            writable=self.writable,
            readable=self.readable,
            allow_dash=self.allow_dash,
        )
        return info_dict

    def coerce_path_result(self, rv):
        if self.type is not None and not isinstance(rv, self.type):
            if self.type is str:
                rv = rv.decode(get_filesystem_encoding())
            else:
                rv = rv.encode(get_filesystem_encoding())
        return rv

    def convert(self, value, param, ctx):
        rv = value

        is_dash = self.file_okay and self.allow_dash and rv in (b"-", "-")

        if not is_dash:
            if self.resolve_path:
                rv = os.path.realpath(rv)

            try:
                st = os.stat(rv)
            except OSError:
                if not self.exists:
                    return self.coerce_path_result(rv)
                self.fail(
                    f"{self.path_type} {filename_to_ui(value)!r} does not exist.",
                    param,
                    ctx,
                )

            if not self.file_okay and stat.S_ISREG(st.st_mode):
                self.fail(
                    f"{self.path_type} {filename_to_ui(value)!r} is a file.",
                    param,
                    ctx,
                )
            if not self.dir_okay and stat.S_ISDIR(st.st_mode):
                self.fail(
                    f"{self.path_type} {filename_to_ui(value)!r} is a directory.",
                    param,
                    ctx,
                )
            if self.writable and not os.access(value, os.W_OK):
                self.fail(
                    f"{self.path_type} {filename_to_ui(value)!r} is not writable.",
                    param,
                    ctx,
                )
            if self.readable and not os.access(value, os.R_OK):
                self.fail(
                    f"{self.path_type} {filename_to_ui(value)!r} is not readable.",
                    param,
                    ctx,
                )

        return self.coerce_path_result(rv)

    def shell_complete(self, ctx, param, args, incomplete):
        """Return a special completion marker that tells the completion
        system to use the shell to provide path completions for only
        directories or any paths.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param args: List of complete args before the incomplete value.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        type = "dir" if self.dir_okay and not self.file_okay else "file"
        return [CompletionItem(incomplete, type=type)]


class Tuple(CompositeParamType):
    """The default behavior of Click is to apply a type on a value directly.
    This works well in most cases, except for when `nargs` is set to a fixed
    count and different types should be used for different items.  In this
    case the :class:`Tuple` type can be used.  This type can only be used
    if `nargs` is set to a fixed number.

    For more information see :ref:`tuple-type`.

    This can be selected by using a Python tuple literal as a type.

    :param types: a list of types that should be used for the tuple items.
    """

    def __init__(self, types):
        self.types = [convert_type(ty) for ty in types]

    def to_info_dict(self):
        info_dict = super().to_info_dict()
        info_dict["types"] = [t.to_info_dict() for t in self.types]
        return info_dict

    @property
    def name(self):
        return f"<{' '.join(ty.name for ty in self.types)}>"

    @property
    def arity(self):
        return len(self.types)

    def convert(self, value, param, ctx):
        if len(value) != len(self.types):
            raise TypeError(
                "It would appear that nargs is set to conflict with the"
                " composite type arity."
            )
        return tuple(ty(x, param, ctx) for ty, x in zip(self.types, value))


def convert_type(ty, default=None):
    """Converts a callable or python type into the most appropriate
    param type.
    """
    guessed_type = False
    if ty is None and default is not None:
        if isinstance(default, tuple):
            ty = tuple(map(type, default))
        else:
            ty = type(default)
        guessed_type = True

    if isinstance(ty, tuple):
        return Tuple(ty)
    if isinstance(ty, ParamType):
        return ty
    if ty is str or ty is None:
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

    # Catch a common mistake
    if __debug__:
        try:
            if issubclass(ty, ParamType):
                raise AssertionError(
                    f"Attempted to use an uninstantiated parameter type ({ty})."
                )
        except TypeError:
            pass
    return FuncParamType(ty)


#: A dummy parameter type that just does nothing.  From a user's
#: perspective this appears to just be the same as `STRING` but
#: internally no string conversion takes place if the input was bytes.
#: This is usually useful when working with file paths as they can
#: appear in bytes and unicode.
#:
#: For path related uses the :class:`Path` type is a better choice but
#: there are situations where an unprocessed type is useful which is why
#: it is is provided.
#:
#: .. versionadded:: 4.0
UNPROCESSED = UnprocessedParamType()

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

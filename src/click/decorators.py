import inspect
from functools import update_wrapper

from .core import Argument
from .core import Command
from .core import Group
from .core import Option
from .globals import get_current_context
from .utils import echo


def pass_context(f):
    """Marks a callback as wanting to receive the current context
    object as first argument.
    """

    def new_func(*args, **kwargs):
        return f(get_current_context(), *args, **kwargs)

    return update_wrapper(new_func, f)


def pass_obj(f):
    """Similar to :func:`pass_context`, but only pass the object on the
    context onwards (:attr:`Context.obj`).  This is useful if that object
    represents the state of a nested system.
    """

    def new_func(*args, **kwargs):
        return f(get_current_context().obj, *args, **kwargs)

    return update_wrapper(new_func, f)


def make_pass_decorator(object_type, ensure=False):
    """Given an object type this creates a decorator that will work
    similar to :func:`pass_obj` but instead of passing the object of the
    current context, it will find the innermost context of type
    :func:`object_type`.

    This generates a decorator that works roughly like this::

        from functools import update_wrapper

        def decorator(f):
            @pass_context
            def new_func(ctx, *args, **kwargs):
                obj = ctx.find_object(object_type)
                return ctx.invoke(f, obj, *args, **kwargs)
            return update_wrapper(new_func, f)
        return decorator

    :param object_type: the type of the object to pass.
    :param ensure: if set to `True`, a new object will be created and
                   remembered on the context if it's not there yet.
    """

    def decorator(f):
        def new_func(*args, **kwargs):
            ctx = get_current_context()
            if ensure:
                obj = ctx.ensure_object(object_type)
            else:
                obj = ctx.find_object(object_type)
            if obj is None:
                raise RuntimeError(
                    "Managed to invoke callback without a context"
                    f" object of type {object_type.__name__!r}"
                    " existing."
                )
            return ctx.invoke(f, obj, *args, **kwargs)

        return update_wrapper(new_func, f)

    return decorator


def _make_command(f, name, attrs, cls):
    if isinstance(f, Command):
        raise TypeError("Attempted to convert a callback into a command twice.")
    try:
        params = f.__click_params__
        params.reverse()
        del f.__click_params__
    except AttributeError:
        params = []
    help = attrs.get("help")
    if help is None:
        help = inspect.getdoc(f)
        if isinstance(help, bytes):
            help = help.decode("utf-8")
    else:
        help = inspect.cleandoc(help)
    attrs["help"] = help
    return cls(
        name=name or f.__name__.lower().replace("_", "-"),
        callback=f,
        params=params,
        **attrs,
    )


def command(name=None, cls=None, **attrs):
    r"""Creates a new :class:`Command` and uses the decorated function as
    callback.  This will also automatically attach all decorated
    :func:`option`\s and :func:`argument`\s as parameters to the command.

    The name of the command defaults to the name of the function with
    underscores replaced by dashes.  If you want to change that, you can
    pass the intended name as the first argument.

    All keyword arguments are forwarded to the underlying command class.

    Once decorated the function turns into a :class:`Command` instance
    that can be invoked as a command line utility or be attached to a
    command :class:`Group`.

    :param name: the name of the command.  This defaults to the function
                 name with underscores replaced by dashes.
    :param cls: the command class to instantiate.  This defaults to
                :class:`Command`.
    """
    if cls is None:
        cls = Command

    def decorator(f):
        cmd = _make_command(f, name, attrs, cls)
        cmd.__doc__ = f.__doc__
        return cmd

    return decorator


def group(name=None, **attrs):
    """Creates a new :class:`Group` with a function as callback.  This
    works otherwise the same as :func:`command` just that the `cls`
    parameter is set to :class:`Group`.
    """
    attrs.setdefault("cls", Group)
    return command(name, **attrs)


def _param_memo(f, param):
    if isinstance(f, Command):
        f.params.append(param)
    else:
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append(param)


def argument(*param_decls, **attrs):
    """Attaches an argument to the command.  All positional arguments are
    passed as parameter declarations to :class:`Argument`; all keyword
    arguments are forwarded unchanged (except ``cls``).
    This is equivalent to creating an :class:`Argument` instance manually
    and attaching it to the :attr:`Command.params` list.

    :param cls: the argument class to instantiate.  This defaults to
                :class:`Argument`.
    """

    def decorator(f):
        ArgumentClass = attrs.pop("cls", Argument)
        _param_memo(f, ArgumentClass(param_decls, **attrs))
        return f

    return decorator


def option(*param_decls, **attrs):
    """Attaches an option to the command.  All positional arguments are
    passed as parameter declarations to :class:`Option`; all keyword
    arguments are forwarded unchanged (except ``cls``).
    This is equivalent to creating an :class:`Option` instance manually
    and attaching it to the :attr:`Command.params` list.

    :param cls: the option class to instantiate.  This defaults to
                :class:`Option`.
    """

    def decorator(f):
        # Issue 926, copy attrs, so pre-defined options can re-use the same cls=
        option_attrs = attrs.copy()

        if "help" in option_attrs:
            option_attrs["help"] = inspect.cleandoc(option_attrs["help"])
        OptionClass = option_attrs.pop("cls", Option)
        _param_memo(f, OptionClass(param_decls, **option_attrs))
        return f

    return decorator


def confirmation_option(*param_decls, **attrs):
    """Shortcut for confirmation prompts that can be ignored by passing
    ``--yes`` as parameter.

    This is equivalent to decorating a function with :func:`option` with
    the following parameters::

        def callback(ctx, param, value):
            if not value:
                ctx.abort()

        @click.command()
        @click.option('--yes', is_flag=True, callback=callback,
                      expose_value=False, prompt='Do you want to continue?')
        def dropdb():
            pass
    """

    def decorator(f):
        def callback(ctx, param, value):
            if not value:
                ctx.abort()

        attrs.setdefault("is_flag", True)
        attrs.setdefault("callback", callback)
        attrs.setdefault("expose_value", False)
        attrs.setdefault("prompt", "Do you want to continue?")
        attrs.setdefault("help", "Confirm the action without prompting.")
        return option(*(param_decls or ("--yes",)), **attrs)(f)

    return decorator


def password_option(*param_decls, **attrs):
    """Shortcut for password prompts.

    This is equivalent to decorating a function with :func:`option` with
    the following parameters::

        @click.command()
        @click.option('--password', prompt=True, confirmation_prompt=True,
                      hide_input=True)
        def changeadmin(password):
            pass
    """

    def decorator(f):
        attrs.setdefault("prompt", True)
        attrs.setdefault("confirmation_prompt", True)
        attrs.setdefault("hide_input", True)
        return option(*(param_decls or ("--password",)), **attrs)(f)

    return decorator


def version_option(
    version=None,
    *param_decls,
    package_name=None,
    prog_name=None,
    message="%(prog)s, version %(version)s",
    **kwargs,
):
    """Add a ``--version`` option which immediately prints the version
    number and exits the program.

    If ``version`` is not provided, Click will try to detect it using
    :func:`importlib.metadata.version` to get the version for the
    ``package_name``. On Python < 3.8, the ``importlib_metadata``
    backport must be installed.

    If ``package_name`` is not provided, Click will try to detect it by
    inspecting the stack frames. This will be used to detect the
    version, so it must match the name of the installed package.

    :param version: The version number to show. If not provided, Click
        will try to detect it.
    :param param_decls: One or more option names. Defaults to the single
        value ``"--version"``.
    :param package_name: The package name to detect the version from. If
        not provided, Click will try to detect it.
    :param prog_name: The name of the CLI to show in the message. If not
        provided, it will be detected from the command.
    :param message: The message to show. The values ``%(prog)s``,
        ``%(package)s``, and ``%(version)s`` are available.
    :param kwargs: Extra arguments are passed to :func:`option`.
    :raise RuntimeError: ``version`` could not be detected.

    .. versionchanged:: 8.0
        Add the ``package_name`` parameter, and the ``%(package)s``
        value for messages.

    .. versionchanged:: 8.0
        Use :mod:`importlib.metadata` instead of ``pkg_resources``.
    """
    if version is None and package_name is None:
        frame = inspect.currentframe()

        if frame is not None:
            package_name = frame.f_back.f_globals.get("__name__").partition(".")[0]

    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return

        nonlocal prog_name
        nonlocal version

        if prog_name is None:
            prog_name = ctx.find_root().info_name

        if version is None and package_name is not None:
            try:
                from importlib import metadata
            except ImportError:
                # Python < 3.8
                try:
                    import importlib_metadata as metadata
                except ImportError:
                    metadata = None

            if metadata is None:
                raise RuntimeError(
                    "Install 'importlib_metadata' to get the version on Python < 3.8."
                )

            try:
                version = metadata.version(package_name)
            except metadata.PackageNotFoundError:
                raise RuntimeError(
                    f"{package_name!r} is not installed. Try passing"
                    " 'package_name' instead."
                )

        if version is None:
            raise RuntimeError(
                f"Could not determine the version for {package_name!r} automatically."
            )

        echo(
            message % {"prog": prog_name, "package": package_name, "version": version},
            color=ctx.color,
        )
        ctx.exit()

    if not param_decls:
        param_decls = ("--version",)

    kwargs.setdefault("is_flag", True)
    kwargs.setdefault("expose_value", False)
    kwargs.setdefault("is_eager", True)
    kwargs.setdefault("help", "Show the version and exit.")
    kwargs["callback"] = callback
    return option(*param_decls, **kwargs)


def help_option(*param_decls, **attrs):
    """Adds a ``--help`` option which immediately ends the program
    printing out the help page.  This is usually unnecessary to add as
    this is added by default to all commands unless suppressed.

    Like :func:`version_option`, this is implemented as eager option that
    prints in the callback and exits.

    All arguments are forwarded to :func:`option`.
    """

    def decorator(f):
        def callback(ctx, param, value):
            if value and not ctx.resilient_parsing:
                echo(ctx.get_help(), color=ctx.color)
                ctx.exit()

        attrs.setdefault("is_flag", True)
        attrs.setdefault("expose_value", False)
        attrs.setdefault("help", "Show this message and exit.")
        attrs.setdefault("is_eager", True)
        attrs["callback"] = callback
        return option(*(param_decls or ("--help",)), **attrs)(f)

    return decorator

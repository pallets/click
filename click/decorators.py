import inspect

from functools import update_wrapper

from .helpers import echo


def pass_context(f):
    """Marks a callback that it wants to receive the current context
    object as first argument.
    """
    f.__click_pass_context__ = True
    return f


def pass_obj(f):
    """Similar to :func:`pass_context` but only pass the object on the
    context onwards (:attr:`Context.obj`).  This is useful if that object
    represents the state of a nested system.
    """
    @pass_context
    def new_func(*args, **kwargs):
        ctx = args[0]
        return ctx.invoke(f, ctx.obj, *args[1:], **kwargs)
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
        @pass_context
        def new_func(*args, **kwargs):
            ctx = args[0]
            if ensure:
                obj = ctx.ensure_object(object_type)
            else:
                obj = ctx.find_object(object_type)
            if obj is None:
                raise RuntimeError('Managed to invoke callback without a '
                                   'context object of type %r existing'
                                   % object_type.__name__)
            return ctx.invoke(f, obj, *args[1:], **kwargs)
        return update_wrapper(new_func, f)
    return decorator


def _make_command(f, name, attrs, cls):
    if isinstance(f, Command):
        raise TypeError('Attempted to convert a callback into a '
                        'command twice.')
    try:
        params = f.__click_params__
        params.reverse()
        del f.__click_params__
    except AttributeError:
        params = []
    help = inspect.getdoc(f)
    if isinstance(help, bytes):
        help = help.decode('utf-8')
    attrs.setdefault('help', help)
    return cls(name=name or f.__name__.lower(),
               callback=f, params=params, **attrs)


def command(name=None, cls=None, **attrs):
    """Creates a new :class:`Command` and uses the decorated function as
    callback.  This will also automatically attach all decorated
    :func:`option`\s and :func:`argument`\s as paramters to the command.

    The name of the command defaults to the name of the function.  If you
    want to change that, you can pass the intended name as the first
    argument.

    All keyword arguments are forwarded to the underlying command class.

    Once decorated the function turns into a :class:`Command` instance
    that can be invoked as a command line utility or be attached to a
    command :class:`Group`.

    :param name: the name of the command.  This defaults to the function
                 name.
    :param cls: the command class to instantiate.  This defaults to
                :class:`Command`.
    """
    if cls is None:
        cls = Command
    def decorator(f):
        return _make_command(f, name, attrs, cls)
    return decorator


def group(name=None, **attrs):
    """Creates a new :class:`Group` with a function as callback.  This
    works otherwise the same as :func:`command` just that the `cls`
    parameter is set to :class:`Group`.
    """
    return command(name, cls=Group, **attrs)


def _param_memo(f, param):
    if isinstance(f, Command):
        f.params.append(param)
    else:
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        f.__click_params__.append(param)


def argument(*param_decls, **attrs):
    """Attaches an option to the command.  All positional arguments are
    passed as parameter declarations to :class:`Argment`, all keyword
    arguments are forwarded unchanged.  This is equivalent to creating an
    :class:`Option` instance manually and attaching it to the
    :attr:`Command.params` list.
    """
    def decorator(f):
        _param_memo(f, Argument(param_decls, **attrs))
        return f
    return decorator


def option(*param_decls, **attrs):
    """Attaches an option to the command.  All positional arguments are
    passed as parameter declarations to :class:`Option`, all keyword
    arguments are forwarded unchanged.  This is equivalent to creating an
    :class:`Option` instance manually and attaching it to the
    :attr:`Command.params` list.
    """
    def decorator(f):
        _param_memo(f, Option(param_decls, **attrs))
        return f
    return decorator


def confirmation_option(*param_decls, **attrs):
    """Shortcut for confirmation prompts that can be ignored by bypassed
    ``--yes`` as parameter.

    This is equivalent to decorating a function with :func:`option` with
    the following parameters::

        def callback(ctx, value):
            if not value:
                ctx.abort()

        @click.command()
        @click.option('--yes', is_flag=True, callback=callback,
                      expose_value=False, prompt='Do you want to continue?')
        def dropdb():
            pass
    """
    def decorator(f):
        def callback(ctx, value):
            if not value:
                ctx.abort()
        attrs.setdefault('is_flag', True)
        attrs.setdefault('callback', callback)
        attrs.setdefault('expose_value', False)
        attrs.setdefault('prompt', 'Do you want to continue?')
        return option(*(param_decls or ('--yes',)), **attrs)(f)
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
        attrs.setdefault('prompt', True)
        attrs.setdefault('confirmation_prompt', True)
        attrs.setdefault('hide_input', True)
        return option(*(param_decls or ('--password',)), **attrs)(f)
    return decorator


def version_option(version, *param_decls, **attrs):
    """Adds a ``--version`` option which immediately ends the program
    printing out the version number.  This is implemented as an eager
    option that prints the version and exits the program in the callback.

    :param version: the version number to show
    :param prog_name: the name of the program (defaults to autodetection)
    :param message: custom message to show instead of the default
                    (``'%(prog)s, version %(version)s'``)
    :param others: everything else is forwarded to :func:`option`.
    """
    def decorator(f):
        prog_name = attrs.pop('prog_name', None)
        message = attrs.pop('message', '%(prog)s, version %(version)s')

        def callback(ctx, value):
            if not value:
                return
            prog = prog_name
            if prog is None:
                prog = ctx.find_root().info_name
            echo(message % {
                'prog': prog,
                'version': version,
            })
            ctx.exit()

        attrs.setdefault('is_flag', True)
        attrs.setdefault('expose_value', False)
        attrs.setdefault('is_eager', True)
        attrs.setdefault('help', 'Show the version and exit.')
        attrs['callback'] = callback
        return option(*(param_decls or ('--version',)), **attrs)(f)
    return decorator


def help_option(*param_decls, **attrs):
    """Adds a ``--help`` option which immediately ends the program
    printing out the help page.  This is usually unnecessary to add as
    this is added by default to all commands unless supressed.

    Like :func:`version_option` this is implemented as eager option that
    prints in the callback and exits.

    All arguments are forwarded to :func:`option`.
    """
    def decorator(f):
        def callback(ctx, value):
            if value:
                echo(ctx.get_help())
                ctx.exit()
        attrs.setdefault('is_flag', True)
        attrs.setdefault('expose_value', False)
        attrs.setdefault('help', 'Show this message and exit.')
        attrs.setdefault('is_eager', True)
        attrs['callback'] = callback
        return option(*(param_decls or ('--help',)), **attrs)(f)
    return decorator


# Circular dependencies between core and decorators
from .core import Command, Group, Argument, Option

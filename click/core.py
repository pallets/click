import os
import sys
import codecs
from contextlib import contextmanager
from itertools import chain, repeat

from .types import convert_type, IntRange, BOOL
from .utils import make_str, make_default_short_help, echo
from .exceptions import ClickException, UsageError, BadParameter, Abort
from .termui import prompt, confirm
from .formatting import HelpFormatter
from .parser import OptionParser, split_opt

from ._compat import PY2, isidentifier

_missing = object()


def _bashcomplete(cmd, prog_name, complete_var=None):
    """Internal handler for the bash completion support."""
    if complete_var is None:
        complete_var = '_%s_COMPLETE' % (prog_name.replace('-', '_')).upper()
    complete_instr = os.environ.get(complete_var)
    if not complete_instr:
        return

    from click._bashcomplete import bashcomplete
    if bashcomplete(cmd, prog_name, complete_var, complete_instr):
        sys.exit(1)


def batch(iterable, batch_size):
    return list(zip(*repeat(iter(iterable), batch_size)))


def invoke_param_callback(callback, ctx, param, value):
    code = getattr(callback, '__code__', None)
    args = getattr(code, 'co_argcount', 3)

    if args < 3:
        # This will become a warning in Click 3.0
        ##from warnings import warn
        ##warn(Warning('Invoked legacy parameter callback "%s".  The new '
        ##             'signature for such callbacks starting with '
        ##             'Click 2.0 is (ctx, param, value).'
        ##             % callback), stacklevel=3)
        return callback(ctx, value)
    return callback(ctx, param, value)


@contextmanager
def augment_usage_errors(ctx, param=None):
    """Context manager that attaches extra information to exceptions that
    fly.
    """
    try:
        yield
    except BadParameter as e:
        if e.ctx is None:
            e.ctx = ctx
        if param is not None and e.param is None:
            e.param = param
        raise
    except UsageError as e:
        if e.ctx is None:
            e.ctx = ctx
        raise


def iter_params_for_processing(invocation_order, declaration_order):
    """Given a sequence of parameters in the order as should be considered
    for processing and an iterable of parameters that exist, this returns
    a list in the correct order as they should be processed.
    """
    def sort_key(item):
        try:
            idx = invocation_order.index(item)
        except ValueError:
            idx = float('inf')
        return (not item.is_eager, idx)

    return sorted(declaration_order, key=sort_key)


class Context(object):
    """The context is a special internal object that holds state relevant
    for the script execution at every single level.  It's normally invisible
    to commands unless they opt-in to getting access to it.

    The context is useful as it can pass internal objects around and can
    control special execution features such as reading data from
    environment variables.

    A context can be used as context manager in which case it will call
    :meth:`close` on teardown.

    :param command: the command class for this context.
    :param parent: the parent context.
    :param info_name: the info name for this invokation.  Generally this
                      is the most descriptive name for the script or
                      command.  For the toplevel script is is usually
                      the name of the script, for commands below it it's
                      the name of the script.
    :param obj: an arbitrary object of user data.
    :param auto_envvar_prefix: the prefix to use for automatic environment
                               variables.  If this is `None` then reading
                               from environment variables is disabled.  This
                               does not affect manually set environment
                               variables which are always read.
    :param default_map: a dictionary (like object) with default values
                        for parameters.
    :param terminal_width: the width of the terminal.  The default is
                           inherit from parent context.  If no context
                           defines the terminal width then auto
                           detection will be applied.
    :param resilient_parsing: if this flag is enabled then click will
                              parse without any interactivity or callback
                              invocation.  This is useful for implementing
                              things such as completion support.
    """

    def __init__(self, command, parent=None, info_name=None, obj=None,
                 auto_envvar_prefix=None, default_map=None,
                 terminal_width=None, resilient_parsing=False):
        #: the parent context or `None` if none exists.
        self.parent = parent
        #: the :class:`Command` for this context.
        self.command = command
        #: the descriptive information name
        self.info_name = info_name
        #: the parsed parameters except if the value is hidden in which
        #: case it's not remembered.
        self.params = {}
        #: the leftover arguments.
        self.args = []
        #: this flag indicates if a subcommand is going to be executed.
        #: a group callback can use this information to figure out if it's
        #: being executed directly or because the execution flow passes
        #: onwards to a subcommand.  By default it's `None` but it can be
        #: the name of the subcommand to execute.
        self.invoked_subcommand = None
        if obj is None and parent is not None:
            obj = parent.obj
        #: the user object stored.
        self.obj = obj
        #: A dictionary (like object) with defaults for parameters.
        self.default_map = default_map

        if terminal_width is None and parent is not None:
            terminal_width = parent.terminal_width
        #: The width of the terminal (None is autodetection).
        self.terminal_width = terminal_width

        #: Indicates if resilient parsing is enabled.  In that case click
        #: will do its best to not cause any failures.
        self.resilient_parsing = resilient_parsing

        # If there is no envvar prefix yet, but the parent has one and
        # the command on this level has a name, we can expand the envvar
        # prefix automatically.
        if auto_envvar_prefix is None:
            if parent is not None \
               and parent.auto_envvar_prefix is not None and \
               self.info_name is not None:
                auto_envvar_prefix = '%s_%s' % (parent.auto_envvar_prefix,
                                           self.info_name.upper())
        else:
            self.auto_envvar_prefix = auto_envvar_prefix.upper()
        self.auto_envvar_prefix = auto_envvar_prefix

        self._close_callbacks = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def make_formatter(self):
        """Creates the formatter for the help and usage output."""
        return HelpFormatter(width=self.terminal_width)

    def call_on_close(self, f):
        """This decorator remembers a function as callback that should be
        executed when the context tears down.  This is most useful to bind
        resource handling to the script execution.  For instance file objects
        opened by the :class:`File` type will register their close callbacks
        here.

        :param f: the function to execute on teardown.
        """
        self._close_callbacks.append(f)
        return f

    def close(self):
        """Invokes all close callbacks."""
        for cb in self._close_callbacks:
            cb()
        self._close_callbacks = []

    @property
    def command_path(self):
        """The computed command path.  This is used for the ``usage``
        information on the help page.  It's automatically created by
        combining the info names of the chain of contexts to the root.
        """
        rv = ''
        if self.info_name is not None:
            rv = self.info_name
        if self.parent is not None:
            rv = self.parent.command_path + ' ' + rv
        return rv.lstrip()

    def find_root(self):
        """Finds the outermost context."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def find_object(self, object_type):
        """Finds the closest object of a given type."""
        node = self
        while node is not None:
            if isinstance(node.obj, object_type):
                return node.obj
            node = node.parent

    def ensure_object(self, object_type):
        """Like :meth:`find_object` but sets the innermost object to a
        new instance of `object_type` if it does not exist.
        """
        rv = self.find_object(object_type)
        if rv is None:
            self.obj = rv = object_type()
        return rv

    def lookup_default(self, name):
        """Looks up the default for a parameter name.  This by default
        looks into the :attr:`default_map` if available.
        """
        if self.default_map is not None:
            rv = self.default_map.get(name)
            if callable(rv):
                rv = rv()
            return rv

    def fail(self, message):
        """Aborts the execution of the program with a specific error
        message.

        :param message: the error message to fail with.
        """
        raise UsageError(message, self)

    def abort(self):
        """Aborts the script."""
        raise Abort()

    def exit(self, code=0):
        """Exits the application with a given exit code."""
        sys.exit(code)

    def get_usage(self):
        """Helper method to get formatted usage string for the current
        context and command.
        """
        return self.command.get_usage(self)

    def get_help(self):
        """Helper method to get formatted help page for the current
        context and command.
        """
        return self.command.get_help(self)

    def invoke(*args, **kwargs):
        """Invokes a command callback in exactly the way it expects.
        """
        self, callback = args[:2]

        # It's also possible to invoke another command which might or
        # might not have a callback.
        if isinstance(callback, Command):
            callback = callback.callback
            if callback is None:
                raise TypeError('The given command does not have a '
                                'callback that can be invoked.')

        args = args[2:]
        if getattr(callback, '__click_pass_context__', False):
            args = (self,) + args
        with augment_usage_errors(self):
            return callback(*args, **kwargs)

    def forward(*args, **kwargs):
        """Similar to :meth:`forward` but fills in default keyword
        arguments from the current context if the other command expects
        it.  This cannot invoke callbacks directly, only other commands.
        """
        self, cmd = args[:2]

        # It's also possible to invoke another command which might or
        # might not have a callback.
        if not isinstance(cmd, Command):
            raise TypeError('Callback is not a command.')

        for param in self.params:
            if param in self.params and \
               param not in kwargs:
                kwargs[param] = self.params[param]

        return self.invoke(cmd, **kwargs)


class BaseCommand(object):
    """The base command implements the minimal API contract of commands.
    Most code will never use this as it does not implement a lot of useful
    functionality but it can act as the direct subclass of alternative
    parsing methods that do not depend on the click parser.

    For instance this can be used to bridge click and other systems like
    argparse or docopt.

    Because base commands do not implement a lot of the API that other
    parts of click take for granted they are not supported for all
    operations.  For instance they cannot be used with the decorators
    usually and they have no built-in callback system.

    :param name: the name of the command to use unless a group overrides it.
    """

    def __init__(self, name):
        #: the name the command thinks it has.  Upon registering a command
        #: on a :class:`Group` the group will default the command name
        #: with this information.  You should instead use the
        #: :class:`Context`\'s :attr:`~Context.info_name` attribute.
        self.name = name

    def get_usage(self, ctx):
        raise NotImplementedError('Base commands cannot get usage')

    def get_help(self, ctx):
        raise NotImplementedError('Base commands cannot get help')

    def make_context(self, info_name, args, parent=None, **extra):
        """This function when given an info name and arguments will kick
        off the parsing and create a new :class:`Context`.  It does not
        invoke the actual command callback though.

        :param info_name: the info name for this invokation.  Generally this
                          is the most descriptive name for the script or
                          command.  For the toplevel script it's usually
                          the name of the script, for commands below it it's
                          the name of the script.
        :param args: the arguments to parse as list of strings.
        :param parent: the parent context if available.
        :param extra: extra keyword arguments forwarded to the context
                      constructor.
        """
        if 'default_map' not in extra:
            default_map = None
            if parent is not None and parent.default_map is not None:
                default_map = parent.default_map.get(info_name)
            extra['default_map'] = default_map
        ctx = Context(self, info_name=info_name, parent=parent, **extra)
        self.parse_args(ctx, args)
        return ctx

    def parse_args(self, ctx, args):
        """Given a context and a list of arguments this creates the parser
        and parses the arguments, then modifies the context as necessary.
        This is automatically invoked by :meth:`make_context`.
        """
        raise NotImplementedError('Base commands do not know how to parse '
                                  'arguments.')

    def invoke(self, ctx):
        """Given a context, this invokes the command.  The default
        implementation is raising a not implemented error.
        """
        raise NotImplementedError('Base commands are not invokable by default')

    def main(self, args=None, prog_name=None, complete_var=None, **extra):
        """This is the way to invoke a script with all the bells and
        whistles as a command line application.  This will always terminate
        the application after a call.  If this is not wanted, ``SystemExit``
        needs to be caught.

        This method is also available by directly calling the instance of
        a :class:`Command`.

        :param args: the arguments that should be used for parsing.  If not
                     provided, ``sys.argv[1:]`` is used.
        :param prog_name: the program name that should be used.  By default
                          the program name is constructed by taking the file
                          name from ``sys.argv[0]``.
        :param complete_var: the environment variable that controls the
                             bash completion support.  The default is
                             ``"_<prog_name>_COMPLETE"`` with prog name in
                             uppercase.
        :param extra: extra keyword arguments are forwarded to the context
                      constructor.  See :class:`Context` for more information.
        """
        # If we are on python 3 we will verify that the environment is
        # sane at this point of reject further execution to avoid a
        # broken script.
        if not PY2:
            try:
                import locale
                fs_enc = codecs.lookup(locale.getpreferredencoding()).name
            except Exception:
                fs_enc = 'ascii'
            if fs_enc == 'ascii':
                raise RuntimeError('Click will abort further execution '
                                   'because Python 3 was configured to use '
                                   'ASCII as encoding for the environment. '
                                   'Either switch to Python 2 or consult '
                                   'http://click.pocoo.org/python3/ '
                                   'for mitigation steps.')

        if args is None:
            args = sys.argv[1:]
        else:
            args = list(args)
        if prog_name is None:
            prog_name = make_str(os.path.basename(
                sys.argv and sys.argv[0] or __file__))

        # Hook for the bash completion.  This only activates if the bash
        # completion is actually enabled, otherwise this is quite a fast
        # noop.
        _bashcomplete(self, prog_name, complete_var)

        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    self.invoke(ctx)
                    ctx.exit()
            except (EOFError, KeyboardInterrupt):
                echo(file=sys.stderr)
                raise Abort()
            except ClickException as e:
                e.show()
                sys.exit(e.exit_code)
        except Abort:
            echo('Aborted!', file=sys.stderr)
            sys.exit(1)

    def __call__(self, *args, **kwargs):
        """Alias for :meth:`main`."""
        return self.main(*args, **kwargs)


class Command(BaseCommand):
    """Commands are the basic building block of command line interfaces in
    click.  A basic command handles command line parsing and might dispatch
    more parsing to commands nested below it.

    :param name: the name of the command to use unless a group overrides it.
    :param callback: the callback to invoke.  This is optional.
    :param params: the parameters to register with this command.  This can
                   be either :class:`Option` or :class:`Argument` objects.
    :param help: the help string to use for this command.
    :param epilog: like the help string but it's printed at the end of the
                   help page after everything else.
    :param short_help: the short help to use for this command.  This is
                       shown on the command listing of the parent command.
    :param add_help_option: by default each command registers a ``--help``
                            option.  This can be disabled by this parameter.
    """
    allow_extra_args = False

    def __init__(self, name, callback=None, params=None, help=None,
                 epilog=None, short_help=None,
                 options_metavar='[OPTIONS]', add_help_option=True):
        BaseCommand.__init__(self, name)
        #: the callback to execute when the command fires.  This might be
        #: `None` in which case nothing happens.
        self.callback = callback
        #: the list of parameters for this command in the order they
        #: should show up in the help page and execute.  Eager parameters
        #: will automatically be handled before non eager ones.
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.options_metavar = options_metavar
        if short_help is None and help:
            short_help = make_default_short_help(help)
        self.short_help = short_help
        if add_help_option:
            self.add_help_option()

    def add_help_option(self):
        """Adds a help option to the command."""
        help_option()(self)

    def get_usage(self, ctx):
        formatter = ctx.make_formatter()
        self.format_usage(ctx, formatter)
        return formatter.getvalue().rstrip('\n')

    def format_usage(self, ctx, formatter):
        """Writes the usage line into the formatter."""
        pieces = self.collect_usage_pieces(ctx)
        formatter.write_usage(ctx.command_path, ' '.join(pieces))

    def collect_usage_pieces(self, ctx):
        """Returns all the pieces that go into the usage line and returns
        it as a list of strings.
        """
        rv = [self.options_metavar]
        for param in self.params:
            rv.extend(param.get_usage_pieces(ctx))
        return rv

    def make_parser(self, ctx):
        """Creates the underlying option parser for this command."""
        parser = OptionParser(ctx)
        for param in self.params:
            param.add_to_parser(parser, ctx)
        return parser

    def get_help(self, ctx):
        """Formats the help into a string and returns it.  This creates a
        formatter and will call into the following formatting methods:
        """
        formatter = ctx.make_formatter()
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip('\n')

    def format_help(self, ctx, formatter):
        """Writes the help into the formatter if it exists.

        This calls into the following methods:

        -   :meth:`format_usage`
        -   :meth:`format_help_text`
        -   :meth:`format_options`
        -   :meth:`format_epilog`
        """
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def format_help_text(self, ctx, formatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(self.help)

    def format_options(self, ctx, formatter):
        """Writes all the options into the formatter if they exist."""
        opts = []
        for param in self.params:
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append(rv)

        if opts:
            with formatter.section('Options'):
                formatter.write_dl(opts)

    def format_epilog(self, ctx, formatter):
        """Writes the epilog into the formatter if it exists."""
        if self.epilog:
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(self.epilog)

    def parse_args(self, ctx, args):
        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        for param in iter_params_for_processing(param_order, self.params):
            value, args = param.handle_parse_result(ctx, opts, args)

        if args and not self.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail('Got unexpected extra argument%s (%s)'
                     % (len(args) != 1 and 's' or '',
                        ' '.join(map(make_str, args))))

        ctx.args = args

    def invoke(self, ctx):
        """Given a context, this invokes the attached callback (if it exists)
        in the right way.
        """
        if self.callback is not None:
            ctx.invoke(self.callback, **ctx.params)


class MultiCommand(Command):
    """A multi command is the basic implementation of a command that
    dispatches to subcommands.  The most common version is the
    :class:`Command`.

    :param invoke_without_command: this controls how the multi command itself
                                   is invoked.  By default it's only invoked
                                   if a subcommand is provided.
    :param no_args_is_help: this controls what happens if no arguments are
                            provided.  This option is enabled by default if
                            `invoke_without_command` is disabled or disabled
                            if it's enabled.  If enabled this will add
                            ``--help`` as argument if no arguments are
                            passed.
    :param subcommand_metavar: the string that is used in the documentation
                               to indicate the subcommand place.
    """
    allow_extra_args = True

    def __init__(self, name=None, invoke_without_command=False,
                 no_args_is_help=None, subcommand_metavar='COMMAND [ARGS]...',
                 **attrs):
        Command.__init__(self, name, **attrs)
        if no_args_is_help is None:
            no_args_is_help = not invoke_without_command
        self.no_args_is_help = no_args_is_help
        self.invoke_without_command = invoke_without_command
        self.subcommand_metavar = subcommand_metavar

    def make_parser(self, ctx):
        parser = Command.make_parser(self, ctx)
        parser.allow_interspersed_args = False
        return parser

    def collect_usage_pieces(self, ctx):
        rv = Command.collect_usage_pieces(self, ctx)
        rv.append(self.subcommand_metavar)
        return rv

    def format_options(self, ctx, formatter):
        Command.format_options(self, ctx, formatter)
        self.format_commands(ctx, formatter)

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue

            help = cmd.short_help or ''
            rows.append((subcommand, help))

        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)

    def parse_args(self, ctx, args):
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            echo(ctx.get_help())
            ctx.exit()
        return Command.parse_args(self, ctx, args)

    def invoke(self, ctx):
        if not ctx.args:
            if self.invoke_without_command:
                return Command.invoke(self, ctx)
            ctx.fail('Missing command.')

        cmd_name = make_str(ctx.args[0])
        cmd = self.get_command(ctx, cmd_name)

        # If we don't find the command we want to show an error message
        # to the user that it was not provided.  However there is
        # something else we should do: if the first argument looks like
        # an option we want to kick off parsing again for arguments to
        # resolve things like --help which now should go to the main
        # place.
        if cmd is None:
            if split_opt(cmd_name)[0]:
                self.parse_args(ctx, ctx.args)
            ctx.fail('No such command "%s".' % cmd_name)

        return self.invoke_subcommand(ctx, cmd, cmd_name, ctx.args[1:])

    def invoke_subcommand(self, ctx, cmd, cmd_name, args):
        # Whenever we dispatch to a subcommand we also invoke the regular
        # callback.  This is done so that parameters can be handled.
        ctx.invoked_subcommand = cmd_name
        Command.invoke(self, ctx)

        with cmd.make_context(cmd_name, args, parent=ctx) as cmd_ctx:
            return cmd.invoke(cmd_ctx)

    def get_command(self, ctx, cmd_name):
        """Given a context and a command name, this returns a
        :class:`Command` object if it exists or returns `None`.
        """
        raise NotImplementedError()

    def list_commands(self, ctx):
        """Returns a list of subcommand names in the order they should
        appear.
        """
        return []


class Group(MultiCommand):
    """A group allows a command to have subcommands attached.  This is the
    most common way to implement nesting in click.

    :param commands: a dictionary of commands.
    """

    def __init__(self, name=None, commands=None, **attrs):
        MultiCommand.__init__(self, name, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or {}

    def add_command(self, cmd, name=None):
        """Registers another :class:`Command` with this group.  If the name
        is not provided, the name of the command is used.
        """
        name = name or cmd.name
        if name is None:
            raise TypeError('Command has no name.')
        self.commands[name] = cmd

    def command(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a command to
        the group.  This takes the same arguments as :func:`command` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator

    def group(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a group to
        the group.  This takes the same arguments as :func:`group` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def list_commands(self, ctx):
        return sorted(self.commands)


class CommandCollection(MultiCommand):
    """A command collection is a multi command that merges multiple multi
    commands together into one.  This is a straightforward implementation
    that accepts a list of different multi commands as sources and
    provides all the commands for each of them.
    """

    def __init__(self, name=None, sources=None, **attrs):
        MultiCommand.__init__(self, name, **attrs)
        #: The list of registered multi commands.
        self.sources = sources or []

    def add_source(self, multi_cmd):
        """Adds a new multi command to the chain dispatcher."""
        self.sources.append(multi_cmd)

    def get_command(self, ctx, cmd_name):
        for source in self.sources:
            rv = source.get_command(ctx, cmd_name)
            if rv is not None:
                return rv

    def list_commands(self, ctx):
        rv = set()
        for source in self.sources:
            rv.update(source.list_commands(ctx))
        return sorted(rv)


class Parameter(object):
    """A parameter to a command comes in two versions: they are either
    :class:`Option`\s or :class:`Argument`\s.  Other subclasses are currently
    not supported by design as some of the internals for parsing are
    intentionally not finalized.

    Some settings are supported by both options and arguments.

    .. versionchanged:: 2.0
       Changed signature for parameter callback to also be passed the
       parameter.  In click 2.0 the old callback format will still work
       but it will raise a warning to give you change to migrate the
       code easier.

    :param param_decls: the parameter declarations for this option or
                        argument.  This is a list of flags or argument
                        names.
    :param type: the type that should be used.  Either a :class:`ParamType`
                 or a python type.  The later is converted into the former
                 automatically if supported.
    :param required: controls if this is optional or not.
    :param default: the default value if omitted.  This can also be a callable
                    in which case it's invoked when the default is needed
                    without any arguments.
    :param callback: a callback that should be executed after the parameter
                     was matched.  This is called as ``fn(ctx, param,
                     value)`` and needs to return the value.  Before click
                     2.0 the signature was ``(ctx, value)``.
    :param nargs: the number of arguments to match.  If not ``1`` the return
                  value is a tuple instead of single value.
    :param metavar: how the value is represented in the help page.
    :param expose_value: if this is `True` then the value is passed onwards
                         to the command callback and stored on the context,
                         otherwise it's skipped.
    :param is_eager: eager values are processed before non eager ones.  This
                     should not be set for arguments or it will inverse the
                     order of processing.
    :param envvar: a string or list of strings that are environment variables
                   that should be checked.
    """
    param_type_name = 'parameter'

    def __init__(self, param_decls=None, type=None, required=False,
                 default=None, callback=None, nargs=1, metavar=None,
                 expose_value=True, is_eager=False, envvar=None):
        self.name, self.opts, self.secondary_opts = \
            self._parse_decls(param_decls or ())
        self.type = convert_type(type, default)
        self.required = required
        self.callback = callback
        self.nargs = nargs
        self.multiple = False
        self.expose_value = expose_value
        self.default = default
        self.is_eager = is_eager
        self.metavar = metavar
        self.envvar = envvar

    def make_metavar(self):
        if self.metavar is not None:
            return self.metavar
        metavar = self.type.get_metavar(self)
        if metavar is None:
            metavar = self.type.name.upper()
        if self.nargs != 1:
            metavar += '...'
        return metavar

    def get_default(self, ctx):
        """Given a context variable this calculates the default value."""
        # Otherwise go with the regular default.
        if callable(self.default):
            rv = self.default()
        else:
            rv = self.default
        return self.type(rv, self, ctx)

    def add_to_parser(self, parser, ctx):
        pass

    def consume_value(self, ctx, opts):
        value = opts.get(self.name)
        if value is None:
            value = ctx.lookup_default(self.name)
        if value is None:
            value = self.value_from_envvar(ctx)
        return value

    def process_value(self, ctx, value):
        """Given a value and context this runs the logic to convert the
        value as necessary.
        """
        def _convert(value, level):
            if level == 0:
                return self.type(value, self, ctx)
            return tuple(_convert(x, level - 1) for x in value or ())
        return _convert(value, (self.nargs != 1) + bool(self.multiple))

    def value_is_missing(self, value):
        if value is None:
            return True
        if (self.nargs != 1 or self.multiple) and value == ():
            return True
        return False

    def full_process_value(self, ctx, value):
        value = self.process_value(ctx, value)

        if value is None:
            value = self.get_default(ctx)

        if self.required and self.value_is_missing(value):
            ctx.fail(self.get_missing_message(ctx))

        return value

    def get_missing_message(self, ctx):
        return 'Missing %s %s.' % (
            self.param_type_name,
            ' / '.join('"%s"' % x for x in chain(
                self.opts, self.secondary_opts)),
        )

    def resolve_envvar_value(self, ctx):
        if self.envvar is None:
            return
        if isinstance(self.envvar, (tuple, list)):
            for envvar in self.envvar:
                rv = os.environ.get(envvar)
                if rv is not None:
                    return rv
        else:
            return os.environ.get(self.envvar)

    def value_from_envvar(self, ctx):
        rv = self.resolve_envvar_value(ctx)
        if rv is not None and self.nargs != 1:
            rv = self.type.split_envvar_value(rv)
        return rv

    def handle_parse_result(self, ctx, opts, args):
        with augment_usage_errors(ctx, param=self):
            value = self.consume_value(ctx, opts)
            try:
                value = self.full_process_value(ctx, value)
            except Exception:
                if not ctx.resilient_parsing:
                    raise
                value = None
            if self.callback is not None:
                try:
                    value = invoke_param_callback(
                        self.callback, ctx, self, value)
                except Exception:
                    if not ctx.resilient_parsing:
                        raise

        if self.expose_value:
            ctx.params[self.name] = value
        return value, args

    def get_help_record(self, ctx):
        pass

    def get_usage_pieces(self, ctx):
        return []


class Option(Parameter):
    """Options are usually optionaly values on the command line and
    have some extra features that arguments don't have.

    All other parameters are passed onwards to the parameter constructor.

    :param show_default: controls if the default value should be shown on the
                         help page.  Normally defaults are not shown.
    :param prompt: if set to `True` or a non empty string then the user will
                   be prompted for input if not set.  If set to `True` the
                   prompt will be the option name capitalized.
    :param confirmation_prompt: if set then the value will need to be confirmed
                                if it was prompted for.
    :param hide_input: if this is `True` then the input on the prompt will be
                       hidden from the user.  This is useful for password
                       input.
    :param is_flag: forces this option to act as a flag.  The default is
                    auto detection.
    :param flag_value: which value should be used for this flag if it's
                       enabled.  This is set to a boolean automatically if
                       the option string contains a slash to mark two options.
    :param multiple: if this is set to `True` then the argument is accepted
                     multiple times and recorded.  This is similar to ``nargs``
                     in how it works but supports arbitrary number of
                     arguments.
    :param count: this flag makes an option increment an integer.
    :param allow_from_autoenv: if this is enabled then the value of this
                               parameter will be pulled from an environment
                               variable in case a prefix is defined on the
                               context.
    :param help: the help string.
    """
    param_type_name = 'option'

    def __init__(self, param_decls=None, show_default=False,
                 prompt=False, confirmation_prompt=False,
                 hide_input=False, is_flag=None, flag_value=None,
                 multiple=False, count=False, allow_from_autoenv=True,
                 type=None, help=None, **attrs):
        default_is_missing = attrs.get('default', _missing) is _missing
        Parameter.__init__(self, param_decls, type=type, **attrs)

        if prompt is True:
            prompt_text = self.name.replace('_', ' ').capitalize()
        elif prompt is False:
            prompt_text = None
        else:
            prompt_text = prompt
        self.prompt = prompt_text
        self.confirmation_prompt = confirmation_prompt
        self.hide_input = hide_input

        # Flags
        if is_flag is None:
            if flag_value is not None:
                is_flag = True
            else:
                is_flag = bool(self.secondary_opts)
        if is_flag and default_is_missing:
            self.default = False
        if flag_value is None:
            flag_value = not self.default
        self.is_flag = is_flag
        self.flag_value = flag_value
        if self.is_flag and isinstance(self.flag_value, bool) \
           and type is None:
            self.type = BOOL
            self.is_bool_flag = True
        else:
            self.is_bool_flag = False

        # Counting
        self.count = count
        if count:
            if type is None:
                self.type = IntRange(min=0)
            if default_is_missing:
                self.default = 0

        self.multiple = multiple
        self.allow_from_autoenv = allow_from_autoenv
        self.help = help
        self.show_default = show_default

        # Sanity check for stuff we don't support
        if __debug__:
            if self.prompt and self.is_flag and not self.is_bool_flag:
                raise TypeError('Cannot prompt for flags that are not bools.')
            if not self.is_bool_flag and self.secondary_opts:
                raise TypeError('Got secondary option for non boolean flag.')
            if self.is_bool_flag and self.hide_input \
               and self.prompt is not None:
                raise TypeError('Hidden input does not work with boolean '
                                'flag prompts.')
            if self.count:
                if self.multiple:
                    raise TypeError('Options cannot be multiple and count '
                                    'at the same time.')
                elif self.is_flag:
                    raise TypeError('Options cannot be count and flags at '
                                    'the same time.')

    def _parse_decls(self, decls):
        opts = []
        secondary_opts = []
        name = None
        possible_names = []

        for decl in decls:
            if isidentifier(decl):
                if name is not None:
                    raise TypeError('Name defined twice')
                name = decl
            else:
                if '/' in decl:
                    first, second = decl.split('/', 1)
                    possible_names.append(split_opt(first))
                    opts.append(first)
                    secondary_opts.append(second)
                else:
                    possible_names.append(split_opt(decl))
                    opts.append(decl)

        if name is None and possible_names:
            possible_names.sort(key=lambda x: len(x[0]))
            name = possible_names[-1][1].replace('-', '_').lower()
            if not isidentifier(name):
                name = None

        if name is None:
            raise TypeError('Could not determine name for option')

        return name, opts, secondary_opts

    def add_to_parser(self, parser, ctx):
        kwargs = {
            'dest': self.name,
            'nargs': self.nargs,
            'obj': self,
        }

        if self.multiple:
            action = 'append'
        elif self.count:
            action = 'count'
        else:
            action = 'store'

        if self.is_flag:
            kwargs.pop('nargs', None)
            if self.is_bool_flag and self.secondary_opts:
                parser.add_option(self.opts, action=action + '_const',
                                  const=True, **kwargs)
                parser.add_option(self.secondary_opts, action=action +
                                  '_const', const=False, **kwargs)
            else:
                parser.add_option(self.opts, action=action + '_const',
                                  const=self.flag_value,
                                  **kwargs)
        else:
            kwargs['action'] = action
            parser.add_option(self.opts, **kwargs)

    def get_help_record(self, ctx):
        def _write_opts(opts):
            rv = []
            for opt in opts:
                prefix = split_opt(opt)[0]
                rv.append((len(prefix), opt))

            rv.sort(key=lambda x: x[0])

            rv = ', '.join(x[1] for x in rv)
            if not self.is_flag:
                rv += ' ' + self.make_metavar()
            return rv

        rv = [_write_opts(self.opts)]
        if self.secondary_opts:
            rv.append(_write_opts(self.secondary_opts))

        help = self.help or ''
        extra = []
        if self.default is not None and self.show_default:
            extra.append('default: %s' % self.default)
        if self.required:
            extra.append('required')
        if extra:
            help = '%s[%s]' % (help and help + '  ' or '', '; '.join(extra))

        return (' / '.join(rv), help)

    def get_default(self, ctx):
        # If we're a non boolean flag out default is more complex because
        # we need to look at all flags in the same group to figure out
        # if we're the the default one in which case we return the flag
        # value as default.
        if self.is_flag and not self.is_bool_flag:
            for param in ctx.command.params:
                if param.name == self.name and param.default:
                    return param.flag_value
            return None
        return Parameter.get_default(self, ctx)

    def prompt_for_value(self, ctx):
        """This is an alternative flow that can be activated in the full
        value processing if a value does not exist.  It will prompt the
        user until a valid value exists and then returns the processed
        value as result.
        """
        # Calculate the default before prompting anything to be stable.
        default = self.get_default(ctx)

        # If this is a prompt for a flag we need to handle this
        # differently.
        if self.is_bool_flag:
            return confirm(self.prompt, default)

        return prompt(self.prompt, default=default,
                      hide_input=self.hide_input,
                      confirmation_prompt=self.confirmation_prompt,
                      value_proc=lambda x: self.process_value(ctx, x))

    def resolve_envvar_value(self, ctx):
        rv = Parameter.resolve_envvar_value(self, ctx)
        if rv is not None:
            return rv
        if self.allow_from_autoenv and \
           ctx.auto_envvar_prefix is not None:
            envvar = '%s_%s' % (ctx.auto_envvar_prefix, self.name.upper())
            return os.environ.get(envvar)

    def value_from_envvar(self, ctx):
        rv = self.resolve_envvar_value(ctx)
        if rv is None:
            return None
        value_depth = (self.nargs != 1) + bool(self.multiple)
        if value_depth > 0 and rv is not None:
            rv = self.type.split_envvar_value(rv)
            if self.multiple and self.nargs != 1:
                rv = batch(rv, self.nargs)
        return rv

    def full_process_value(self, ctx, value):
        if value is None and self.prompt is not None \
           and not ctx.resilient_parsing:
            return self.prompt_for_value(ctx)
        return Parameter.full_process_value(self, ctx, value)


class Argument(Parameter):
    """Arguments are positional parameters to a command.  They generally
    provide fewer features than options but can have infinite ``nargs``
    and are required by default.

    All parameters are passed onwards to the parameter constructor.
    """
    param_type_name = 'argument'

    def __init__(self, param_decls, required=None, **attrs):
        if required is None:
            if attrs.get('default') is not None:
                required = False
            else:
                required = attrs.get('nargs', 1) > 0
        Parameter.__init__(self, param_decls, required=required, **attrs)

    def make_metavar(self):
        if self.metavar is not None:
            return self.metavar
        var = self.name.upper()
        if not self.required:
            var = '[%s]' % var
        if self.nargs != 1:
            var += '...'
        return var

    def _parse_decls(self, decls):
        if not decls:
            raise TypeError('Could not determine name for argument')
        if len(decls) == 1:
            name = arg = decls[0]
            name = name.replace('-', '_').lower()
        elif len(decls) == 2:
            name, arg = decls
        else:
            raise TypeError('Arguments take exactly one or two '
                            'parameter declarations, got %d' % len(decls))
        return name, [arg], []

    def get_usage_pieces(self, ctx):
        return [self.make_metavar()]

    def add_to_parser(self, parser, ctx):
        parser.add_argument(dest=self.name, nargs=self.nargs,
                            obj=self)


# Circular dependency between decorators and core
from .decorators import command, group, help_option

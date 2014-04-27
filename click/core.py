import os
import sys
from itertools import chain

from .types import convert_type, BOOL
from .utils import echo
from .exceptions import UsageError, Abort
from .helpers import prompt, confirm

from . import _optparse


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
    """

    def __init__(self, command, parent=None, info_name=None, obj=None,
                 auto_envvar_prefix=None):
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

        self._parser = command._make_parser(self)
        self._close_callbacks = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

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
        while node.parent is not None:
            if isinstance(node.obj, object_type):
                return node.obj
            node = node.parent

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

    def format_usage(self):
        """Helper method to get formatted usage string for the current
        context and command.
        """
        return self._parser.get_usage()

    def format_help(self):
        """Helper method to get formatted help page for the current
        context and command.
        """
        return self._parser.format_help().rstrip()

    def invoke(*args, **kwargs):
        """Invokes a command callback in exactly the way it expects.
        """
        self, callback = args[:2]
        args = args[2:]
        if getattr(callback, '__click_pass_context__', False):
            args = (self,) + args
        return callback(*args, **kwargs)


class Command(object):
    """Commands are the basic building block of command line interfaces in
    click.  A basic command handles command line parsing and might dispatch
    more parsing to commands nested blow it.

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
        #: the name the command things it has.  Upon registering a command
        #: on a :class:`Group` the group will default the command name
        #: with this information.  You should instead use the
        #: :class:`Context`\'s :attr:`~Context.info_name` attribute.
        self.name = name
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
            short_help = help.split('.')[0].strip()
            if len(short_help) > 45:
                short_help = None
            elif short_help:
                short_help = short_help[0].lower() + short_help[1:] + '.'
        self.short_help = short_help
        if add_help_option:
            help_option()(self)

    def iter_params_for_processing(self):
        """This returns an iterator over all attached parameters in the
        order of processing.  This iterator returns all eager parameters
        first, followed by all non-eager parameters.
        """
        for param in self.params:
            if param.is_eager:
                yield param
        for param in self.params:
            if not param.is_eager:
                yield param

    def _make_parser(self, ctx):
        parser = _optparse._SimplifiedOptionParser(
            ctx, description=self.help, epilog=self.epilog)
        for param in self.params:
            param._add_to_parser(parser, ctx)
        return parser

    def _format_extra_help(self, ctx):
        pass

    def make_context(self, info_name, args, parent=None, **extra):
        """This function when given an info name and arguments will kick
        off the parsing and create a new :class:`Context`.  It does not
        invoke the actual command callback though.

        :param info_name: the info name for this invokation.  Generally this
                          is the most descriptive name for the script or
                          command.  For the toplevel script is is usually
                          the name of the script, for commands below it it's
                          the name of the script.
        :param args: the arguments to parse as list of strings.
        :param parent: the parent context if available.
        :param extra: extra keyword arguments forwarded to the context
                      constructor.
        """
        ctx = Context(self, info_name=info_name, parent=parent, **extra)
        opts, args = ctx._parser.parse_args(args=args)
        opts = opts.__dict__

        for param in ctx.command.iter_params_for_processing():
            value, args = param.handle_parse_result(ctx, opts, args)

        if args and not self.allow_extra_args:
            ctx.fail('Got unexpected extra argument%s (%s)'
                     % (len(args) != 1 and 's' or '', ' '.join(args)))

        ctx.args = args

        return ctx

    def invoke(self, ctx):
        """Given a context, this invokes the attached callback (if it exists)
        in the right way.
        """
        if self.callback is not None:
            ctx.invoke(self.callback, **ctx.params)

    def main(self, args=None, prog_name=None, **extra):
        """This is the way to invoke a script with all the bells and
        whistles as command line application.  This will always terminate
        the application after calling.  If this is not wanted, ``SystemExit``
        needs to be caught.

        This method is also available by directly calling the instance of
        a :class:`Command`.

        :param args: the arguments that should be used for parsing.  If not
                     provided, ``sys.argv[1:]`` is used.
        :param prog_name: the program name that should be used.  By default
                          the progam name is constructed by taking the file
                          name from ``sys.argv[0]``.
        :param extra: extra keyword arguments are forwarded to the context
                      constructor.
        """
        if args is None:
            args = sys.argv[1:]
        else:
            args = list(args)
        if prog_name is None:
            prog_name = os.path.basename(sys.argv and sys.argv[0] or __file__)
        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    self.invoke(ctx)
                    ctx.exit()
            except (EOFError, KeyboardInterrupt):
                echo(file=sys.stderr)
                raise Abort()
            except UsageError as e:
                if e.ctx is not None:
                    echo(e.ctx.format_usage(), file=sys.stderr)
                echo('Error: %s' % e.message, file=sys.stderr)
                sys.exit(2)
        except Abort:
            echo('Aborted!', file=sys.stderr)
            sys.exit(1)

    def __call__(self, *args, **kwargs):
        """Alias for :meth:`main`."""
        return self.main(*args, **kwargs)


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

    def _make_parser(self, ctx):
        parser = Command._make_parser(self, ctx)
        parser.usage += ' ' + self.subcommand_metavar
        parser.disable_interspersed_args()
        return parser

    def _format_extra_help(self, ctx):
        commands = self.list_commands()
        if not commands:
            return

        longest = len(sorted(commands, key=len)[-1])

        subcommand_info = []
        for subcommand in self.list_commands():
            cmd = self.get_command(ctx, subcommand)
            help = cmd.short_help or ''
            subcommand_info.append('  %-*s  %s' % (longest, subcommand, help))

        return 'Commands:\n%s' % '\n'.join(subcommand_info)

    def make_context(self, info_name, args, parent=None, **extra):
        # Multi-commands invoked without any arguments is a shortcut to
        # invoking it with --help unless supresssed.
        if not args and self.no_args_is_help:
            args = ['--help']
        return Command.make_context(self, info_name, args, parent, **extra)

    def invoke(self, ctx):
        if not ctx.args:
            if self.invoke_without_command:
                return Command.invoke(self, ctx)
            ctx.fail('Missing command')
        cmd_name = ctx.args[0]

        cmd = self.get_command(ctx, cmd_name)
        if cmd is None:
            ctx.fail('No such command "%s"' % cmd_name)

        # Whenever we dispatch to a subcommand we also invoke the regular
        # callback.  This is done so that parameters can be handled.
        ctx.invoked_subcommand = cmd_name
        Command.invoke(self, ctx)

        with cmd.make_context(cmd_name, ctx.args[1:], parent=ctx) as cmd_ctx:
            return cmd.invoke(cmd_ctx)

    def get_command(self, ctx, cmd_name):
        """Given a context and a command name, this returns a
        :class:`Command` object if it exists or returns `None`.
        """
        raise NotImplementedError()

    def list_commands(self):
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

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def list_commands(self):
        return sorted(self.commands)


class Parameter(object):
    """A parameter to a command comes in two versions: they are either
    :class:`Option`\s or :class:`Argument`\s.  Other subclasses are currently
    not supported by design as some of the internals for parsing are
    intentionally not finalized.

    Some settings are supported by both options and arguments.

    :param param_decls: the parameter declarations for this option or
                        argument.  This is a list of flags or argument
                        names.
    :param type: the type that should be used.  Either a :class:`ParamType`
                 or a python type.  The latter is converted into the former
                 automatically if supported.
    :param required: controls if this is optional or not.
    :param default: the default value if omitted.  This can also be a callable
                    in which case it's invoked when the default is needed
                    without any arguments.
    :param help: the help string.
    :param callback: a callback that should be executed after the parameter
                     was matched.  This is called as ``fn(ctx, value)`` and
                     needs to return the value.
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
                 default=None, help=None, callback=None, nargs=1,
                 metavar=None, expose_value=True, is_eager=False,
                 envvar=None):
        self.name, self.opts, self.secondary_opts = \
            self._parse_decls(param_decls or ())
        self.type = convert_type(type, default)
        self.required = required
        self.help = help
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
        if metavar is not None:
            return metavar
        metavar = self.name.upper()
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

    def _add_to_parser(self, parser, ctx):
        raise NotImplementedError()

    def process_value(self, ctx, value):
        """Given a value and context this runs the logic to convert the
        value as necessary.
        """
        def _convert(value, level):
            if level == 0:
                return self.type(value, self, ctx)
            return tuple(_convert(x, level - 1) for x in value or ())
        return _convert(value, (self.nargs != 1) + bool(self.multiple))

    def full_process_value(self, ctx, value):
        value = self.process_value(ctx, value)

        if value is None:
            value = self.get_default(ctx)

        if value is None and self.required:
            ctx.fail(self.get_missing_message(ctx))

        return value

    def get_missing_message(self, ctx):
        return 'Missing %s "%s".' % (
            self.param_type_name,
            ' / '.join(chain(self.opts, self.secondary_opts)),
        )

    def value_from_envvar(self, ctx):
        if self.envvar is None:
            return
        if isinstance(self.envvar, (tuple, list)):
            for envvar in self.envvar:
                rv = os.environ.get(envvar)
                if rv is not None:
                    return rv
        else:
            return os.environ.get(self.envvar)

    def consume_value(self, ctx, opts, args):
        return None, args

    def handle_parse_result(self, ctx, opts, args):
        value, args = self.consume_value(ctx, opts, args)
        value = self.full_process_value(ctx, value)
        if self.callback is not None:
            value = self.callback(ctx, value)
        if self.expose_value:
            ctx.params[self.name] = value
        return value, args


class Option(Parameter):
    """Options are usually optionaly values on the command line and
    have some extra features that arguments don't have.

    All other parameters are passed onwards to the parameter constructor.

    :param show_default: controls if the default value should be shown on the
                         help page.  The default is auto detection.
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
    :param multiple: if this is set to True then the argument is accepted
                     multiple times and recorded.  This is similar to nargs
                     in how it works but supports arbitrary number of
                     arguments.
    :param allow_from_autoenv: if this is enabled then the value of this
                               parameter will be pulled from an environment
                               variable in case a prefix is defined on the
                               context.
    """
    param_type_name = 'option'

    def __init__(self, param_decls=None, show_default=None,
                 prompt=False, confirmation_prompt=False,
                 hide_input=False, is_flag=None, flag_value=None,
                 multiple=False, allow_from_autoenv=True, type=None,
                 **attrs):
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

        if is_flag is None:
            if flag_value is not None:
                is_flag = True
            else:
                is_flag = bool(self.secondary_opts)

        if is_flag and self.default is None:
            self.default = False
            if show_default is None:
                show_default = False

        if flag_value is None:
            flag_value = not self.default

        self.show_default = show_default
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.multiple = multiple

        if self.is_flag and isinstance(self.flag_value, bool) \
           and type is None:
            self.type = BOOL
            self.is_bool_flag = True
        else:
            self.is_bool_flag = False

        self.allow_from_autoenv = allow_from_autoenv

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

    def _parse_decls(self, decls):
        opts = []
        secondary_opts = []
        name = None
        possible_names = []

        for decl in decls:
            if not decl.startswith('-'):
                if name is not None:
                    raise TypeError('Name defined twice')
                name = decl
            else:
                if '/' in decl:
                    first, second = decl.split('/', 1)
                    possible_names.append(first.lstrip('-'))
                    opts.append(first)
                    secondary_opts.append(second)
                else:
                    possible_names.append(decl.lstrip('-'))
                    opts.append(decl)

        if name is None and possible_names:
            possible_names.sort(key=len)
            name = possible_names[-1]

        if name is None:
            raise TypeError('Could not determine name for option')

        return name.replace('-', '_'), opts, secondary_opts

    def _add_to_parser(self, parser, ctx):
        help = self.help
        extra = []
        if self.default is not None and self.show_default:
            extra.append('default: %s' % self.default)
        if self.required:
            extra.append('required')
        if self.nargs != 1:
            extra.append('%d arguments' % self.nargs)
        if extra:
            help = '%s[%s]' % (help and help + '  ' or '', '; '.join(extra))

        kwargs = {
            'help': help,
            'dest': self.name,
            'nargs': self.nargs,
            'metavar': self.make_metavar(),
        }

        action = self.multiple and 'append' or 'store'

        if self.is_flag:
            kwargs.pop('nargs', None)
            if self.is_bool_flag and self.secondary_opts:
                pos_opt = _optparse.make_option(
                    *self.opts, action=action + '_true', **kwargs)
                kwargs.pop('default', None)
                kwargs.pop('help', None)
                neg_opt = _optparse.make_option(
                    *self.secondary_opts, action=action + '_false',
                    help=_optparse.SUPPRESS_HELP, **kwargs)
                pos_opt._negative_version = neg_opt
                parser.add_option(pos_opt)
                parser.add_option(neg_opt)
            else:
                parser.add_option(*self.opts, action=action + '_const',
                                  const=self.flag_value,
                                  **kwargs)
        else:
            kwargs['action'] = action
            parser.add_option(*self.opts, **kwargs)

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

    def value_from_envvar(self, ctx):
        rv = Parameter.value_from_envvar(self, ctx)
        if rv is not None:
            return rv
        if self.allow_from_autoenv and ctx.auto_envvar_prefix is not None:
            envvar = '%s_%s' % (ctx.auto_envvar_prefix, self.name.upper())
            return os.environ.get(envvar)

    def full_process_value(self, ctx, value):
        if value is None and self.prompt is not None:
            return self.prompt_for_value(ctx)
        return Parameter.full_process_value(self, ctx, value)

    def consume_value(self, ctx, opts, args):
        value = opts.get(self.name)
        if value is None:
            value = self.value_from_envvar(ctx)
        return value, args


class Argument(Parameter):
    """Arguments are positional parameters to a command.  They generally
    provide fewer features than options but can have infinite ``nargs``
    and are required by default.

    All parameters are passed onwards to the parameter constructor.
    """
    param_type_name = 'argument'

    def __init__(self, param_decls, required=True, **attrs):
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
        elif len(decls) == 2:
            name, arg = decls
        else:
            raise TypeError('Arguments take exactly one or two '
                            'parameter declarations, got %d' % len(decls))
        return name.replace('-', '_'), [arg], []

    def _add_to_parser(self, parser, ctx):
        parser.usage += ' ' + self.make_metavar()

    def consume_value(self, ctx, opts, args):
        found = True
        if self.nargs == 1:
            try:
                value = args.pop(0)
            except IndexError:
                found = False
        elif self.nargs < 0:
            value = tuple(args)
            found = value
            args = []
        else:
            values = args[:self.nargs]
            args = args[self.nargs:]
            value = tuple(values)
            found = value
        if not found:
            value = self.value_from_envvar(ctx)
            if self.nargs != 1:
                value = value and (value,) or ()
        return value, args


# Circular dependency between decorators and core
from .decorators import command, help_option

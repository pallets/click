# -*- coding: utf-8 -*-
"""
    click
    ~~~~~

    click is a simple Python module that wraps the stdlib's optparse to make
    writing command line scripts fun.  Unlike other modules it's based around
    a simple API that does not come with too much magic and is composable.

    In case optparse ever goes away from the stdlib it will be shipped by
    this module.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import codecs
import inspect
import getpass
import optparse
import re
import textwrap
import struct
from itertools import chain
from functools import update_wrapper


PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    bytes = str

    def open_stream(filename, mode='r', encoding=None, errors='strict'):
        if filename != '-':
            if encoding is not None:
                return codecs.open(filename, mode, encoding, errors), True
            return open(filename, mode), True
        if 'w' in mode:
            f = sys.stdout
            if encoding is not None:
                f = _wrap_stream_for_codec(f, encoding, errors)
        else:
            f = sys.stdin
            if 'b' not in mode:
                if encoding is None:
                    encoding = sys.stdin.encoding
                f = _wrap_stream_for_codec(f, encoding, errors)
        return f, False
else:
    text_type = str
    raw_input = input

    def open_stream(filename, mode='r', encoding=None, errors='strict'):
        if filename != '-':
            return open(filename, mode, encoding=encoding, errors=errors), True
        if 'w' in mode:
            f = sys.stdout
            if encoding is not None or 'b' in mode:
                f = f.buffer.raw
                if encoding is not None:
                    f = _wrap_stream_for_codec(f, encoding, errors)
        else:
            f = sys.stdin
            if 'b' in mode:
                f = f.buffer.raw
                if encoding is not None:
                    f = _wrap_stream_for_codec(f, encoding, errors)
        return f, False


def get_terminal_size():
    """Returns the current size of the terminal as tuple in the form
    ``(width, height)`` in columns and rows.
    """
    def ioctl_gwinsz(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except Exception:
            return
        return cr

    cr = ioctl_gwinsz(0) or ioctl_gwinsz(1) or ioctl_gwinsz(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            try:
                cr = ioctl_gwinsz(fd)
            finally:
                os.close(fd)
        except Exception:
            pass
    if not cr:
        cr = (os.environ.get('LINES', 25),
              os.environ.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])


def safecall(func):
    """Wraps a function so that it swallows exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
    return wrapper


class TextWrapper(textwrap.TextWrapper):

    def _cutdown(self, ucstr, space_left):
        l = 0
        for i in xrange(len(ucstr)):
            l += len(ucstr[i])
            if space_left < l:
                return (ucstr[:i], ucstr[i:])
        return ucstr, ''

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        space_left = max(width - cur_len, 1)

        if self.break_long_words:
            cut, res = self._cutdown(reversed_chunks[-1], space_left)
            cur_line.append(cut)
            reversed_chunks[-1] = res
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

    def fill_paragraphs(self, text):
        # Remove unnecessary newlines so that we can fill properly
        p = []
        buf = []
        for line in text.splitlines():
            if not line:
                p.append(' '.join(buf))
                buf = []
            else:
                buf.append(line)
        if buf:
            p.append(' '.join(buf))

        rv = []
        for text in p:
            rv.append(self.fill(text))
        return '\n\n'.join(rv)


def _wrap_stream_for_codec(f, encoding=None, errors='strict'):
    if encoding is None:
        encoding = 'utf-8'
    info = codecs.lookup(encoding)
    f = codecs.StreamReaderWriter(f, info.streamreader,
                                  info.streamwriter,
                                  errors)
    f.encoding = encoding
    return f


def echo(message=None, file=None):
    if file is None:
        file = sys.stdout
    if message:
        if PY2 and isinstance(message, text_type):
            message = message.encode(file.encoding)
        file.write(message)
    file.write('\n')
    file.flush()


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


def make_pass_decorator(object_type):
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
    """
    def decorator(f):
        @pass_context
        def new_func(*args, **kwargs):
            ctx = args[0]
            obj = ctx.find_object(object_type)
            if obj is None:
                raise RuntimeError('Managed to invoke callback without a '
                                   'context object of type %r existing'
                                   % object_type.__name__)
            return ctx.invoke(f, obj, *args[1:], **kwargs)
        return update_wrapper(new_func, f)
    return decorator


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


class Abort(Exception):
    """An internal signalling exception that signals click to abort."""


class _SimplifiedFormatter(optparse.IndentedHelpFormatter):

    def __init__(self):
        optparse.IndentedHelpFormatter.__init__(self,
            width=min(get_terminal_size()[0], 80) - 2)
        self.default_tag = ''

    def format_usage(self, usage):
        prefix = 'Usage: '
        indent = len(prefix)
        text_width = self.width - indent
        return '%s%s\n' % (prefix, TextWrapper(
            text_width, initial_indent='',
            subsequent_indent=' ' * indent,
            replace_whitespace=False).fill(usage))

    def _format_text(self, text):
        text_width = self.width - self.current_indent
        indent = ' ' * self.current_indent

        return TextWrapper(text_width,
                           initial_indent=indent,
                           subsequent_indent=indent,
                           replace_whitespace=False).fill_paragraphs(text)

    def format_description(self, description):
        if not description:
            return ''
        self.indent()
        rv = self._format_text(description) + '\n'
        self.dedent()
        return rv

    def format_option_strings(self, option):
        rv = optparse.IndentedHelpFormatter.format_option_strings(self, option)
        if hasattr(option, '_negative_version'):
            rv += ' / ' + optparse.IndentedHelpFormatter.format_option_strings(
                self, option._negative_version)
        return rv


class _SimplifiedOptionParser(optparse.OptionParser):

    def __init__(self, ctx, **extra):
        usage = ctx.command_path + ' ' + ctx.command.options_metavar
        optparse.OptionParser.__init__(self, prog=ctx.command_path,
                                       usage=usage,
                                       add_help_option=False,
                                       formatter=_SimplifiedFormatter(),
                                       **extra)
        self.__ctx = ctx

    def expand_prog_name(self, s):
        return s

    def format_option_help(self, formatter):
        rv = optparse.OptionParser.format_option_help(self, formatter)
        extra_help = self.__ctx.command._format_extra_help(self.__ctx)
        if extra_help:
            rv = '%s\n\n%s' % (extra_help, rv)
        return rv

    def error(self, msg):
        raise UsageError(msg, self.__ctx)


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
        parser = _SimplifiedOptionParser(ctx, description=self.help,
                                         epilog=self.epilog)
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
                 no_args_is_help=None,
                 subcommand_metavar='COMMAND [ARGS]...', **attrs):
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
            message = 'Invalid value for %s: %s' % (param.name, message)
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
    name = 'choice'

    def __init__(self, choices):
        self.choices = choices

    def get_metavar(self, param):
        return '[%s]' % '|'.join(self.choices)

    def convert(self, value, param, ctx):
        if value in self.choices:
            return value
        self.fail('invalid choice: %s. (chose from %s)' %
                  (value, ', '.join(self.choices)), param, ctx)

    def __repr__(self):
        return 'Choice(%r)' % list(self.choices)


class Regex(Choice):
    name = 'regex'

    def convert(self, value, param, ctx):
        for pattern in self.choices:
            if re.match(pattern, value):
                return value
            continue
        self.fail('invalid value: %s. (can\'t match either of [%s])' %
                  (value, ', '.join(self.choices)), param, ctx)

    def __repr__(self):
        return 'Regex(%r)' % list(self.choices)


class IntParamType(ParamType):
    name = 'integer'

    def convert(self, value, param, ctx):
        try:
            return int(value)
        except ValueError:
            self.fail('%s is not a valid integer' % value, param, ctx)

    def __repr__(self):
        return 'INT'


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


class File(ParamType):
    """Declares a parameter to be a file for reading or writing.  The file
    is automatically closed once the context tears down (after the command
    finished working).

    Files can be opened for reading or writing.  The special value ``-``
    indicates stdin or stdout depending on the mode.

    By default the file is opened for reading text data but it can also be
    opened in binary mode or for writing.  The encoding parameter can be used
    to force a specific encoding.
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
            prompt = self.name.replace('_', ' ').capitalize()
        elif prompt is False:
            prompt = None
        self.prompt = prompt
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
            self.type = BoolParamType()
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
                pos_opt = optparse.Option(*self.opts, action=action + '_true',
                                          **kwargs)
                kwargs.pop('default', None)
                kwargs.pop('help', None)
                neg_opt = optparse.Option(*self.secondary_opts,
                                          action=action + '_false',
                                          help=optparse.SUPPRESS_HELP,
                                          **kwargs)
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


def command(name=None, **attrs):
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
    """
    def decorator(f):
        return _make_command(f, name, attrs, Command)
    return decorator


def group(name=None, **attrs):
    """Creates a new :class:`Group` with a function as callback.  This
    works otherwise the same as :func:`command` just that the generated
    class is different.
    """
    def decorator(f):
        return _make_command(f, name, attrs, Group)
    return decorator


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
                echo(ctx.format_help())
                ctx.exit()
        attrs.setdefault('is_flag', True)
        attrs.setdefault('expose_value', False)
        attrs.setdefault('help', 'Show this message and exit.')
        attrs.setdefault('is_eager', True)
        attrs['callback'] = callback
        return option(*(param_decls or ('--help',)), **attrs)(f)
    return decorator


def confirm(text, default=False, abort=False):
    """Prompts for confirmation (yes/no question).

    If the user aborts the input by sending a interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the question to ask.
    :param default: the default for the prompt.
    :param abort: if this is set to `True` a negative answer aborts the
                  exception by raising :exc:`Abort`.
    """
    prompt = '%s [%s]: ' % (text, default and 'Yn' or 'yN')
    while 1:
        try:
            value = raw_input(prompt).lower().strip()
        except (KeyboardInterrupt, EOFError):
            raise Abort()
        if value in ('y', 'yes'):
            rv = True
        elif value in ('n', 'no'):
            rv = False
        elif value == '':
            rv = default
        else:
            echo('Error: invalid input')
            continue
        break
    if abort and not rv:
        raise Abort()
    return rv


def prompt(text, default=None, hide_input=False,
           confirmation_prompt=False, type=None,
           value_proc=None):
    """Prompts a user for input.  This is a convenience function that can
    be used to prompt a user for input later.

    If the user aborts the input by sending a interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the text to show for the prompt.
    :param default: the default value to use if no input happens.  If this
                    is not given it will prompt until it's aborted.
    :param hide_input: if this is set to true then the input value will
                       be hidden.
    :param confirmation_prompt: asks for confirmation for the value.
    :param type: the type to use to check the value against.
    :param value_proc: if this parameter is provided it's a function that
                       is invoked instead of the type conversion to
                       convert a value.
    """
    result = None

    def prompt_func(text):
        f = hide_input and getpass.getpass or raw_input
        try:
            return f(text)
        except (KeyboardInterrupt, EOFError):
            raise Abort()

    if value_proc is None:
        value_proc = convert_type(type, default)

    prompt = text
    if default is not None:
        prompt = '%s [%s]' % (prompt, default)
    prompt += ': '

    while 1:
        while 1:
            value = prompt_func(prompt)
            if value:
                break
            # If a default is set and used, then the confirmation
            # prompt is always skipped because that's the only thing
            # that really makes sense.
            elif default is not None:
                return default
        try:
            result = value_proc(value)
        except UsageError as e:
            echo('Error: %s' % e.message)
            continue
        if not confirmation_prompt:
            return result
        while 1:
            value2 = prompt_func('Repeat for confirmation: ')
            if value2:
                break
        if value == value2:
            return result
        echo('Error: the two entered values do not match')


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

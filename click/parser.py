# -*- coding: utf-8 -*-
"""
    click.parser
    ~~~~~~~~~~~~

    This module started out as largely a copy paste from the stdlib's
    optparse module with the features removed that we do not need from
    optparse because we implement them in click on a higher level (for
    instance type handling, help formatting and a lot more).

    The plan is to remove more and more from here over time.

    The reason this is a different module and not optparse from the stdlib
    is that there are differences in 2.x and 3.x about the error messages
    generated and optparse in the stdlib uses gettext for no good reason
    and might cause us issues.
"""
from .exceptions import UsageError
from .utils import unpack_args


def split_opt(opt):
    first = opt[:1]
    if first.isalnum():
        return '', opt
    if opt[1:2] == first:
        return opt[:2], opt[2:]
    return first, opt[1:]


class Option(object):

    def __init__(self, opts, dest, action=None, nargs=1, const=None, obj=None):
        self._short_opts = []
        self._long_opts = []
        self.prefixes = set()

        for opt in opts:
            prefix = split_opt(opt)[0]
            if not prefix:
                raise ValueError('Invalid start character for option (%s)'
                                 % opt)
            self.prefixes.add(prefix[0])
            if len(prefix) == 1:
                self._short_opts.append(opt)
            else:
                self._long_opts.append(opt)
                self.prefixes.add(prefix)

        if action is None:
            action = 'store'

        self.dest = dest
        self.action = action
        self.nargs = nargs
        self.const = const
        self.obj = obj

    @property
    def takes_value(self):
        return self.action in ('store', 'append')

    def process(self, value, state):
        if self.action == 'store':
            state.opts[self.dest] = value
        elif self.action == 'store_const':
            state.opts[self.dest] = self.const
        elif self.action == 'append':
            state.opts.setdefault(self.dest, []).append(value)
        elif self.action == 'append_const':
            state.opts.setdefault(self.dest, []).append(self.const)
        elif self.action == 'count':
            state.opts[self.dest] = state.opts.get(self.dest, 0) + 1
        else:
            raise ValueError('unknown action %r' % self.action)
        state.order.append(self.obj)


class Argument(object):

    def __init__(self, dest, nargs=1, obj=None):
        self.dest = dest
        self.nargs = nargs
        self.obj = obj

    def process(self, value, state):
        state.opts[self.dest] = value
        state.order.append(self.obj)


class ParsingState(object):

    def __init__(self, rargs):
        self.opts = {}
        self.largs = []
        self.rargs = rargs
        self.order = []


class OptionParser(object):
    """The option parser is an internal class that is ultimately used to
    parse options and arguments.  It's modelled after optparse and brings
    a similar but vastly simplified API.  It should generally not be used
    directly as the high level click classes wrap it for you.

    It's not nearly as extensible as optparse or argparse as it does not
    implement features that are implemented on a higher level (such as
    types or defaults).

    :param ctx: optionally the :class:`~click.Context` where this parser
                should go with.
    """

    def __init__(self, ctx=None):
        #: The :class:`~click.Context` for this parser.  This might be
        #: `None` for some advanced use cases.
        self.ctx = ctx
        #: This controls how the parser deals with interspersed arguments.
        #: If this is set to `False`, the parser will stop on the first
        #: non-option.  Click uses this to implement nested subcommands
        #: safely.
        self.allow_interspersed_args = True
        self._short_opt = {}
        self._long_opt = {}
        self._opt_prefixes = set(['-', '--'])
        self._args = []

    def add_option(self, opts, dest, action=None, nargs=1, const=None,
                   obj=None):
        """Adds a new option named `dest` to the parser.  The destination
        is not inferred unlike with optparse and needs to be explicitly
        provided.  Action can be any of ``store``, ``store_const``,
        ``append``, ``appnd_const`` or ``count``.

        The `obj` can be used to identify the option in the order list
        that is returned from the parser.
        """
        if obj is None:
            obj = dest
        option = Option(opts, dest, action=action, nargs=nargs,
                        const=const, obj=obj)
        self._opt_prefixes.update(option.prefixes)
        for opt in option._short_opts:
            self._short_opt[opt] = option
        for opt in option._long_opts:
            self._long_opt[opt] = option

    def add_argument(self, dest, nargs=1, obj=None):
        """Adds a positional argument named `dest` to the parser.

        The `obj` can be used to identify the option in the order list
        that is returned from the parser.
        """
        if obj is None:
            obj = dest
        self._args.append(Argument(dest=dest, nargs=nargs, obj=obj))

    def parse_args(self, args):
        """Parses positional arguments and returns ``(values, args, order)``
        for the parsed options and arguments as well as the leftover
        arguments if there are any.  The order is a list of objects as they
        appear on the command line.  If arguments appear multiple times they
        will be memorized multiple times as well.
        """
        state = ParsingState(args)
        self._process_args_for_options(state)
        self._process_args_for_args(state)
        return state.opts, state.largs, state.order

    def _process_args_for_args(self, state):
        pargs, args = unpack_args(state.largs + state.rargs,
                                  [x.nargs for x in self._args])

        for idx, arg in enumerate(self._args):
            arg.process(pargs[idx], state)

        state.largs = args
        state.rargs = []

    def _process_args_for_options(self, state):
        while state.rargs:
            arg = state.rargs[0]
            arglen = len(arg)
            # Double dash es always handled explicitly regardless of what
            # prefixes are valid.
            if arg == '--':
                del state.rargs[0]
                return
            elif arg[:2] in self._opt_prefixes and arglen > 2:
                # process a single long option (possibly with value(s))
                self._process_long_opt(state)
            elif arg[:1] in self._opt_prefixes and arglen > 1:
                # process a cluster of short options (possibly with
                # value(s) for the last one only)
                self._process_short_opts(state)
            elif self.allow_interspersed_args:
                state.largs.append(arg)
                del state.rargs[0]
            else:
                return

        # Say this is the original argument list:
        # [arg0, arg1, ..., arg(i-1), arg(i), arg(i+1), ..., arg(N-1)]
        #                            ^
        # (we are about to process arg(i)).
        #
        # Then rargs is [arg(i), ..., arg(N-1)] and largs is a *subset* of
        # [arg0, ..., arg(i-1)] (any options and their arguments will have
        # been removed from largs).
        #
        # The while loop will usually consume 1 or more arguments per pass.
        # If it consumes 1 (eg. arg is an option that takes no arguments),
        # then after _process_arg() is done the situation is:
        #
        #   largs = subset of [arg0, ..., arg(i)]
        #   rargs = [arg(i+1), ..., arg(N-1)]
        #
        # If allow_interspersed_args is false, largs will always be
        # *empty* -- still a subset of [arg0, ..., arg(i-1)], but
        # not a very interesting subset!

    def _match_long_opt(self, opt):
        # Is there an exact match?
        if opt in self._long_opt:
            return opt

        # Isolate all words with s as a prefix.
        possibilities = [word for word in self._long_opt
                         if word.startswith(opt)]

        # No exact match, so there had better be just one possibility.
        if not possibilities:
            self._error('no such option: %s' % opt)
        elif len(possibilities) == 1:
            self._error('no such option: %s.  Did you mean %s?' %
                        (opt, possibilities[0]))
            return possibilities[0]
        else:
            # More than one possible completion: ambiguous prefix.
            possibilities.sort()
            self._error('no such option: %s.  (Possible options: %s)'
                        % (opt, ', '.join(possibilities)))

    def _process_long_opt(self, state):
        arg = state.rargs.pop(0)

        # Value explicitly attached to arg?  Pretend it's the next
        # argument.
        if '=' in arg:
            opt, next_arg = arg.split('=', 1)
            state.rargs.insert(0, next_arg)
            had_explicit_value = True
        else:
            opt = arg
            had_explicit_value = False

        opt = self._match_long_opt(opt)
        option = self._long_opt[opt]
        if option.takes_value:
            nargs = option.nargs
            if len(state.rargs) < nargs:
                if nargs == 1:
                    self._error('%s option requires an argument' % opt)
                else:
                    self._error('%s option requires %d arguments' % (opt, nargs))
            elif nargs == 1:
                value = state.rargs.pop(0)
            else:
                value = tuple(state.rargs[:nargs])
                del state.rargs[:nargs]

        elif had_explicit_value:
            self._error('%s option does not take a value' % opt)

        else:
            value = None

        option.process(value, state)

    def _process_short_opts(self, state):
        arg = state.rargs.pop(0)
        stop = False
        i = 1
        prefix = arg[0]
        for ch in arg[1:]:
            opt = prefix + ch
            option = self._short_opt.get(opt)
            i += 1

            if not option:
                self._error('no such option: %s' % opt)
            if option.takes_value:
                # Any characters left in arg?  Pretend they're the
                # next arg, and stop consuming characters of arg.
                if i < len(arg):
                    state.rargs.insert(0, arg[i:])
                    stop = True

                nargs = option.nargs
                if len(state.rargs) < nargs:
                    if nargs == 1:
                        self._error('%s option requires an argument' % opt)
                    else:
                        self._error('%s option requires %d arguments' %
                                    (opt, nargs))
                elif nargs == 1:
                    value = state.rargs.pop(0)
                else:
                    value = tuple(state.rargs[:nargs])
                    del state.rargs[:nargs]

            else:
                value = None

            option.process(value, state)

            if stop:
                break

    def _error(self, msg):
        raise UsageError(msg, self.ctx)

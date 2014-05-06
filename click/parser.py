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


class Option(object):

    def __init__(self, opts, dest, action=None, nargs=1, const=None):
        self._short_opts = []
        self._long_opts = []
        self.prefixes = set()

        for opt in opts:
            first = opt[:1]
            if first.isalnum():
                raise ValueError('Invalid start character for option (%s)'
                                 % first)
            self.prefixes.add(first)
            if opt[1:2] != first:
                self._short_opts.append(opt)
            else:
                self._long_opts.append(opt)
                self.prefixes.add(opt[:2])

        if action is None:
            action = 'store'

        self.dest = dest
        self.action = action
        self.nargs = nargs
        self.const = const

    @property
    def takes_value(self):
        return self.action in ('store', 'append')

    def process(self, opt, value, opts, parser):
        if self.action == 'store':
            opts[self.dest] = value
        elif self.action == 'store_const':
            opts[self.dest] = self.const
        elif self.action == 'append':
            opts.setdefault(self.dest, []).append(value)
        elif self.action == 'append_const':
            opts.setdefault(self.dest, []).append(self.const)
        elif self.action == 'count':
            opts[self.dest] = opts.get(self.dest, 0) + 1
        else:
            raise ValueError('unknown action %r' % self.action)


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
        self._arg_dest = []
        self._nargs = []
        self._opt_prefixes = set(['-', '--'])

    def add_option(self, opts, dest, action=None, nargs=1, const=None):
        """Adds a new option named `dest` to the parser.  The destination
        is not inferred unlike with optparse and needs to be explicitly
        provided.  Action can be any of ``store``, ``store_const``,
        ``append``, ``appnd_const`` or ``count``.
        """
        option = Option(opts, dest, action=action, nargs=nargs, const=const)
        self._opt_prefixes.update(option.prefixes)
        for opt in option._short_opts:
            self._short_opt[opt] = option
        for opt in option._long_opts:
            self._long_opt[opt] = option

    def add_argument(self, dest, nargs=1):
        """Adds a positional argument named `dest` to the parser."""
        self._arg_dest.append(dest)
        self._nargs.append(nargs)

    def parse_args(self, args):
        """Parses positional arguments and returns ``(values, args)`` for
        the parsed options and arguments as well as the leftover arguments
        if there are any.
        """
        rargs = args
        opts = {}
        largs = []

        self._process_args_for_options(largs, rargs, opts)
        args = self._process_args_for_args(largs, rargs, opts)

        return opts, args

    def _process_args_for_args(self, largs, rargs, opts):
        pargs, args = unpack_args(largs + rargs, self._nargs)
        for idx, arg_name in enumerate(self._arg_dest):
            opts[arg_name] = pargs[idx]
        return args

    def _process_args_for_options(self, largs, rargs, opts):
        while rargs:
            arg = rargs[0]
            # Double dash es always handled explicitly regardless of what
            # prefixes are valid.
            if arg == '--':
                del rargs[0]
                return
            elif arg[0:2] in self._opt_prefixes:
                # process a single long option (possibly with value(s))
                self._process_long_opt(rargs, opts)
            elif arg[:1] in self._opt_prefixes and len(arg) > 1:
                # process a cluster of short options (possibly with
                # value(s) for the last one only)
                self._process_short_opts(rargs, opts)
            elif self.allow_interspersed_args:
                largs.append(arg)
                del rargs[0]
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

    def _process_long_opt(self, rargs, opts):
        arg = rargs.pop(0)

        # Value explicitly attached to arg?  Pretend it's the next
        # argument.
        if '=' in arg:
            opt, next_arg = arg.split('=', 1)
            rargs.insert(0, next_arg)
            had_explicit_value = True
        else:
            opt = arg
            had_explicit_value = False

        opt = self._match_long_opt(opt)
        option = self._long_opt[opt]
        if option.takes_value:
            nargs = option.nargs
            if len(rargs) < nargs:
                if nargs == 1:
                    self._error('%s option requires an argument' % opt)
                else:
                    self._error('%s option requires %d arguments' % (opt, nargs))
            elif nargs == 1:
                value = rargs.pop(0)
            else:
                value = tuple(rargs[:nargs])
                del rargs[:nargs]

        elif had_explicit_value:
            self._error('%s option does not take a value' % opt)

        else:
            value = None

        option.process(opt, value, opts, self)

    def _process_short_opts(self, rargs, opts):
        arg = rargs.pop(0)
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
                    rargs.insert(0, arg[i:])
                    stop = True

                nargs = option.nargs
                if len(rargs) < nargs:
                    if nargs == 1:
                        self._error('%s option requires an argument' % opt)
                    else:
                        self._error('%s option requires %d arguments' %
                                    (opt, nargs))
                elif nargs == 1:
                    value = rargs.pop(0)
                else:
                    value = tuple(rargs[:nargs])
                    del rargs[:nargs]

            else:
                value = None

            option.process(opt, value, opts, self)

            if stop:
                break

    def _error(self, msg):
        raise UsageError(msg, self.ctx)

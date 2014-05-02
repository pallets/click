# -*- coding: utf-8 -*-
"""
    click._optparse
    ~~~~~~~~~~~~~~~

    This module is largely a copy paste from the stdlib's optparse module
    with the features removed that we do not need from optparse because
    we implement them in click on a higher level (for instance type
    handling, help formatting and a lot more).

    The plan is to remove more and more from here over time.

    The reason this is a different module and not optparse from the stdlib
    is that there are differences in 2.x and 3.x about the error messages
    generated and optparse in the stdlib uses gettext for no good reason
    and might cause us issues.
"""
import sys

from .exceptions import UsageError


class Option(object):
    ATTRS = ['action', 'type', 'dest', 'nargs', 'const', 'help',
             'metavar']
    ACTIONS = ('store', 'store_const', 'append', 'append_const')
    STORE_ACTIONS = ('store', 'store_const', 'append', 'append_const')
    TYPED_ACTIONS = ('store', 'append')
    TAKES_VALUE_ACTIONS = ('store', 'append')
    CONST_ACTIONS = ('store_const', 'append_const')

    def __init__(self, *opts, **attrs):
        self._short_opts = []
        self._long_opts = []

        for opt in opts:
            if len(opt) < 2:
                raise TypeError(
                    'invalid option string %r: '
                    'must be at least two characters long' % opt)
            elif len(opt) == 2:
                if not (opt[0] == '-' and opt[1] != '-'):
                    raise TypeError(
                        'invalid short option string %r: '
                        'must be of the form -x, (x any non-dash char)' % opt)
                self._short_opts.append(opt)
            else:
                if not (opt[:2] == '--' and opt[2] != '-'):
                    raise TypeError(
                        'invalid long option string %r: '
                        'must start with --, followed by non-dash' % opt)
                self._long_opts.append(opt)

        for attr in self.ATTRS:
            if attr in attrs:
                setattr(self, attr, attrs[attr])
                del attrs[attr]
            else:
                setattr(self, attr, None)
        if attrs:
            attrs = sorted(attrs.keys())
            raise TypeError('invalid keyword arguments: %s' %
                            ', '.join(attrs))

        if self.action is None:
            self.action = 'store'
        if self.action in self.TYPED_ACTIONS:
            if self.nargs is None:
                self.nargs = 1

    @property
    def takes_value(self):
        return self.action in self.TAKES_VALUE_ACTIONS

    def get_opt_string(self):
        if self._long_opts:
            return self._long_opts[0]
        return self._short_opts[0]

    def process(self, opt, value, values, parser):
        if self.action == 'store':
            values[self.dest] = value
        elif self.action == 'store_const':
            values[self.dest] = self.const
        elif self.action == 'append':
            values.setdefault(self.dest, []).append(value)
        elif self.action == 'append_const':
            values.setdefault(self.dest, []).append(self.const)
        else:
            raise ValueError('unknown action %r' % self.action)


class OptionContainer(object):

    def __init__(self, option_class):
        # Initialize the option list and related data structures.
        # This method must be provided by subclasses, and it must
        # initialize at least the following instance attributes:
        # option_list, _short_opt, _long_opt.
        self._create_option_list()

        self.option_class = option_class

    def _create_option_mappings(self):
        # For use by OptionParser constructor -- create the master
        # option mappings used by this OptionParser and all
        # OptionGroups that it owns.
        self._short_opt = {}            # single letter -> Option instance
        self._long_opt = {}             # long option -> Option instance

    def add_option(self, *args, **kwargs):
        if isinstance(args[0], str):
            option = self.option_class(*args, **kwargs)
        elif len(args) == 1 and not kwargs:
            option = args[0]
            if not isinstance(option, Option):
                raise TypeError('not an Option instance: %r' % option)
        else:
            raise TypeError('invalid arguments')

        self.option_list.append(option)
        option.container = self
        for opt in option._short_opts:
            self._short_opt[opt] = option
        for opt in option._long_opts:
            self._long_opt[opt] = option

        return option

    def add_options(self, option_list):
        for option in option_list:
            self.add_option(option)

    def get_option(self, opt_str):
        return (self._short_opt.get(opt_str) or
                self._long_opt.get(opt_str))

    def has_option(self, opt_str):
        return (opt_str in self._short_opt or
                opt_str in self._long_opt)

    def remove_option(self, opt_str):
        option = self._short_opt.get(opt_str)
        if option is None:
            option = self._long_opt.get(opt_str)
        if option is None:
            raise ValueError('no such option %r' % opt_str)

        for opt in option._short_opts:
            del self._short_opt[opt]
        for opt in option._long_opts:
            del self._long_opt[opt]
        option.container.option_list.remove(option)


class OptionParser(OptionContainer):

    def __init__(self, option_list=None, option_class=Option):
        OptionContainer.__init__(self, option_class)
        self.allow_interspersed_args = True
        if option_list:
            self.add_options(option_list)
        self._init_parsing_state()

    def _create_option_list(self):
        self.option_list = []
        self._create_option_mappings()

    def _init_parsing_state(self):
        self.rargs = None
        self.largs = None
        self.values = None

    def parse_args(self, args, values=None):
        rargs = args
        if values is None:
            values = {}
        self.rargs = rargs
        self.largs = largs = []
        self.values = values

        self._process_args(largs, rargs, values)

        args = largs + rargs
        return values, args

    def _process_args(self, largs, rargs, values):
        while rargs:
            arg = rargs[0]
            # We handle bare '--' explicitly, and bare '-' is handled by the
            # standard arg handler since the short arg case ensures that the
            # len of the opt string is greater than 1.
            if arg == '--':
                del rargs[0]
                return
            elif arg[0:2] == '--':
                # process a single long option (possibly with value(s))
                self._process_long_opt(rargs, values)
            elif arg[:1] == '-' and len(arg) > 1:
                # process a cluster of short options (possibly with
                # value(s) for the last one only)
                self._process_short_opts(rargs, values)
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
            self.error('no such option: %s' % opt)
        elif len(possibilities) == 1:
            self.error('no such option: %s.  Did you mean %s?' %
                       (opt, possibilities[0]))
            return possibilities[0]
        else:
            # More than one possible completion: ambiguous prefix.
            possibilities.sort()
            self.error('no such option: %s.  (Possible options: %s)'
                       % (opt, ', '.join(possibilities)))

    def _process_long_opt(self, rargs, values):
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
                    self.error('%s option requires an argument' % opt)
                else:
                    self.error('%s option requires %d arguments' % (opt, nargs))
            elif nargs == 1:
                value = rargs.pop(0)
            else:
                value = tuple(rargs[0:nargs])
                del rargs[0:nargs]

        elif had_explicit_value:
            self.error('%s option does not take a value' % opt)

        else:
            value = None

        option.process(opt, value, values, self)

    def _process_short_opts(self, rargs, values):
        arg = rargs.pop(0)
        stop = False
        i = 1
        for ch in arg[1:]:
            opt = '-' + ch
            option = self._short_opt.get(opt)
            i += 1                      # we have consumed a character

            if not option:
                self.error('no such option: %s' % opt)
            if option.takes_value:
                # Any characters left in arg?  Pretend they're the
                # next arg, and stop consuming characters of arg.
                if i < len(arg):
                    rargs.insert(0, arg[i:])
                    stop = True

                nargs = option.nargs
                if len(rargs) < nargs:
                    if nargs == 1:
                        self.error('%s option requires an argument' % opt)
                    else:
                        self.error('%s option requires %d arguments' %
                                   (opt, nargs))
                elif nargs == 1:
                    value = rargs.pop(0)
                else:
                    value = tuple(rargs[0:nargs])
                    del rargs[0:nargs]

            else:
                value = None

            option.process(opt, value, values, self)

            if stop:
                break

    def exit(self, status=0, msg=None):
        if msg:
            sys.stderr.write(msg)
        sys.exit(status)

    def error(self, msg):
        raise Exception(msg)


class _SimplifiedOptionParser(OptionParser):

    def __init__(self, ctx, **extra):
        OptionParser.__init__(self, **extra)
        self.__ctx = ctx

    def error(self, msg):
        raise UsageError(msg, self.__ctx)

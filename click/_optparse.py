# -*- coding: utf-8 -*-
"""
    click._optparse
    ~~~~~~~~~~~~~~~

    This module is largely a copy paste from the stdlib's optparse module
    with the features removed that we do not need from optparse because
    we implement them in click on a higher level (for instance type
    handling and some other things).

    The plan is to remove more and more from here over time.

    The reason this is a different module and not optparse from the stdlib
    is that there are differences in 2.x and 3.x about the error messages
    generated and optparse in the stdlib uses gettext for no good reason
    and might cause us issues.
"""
import os
import sys
import textwrap

from .helpers import get_terminal_size
from .formatting import TextWrapper
from .exceptions import UsageError


class HelpFormatter(object):

    def __init__(self, indent_increment, max_help_position, width,
                 short_first):
        self.parser = None
        self.indent_increment = indent_increment
        if width is None:
            width = min(get_terminal_size()[0], 80) - 2
        self.width = width
        self.help_position = self.max_help_position = \
            min(max_help_position, max(width - 20, indent_increment * 2))
        self.current_indent = 0
        self.level = 0
        self.help_width = None
        self.short_first = short_first
        self.option_strings = {}
        self._short_opt_fmt = '%s %s'
        self._long_opt_fmt = '%s=%s'

    def set_parser(self, parser):
        self.parser = parser

    def indent(self):
        self.current_indent += self.indent_increment
        self.level += 1

    def dedent(self):
        self.current_indent -= self.indent_increment
        assert self.current_indent >= 0, 'Indent decreased below 0.'
        self.level -= 1

    def format_usage(self, usage):
        raise NotImplementedError('subclasses must implement')

    def format_heading(self, heading):
        raise NotImplementedError('subclasses must implement')

    def _format_text(self, text):
        """
        Format a paragraph of free-form text for inclusion in the
        help output at the current indentation level.
        """
        text_width = max(self.width - self.current_indent, 11)
        indent = ' ' * self.current_indent
        return textwrap.fill(text,
                             text_width,
                             initial_indent=indent,
                             subsequent_indent=indent)

    def format_description(self, description):
        if description:
            return self._format_text(description) + '\n'
        else:
            return ''

    def format_epilog(self, epilog):
        if epilog:
            return '\n' + self._format_text(epilog) + '\n'
        else:
            return ''

    def format_option(self, option):
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = '%*s%s\n' % (self.current_indent, '', opts)
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = '%*s%-*s  ' % (self.current_indent, '', opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = option.help
            help_lines = textwrap.wrap(help_text, self.help_width)
            result.append('%*s%s\n' % (indent_first, '', help_lines[0]))
            result.extend(['%*s%s\n' % (self.help_position, '', line)
                           for line in help_lines[1:]])
        elif opts[-1] != '\n':
            result.append('\n')
        return ''.join(result)

    def store_option_strings(self, parser):
        self.indent()
        max_len = 0
        for opt in parser.option_list:
            strings = self.format_option_strings(opt)
            self.option_strings[opt] = strings
            max_len = max(max_len, len(strings) + self.current_indent)
        self.dedent()
        self.help_position = min(max_len + 2, self.max_help_position)
        self.help_width = max(self.width - self.help_position, 11)

    def format_option_strings(self, option):
        if option.takes_value:
            metavar = option.metavar or option.dest.upper()
            short_opts = [self._short_opt_fmt % (sopt, metavar)
                          for sopt in option._short_opts]
            long_opts = [self._long_opt_fmt % (lopt, metavar)
                         for lopt in option._long_opts]
        else:
            short_opts = option._short_opts
            long_opts = option._long_opts

        if self.short_first:
            opts = short_opts + long_opts
        else:
            opts = long_opts + short_opts

        return ', '.join(opts)


class IndentedHelpFormatter(HelpFormatter):
    """Format help with indented section bodies.
    """

    def __init__(self, indent_increment=2, max_help_position=24,
                 width=None, short_first=1):
        HelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        return 'Usage: %s\n' % usage

    def format_heading(self, heading):
        return '%*s%s:\n' % (self.current_indent, '', heading)


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
            if value.startswith('~/'):
                value = os.path.join(os.environ['HOME'], value[2:])
            values[self.dest] = value
        elif self.action == 'store_const':
            values[self.dest] = self.const
        elif self.action == 'append':
            values.setdefault(self.dest, []).append(value)
        elif self.action == 'append_const':
            values.setdefault(self.dest, []).append(self.const)
        else:
            raise ValueError('unknown action %r' % self.action)


SUPPRESS_HELP = object()


class OptionContainer(object):

    def __init__(self, option_class, description):
        # Initialize the option list and related data structures.
        # This method must be provided by subclasses, and it must
        # initialize at least the following instance attributes:
        # option_list, _short_opt, _long_opt.
        self._create_option_list()

        self.option_class = option_class
        self.description = description

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

    def format_option_help(self, formatter):
        if not self.option_list:
            return ''
        result = []
        for option in self.option_list:
            if not option.help is SUPPRESS_HELP:
                result.append(formatter.format_option(option))
        return ''.join(result)

    def format_description(self, formatter):
        return formatter.format_description(self.description)

    def format_help(self, formatter):
        result = []
        if self.description:
            result.append(self.format_description(formatter))
        if self.option_list:
            result.append(self.format_option_help(formatter))
        return '\n'.join(result)


class OptionParser(OptionContainer):
    standard_option_list = []

    def __init__(self,
                 usage=None,
                 option_list=None,
                 option_class=Option,
                 description=None,
                 formatter=None,
                 epilog=None):
        OptionContainer.__init__(
            self, option_class, description)
        self.usage = usage
        self.allow_interspersed_args = True
        if formatter is None:
            formatter = IndentedHelpFormatter()
        self.formatter = formatter
        self.formatter.set_parser(self)
        self.epilog = epilog

        self._populate_option_list(option_list)

        self._init_parsing_state()

    def _create_option_list(self):
        self.option_list = []
        self._create_option_mappings()

    def _populate_option_list(self, option_list):
        if self.standard_option_list:
            self.add_options(self.standard_option_list)
        if option_list:
            self.add_options(option_list)

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
                self.fail('no such option: %s' % opt)
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

    def get_usage(self):
        if self.usage:
            return self.formatter.format_usage(self.usage)
        return ''

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        result.append(formatter.format_heading('Options'))
        formatter.indent()
        if self.option_list:
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append('\n')
        formatter.dedent()
        # Drop the last '\n', or the header if no options or option groups:
        return ''.join(result[:-1])

    def format_epilog(self, formatter):
        return formatter.format_epilog(self.epilog)

    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        result = []
        if self.usage:
            result.append(self.get_usage() + '\n')
        if self.description:
            result.append(self.format_description(formatter) + '\n')
        result.append(self.format_option_help(formatter))
        result.append(self.format_epilog(formatter))
        return ''.join(result)


class _SimplifiedFormatter(IndentedHelpFormatter):

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
        rv = IndentedHelpFormatter.format_option_strings(self, option)
        if hasattr(option, '_negative_version'):
            rv += ' / ' + IndentedHelpFormatter.format_option_strings(
                self, option._negative_version)
        return rv


class _SimplifiedOptionParser(OptionParser):

    def __init__(self, ctx, **extra):
        usage = ctx.command_path + ' ' + ctx.command.options_metavar
        OptionParser.__init__(self, usage=usage,
                              formatter=_SimplifiedFormatter(),
                              **extra)
        self.__ctx = ctx

    def format_option_help(self, formatter):
        rv = OptionParser.format_option_help(self, formatter)
        extra_help = self.__ctx.command.format_extra_help(self.__ctx)
        if extra_help:
            rv = '%s\n%s' % (rv, extra_help)
        return rv

    def error(self, msg):
        raise UsageError(msg, self.__ctx)

import sys

# optparse never fully supported gettext but for some reason it still
# imports it which slows things down quite a bit.  In case we are the
# first importer of optparse and gettext we can disable gettext support
# through this hackery.
#
# In case someone does depend on gettext being loaded into optparse we
# might have a problem but I don't think anyone will actually notice.
_gettext = sys.modules.get('gettext')
sys.modules['gettext'] = None
from optparse import IndentedHelpFormatter, OptionParser, Option
if _gettext is not None:
    sys.modules['gettext'] = _gettext

from .helpers import get_terminal_size
from .formatting import TextWrapper
from .exceptions import UsageError


class _SimplifiedFormatter(IndentedHelpFormatter):

    def __init__(self):
        IndentedHelpFormatter.__init__(self,
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
        rv = IndentedHelpFormatter.format_option_strings(self, option)
        if hasattr(option, '_negative_version'):
            rv += ' / ' + IndentedHelpFormatter.format_option_strings(
                self, option._negative_version)
        return rv


class _SimplifiedOptionParser(OptionParser):

    def __init__(self, ctx, **extra):
        usage = ctx.command_path + ' ' + ctx.command.options_metavar
        OptionParser.__init__(self, prog=ctx.command_path,
                              usage=usage,
                              add_help_option=False,
                              formatter=_SimplifiedFormatter(),
                              **extra)
        self.__ctx = ctx

    def expand_prog_name(self, s):
        return s

    def format_option_help(self, formatter):
        rv = OptionParser.format_option_help(self, formatter)
        extra_help = self.__ctx.command._format_extra_help(self.__ctx)
        if extra_help:
            rv = '%s\n\n%s' % (extra_help, rv)
        return rv

    def error(self, msg):
        raise UsageError(msg, self.__ctx)


make_option = Option

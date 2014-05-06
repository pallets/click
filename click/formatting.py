import textwrap
from contextlib import contextmanager

from .termui import get_terminal_size


def measure_table(rows):
    widths = {}
    for row in rows:
        for idx, col in enumerate(row):
            widths[idx] = max(widths.get(idx, 0), len(col))
    return tuple(y for x, y in sorted(widths.items()))


def iter_rows(rows, col_count):
    for row in rows:
        row = tuple(row)
        yield row + ('',) * (col_count - len(row))


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

    @contextmanager
    def extra_indent(self, indent):
        old_initial_indent = self.initial_indent
        old_subsequent_indent = self.subsequent_indent
        self.initial_indent += indent
        self.subsequent_indent += indent
        try:
            yield
        finally:
            self.initial_indent = old_initial_indent
            self.subsequent_indent = old_subsequent_indent


def wrap_text(text, width=78, initial_indent='', subsequent_indent='',
              preserve_paragraphs=False):
    """A helper function that intelligently wraps text.  By default it
    assumes that it operates on a single paragraph of text but if the
    `preserve_paragraphs` parameter is provided it will intelligently
    handle paragraphs (defined by two empty lines).

    :param text: the text that should be rewrapped.
    :param width: the maximum width for the text.
    :param initial_indent: the initial indent that should be placed on the
                           first line as a string.
    :param subsequent_indent: the indent string that should be placed on
                              each consecutive line.
    :param preserve_paragraphs: if this flag is set then the wrapping will
                                intelligently handle paragraphs.
    """
    text = text.expandtabs()
    wrapper = TextWrapper(width, initial_indent=initial_indent,
                          subsequent_indent=subsequent_indent,
                          replace_whitespace=False)
    if not preserve_paragraphs:
        return wrapper.fill(text)

    p = []
    buf = []
    indent = 0
    for line in text.splitlines():
        if not line:
            p.append((indent, ' '.join(buf)))
            buf = []
        else:
            indent = len(line) - len(line.lstrip())
            buf.append(line.lstrip())
    if buf:
        p.append((indent, ' '.join(buf)))

    rv = []
    for indent, text in p:
        with wrapper.extra_indent(' ' * indent):
            rv.append(wrapper.fill(text))

    return '\n\n'.join(rv)


class HelpFormatter(object):
    """This class helps with formatting text based help pages.  It's
    usually just needed for very special internal cases but it's also
    exposed so that developers can write their own fancy outputs.

    At present it always writes into memory.

    :param indent_increment: the additional increment for each level.
    :param width: the width for the text.  This defaults to the terminal
                  width clamped to a maximum of 78.
    """

    def __init__(self, indent_increment=2, width=None):
        self.indent_increment = indent_increment
        if width is None:
            width = min(get_terminal_size()[0], 80) - 2
        self.width = width
        self.current_indent = 0
        self.buffer = []

    def write(self, string):
        """Writes a unicode string into the internal buffer."""
        self.buffer.append(string)

    def indent(self):
        """Increases the indentation."""
        self.current_indent += self.indent_increment

    def dedent(self):
        """Decreases the indentation."""
        self.current_indent -= self.indent_increment

    def write_usage(self, prog, args='', prefix='Usage: '):
        """Writes a usage line into the buffer.

        :param prog: the program name.
        :param args: whitespace separated list of arguments.
        :param prefix: the prefix for the first line.
        """
        prefix = '%*s%s' % (self.current_indent, prefix, prog)
        self.write(prefix)

        text_width = max(self.width - self.current_indent - len(prefix), 10)
        indent = ' ' * (len(prefix) + 1)
        self.write(wrap_text(args, text_width,
                             initial_indent=' ',
                             subsequent_indent=indent))

        self.write('\n')

    def write_heading(self, heading):
        """Writes a heading into the buffer."""
        self.write('%*s%s:\n' % (self.current_indent, '', heading))

    def write_paragraph(self):
        """Writes a paragraph into the buffer."""
        if self.buffer:
            self.write('\n')

    def write_text(self, text):
        """Writes re-indented text into the buffer.  This rewraps and
        preserves paragraphs.
        """
        text_width = max(self.width - self.current_indent, 11)
        indent = ' ' * self.current_indent
        self.write(wrap_text(text, text_width,
                             initial_indent=indent,
                             subsequent_indent=indent,
                             preserve_paragraphs=True))
        self.write('\n')

    def write_dl(self, rows, col_max=20, col_spacing=2):
        """Writes a definition list into the buffer.  This is how options
        and commands are usually formatted.

        :param rows: a list of two item tuples for the terms and values.
        :param col_max: the maximum width of the first column.
        :param col_spacing: the number of spaces between the first and
                            second column.
        """
        rows = list(rows)
        widths = measure_table(rows)
        if len(widths) != 2:
            raise TypeError('Expected two columns for definition list')

        first_col = min(widths[0], col_max) + col_spacing

        for first, second in iter_rows(rows, len(widths)):
            self.write('%*s%s' % (self.current_indent, '', first))
            if not second:
                self.write('\n')
                continue
            if len(first) <= first_col - col_spacing:
                self.write(' ' * (first_col - len(first)))
            else:
                self.write('\n')
                self.write(' ' * (first_col + self.current_indent))
            text_width = self.width - first_col - 2
            self.write(wrap_text(
                second, text_width, initial_indent='',
                subsequent_indent=' ' * (first_col + self.current_indent)))
            self.write('\n')

    @contextmanager
    def section(self, name):
        """Helpful context manager that writes a paragraph, a heading
        and the indents.

        :param name: the section name that is written as heading.
        """
        self.write_paragraph()
        self.write_heading(name)
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    @contextmanager
    def indentation(self):
        """A context manager that increases the indentation."""
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    def getvalue(self):
        """Returns the buffer contents."""
        return ''.join(self.buffer)

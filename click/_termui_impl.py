"""
    click._termui_impl
    ~~~~~~~~~~~~~~~~~~

    This module contains implementations for the termui module.  To keep the
    import time of click down some infrequently used functionality is placed
    in this module and only imported as needed.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import time
import math
from ._compat import get_text_stdout, range_type, PY2
from .utils import echo


if os.name == 'nt':
    BEFORE_BAR = '\r'
    AFTER_BAR = '\n'
else:
    BEFORE_BAR = '\r\033[?25l'
    AFTER_BAR = '\033[?25h\n'


def _length_hint(obj):
    """Returns the length hint of an object."""
    try:
        return len(obj)
    except TypeError:
        try:
            get_hint = type(obj).__length_hint__
        except AttributeError:
            return None
        try:
            hint = get_hint(obj)
        except TypeError:
            return None
        if hint is NotImplemented or \
           not isinstance(hint, (int, long)) or \
           hint < 0:
            return None
        return hint


class ProgressBar(object):

    def __init__(self, iterable, length=None, fill_char='#', empty_char=' ',
                 bar_template='%(bar)s', info_sep='  ', show_eta=True,
                 show_percent=None, show_pos=None, label=None, file=None,
                 width=30):
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.bar_template = bar_template
        self.info_sep = info_sep
        self.show_eta = show_eta
        self.show_percent = show_percent
        self.show_pos = show_pos
        self.label = label or ''
        if file is None:
            file = get_text_stdout()
        self.file = file
        self.width = width

        if length is None:
            length = _length_hint(iterable)
        if iterable is None:
            if length is None:
                raise TypeError('iterable or length is required')
            iterable = range_type(length)
        self.iter = iter(iterable)
        self.length = length
        self.length_known = length is not None
        self.pos = 0
        self.avg = []
        self.start = self.last_eta = time.time()
        self.eta_known = False
        self.finished = False
        self.max_width = None
        self.entered = False

        try:
            self.is_hidden = not self.file.isatty()
        except Exception:
            self.is_hidden = True

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.render_finish()

    def __iter__(self):
        if not self.entered:
            raise RuntimeError('You need to use progress bars in a with block.')
        self.render_progress()
        return self

    def render_finish(self):
        if self.is_hidden:
            return
        self.file.write(AFTER_BAR)
        self.file.flush()

    @property
    def pct(self):
        if self.finished:
            return 1.0
        return min(self.pos / (float(self.length) or 1), 1.0)

    @property
    def time_per_iteration(self):
        if not self.avg:
            return 0.0
        return sum(self.avg) / float(len(self.avg))

    @property
    def eta(self):
        if self.length_known and not self.finished:
            return self.time_per_iteration * (self.length - self.pos)
        return 0.0

    def format_eta(self):
        if self.eta_known:
            return time.strftime('%H:%M:%S', time.gmtime(self.eta + 1))
        return ''

    def format_pos(self):
        pos = str(self.pos)
        if self.length_known:
            pos += '/%s' % self.length
        return pos

    def format_pct(self):
        return ('% 4d%%' % int(self.pct * 100))[1:]

    def format_progress_line(self):
        show_percent = self.show_percent
        show_pos = self.show_pos

        info_bits = []
        if self.length_known:
            bar = self.fill_char * int(self.pct * self.width)
            bar += self.empty_char * (self.width - len(bar))
            if show_percent is None:
                show_percent = not show_pos
        else:
            if self.finished:
                bar = self.fill_char * self.width
            else:
                bar = list(self.empty_char * self.width)
                if self.time_per_iteration != 0:
                    bar[int((math.cos(self.pos * self.time_per_iteration)
                        / 2.0 + 0.5) * len(bar))] = self.fill_char
                bar = ''.join(bar)
            if show_pos is None:
                show_pos = True

        if show_pos:
            info_bits.append(self.format_pos())
        if show_percent:
            info_bits.append(self.format_pct())
        if self.show_eta and self.eta_known and not self.finished:
            info_bits.append(self.format_eta())

        return (self.bar_template % {
            'label': self.label,
            'bar': bar,
            'info': self.info_sep.join(info_bits)
        }).strip()

    def render_progress(self):
        if self.is_hidden:
            echo(self.label, file=self.file)
            self.file.flush()
            return

        clear_width = self.width
        if self.max_width is not None:
            clear_width = self.max_width
        self.file.write(BEFORE_BAR)
        line = self.format_progress_line()
        line_len = len(line)
        if self.max_width is None or self.max_width < line_len:
            self.max_width = line_len
        # Use echo here so that we get colorama support.
        echo(line, file=self.file, nl=False)
        self.file.write(' ' * (clear_width - line_len))
        self.file.flush()

    def make_step(self):
        self.pos += 1
        if self.length_known and self.pos >= self.length:
            self.finished = True

        if (time.time() - self.last_eta) < 1.0:
            return

        self.last_eta = time.time()
        self.avg = self.avg[-6:] + [-(self.start - time.time()) / (self.pos)]

        self.eta_known = self.length_known

    def finish(self):
        self.eta_known = 0
        self.finished = True

    def next(self):
        if self.is_hidden:
            return next(self.iter)
        try:
            rv = next(self.iter)
        except StopIteration:
            self.finish()
            self.render_progress()
            raise
        else:
            self.make_step()
            self.render_progress()
            return rv

    if not PY2:
        __next__ = next
        del next

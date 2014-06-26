"""
    click._termui_impl
    ~~~~~~~~~~~~~~~~~~

    This module contains implementations for the termui module.  To keep the
    import time of click down, some infrequently used functionality is placed
    in this module and only imported as needed.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import time
import math
from ._compat import _default_text_stdout, range_type, PY2, isatty, \
     open_stream, strip_ansi, term_len, get_best_encoding
from .utils import echo
from .exceptions import ClickException


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
                 show_percent=None, show_pos=False, item_show_func=None,
                 label=None, file=None, width=30):
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.bar_template = bar_template
        self.info_sep = info_sep
        self.show_eta = show_eta
        self.show_percent = show_percent
        self.show_pos = show_pos
        self.item_show_func = item_show_func
        self.label = label or ''
        if file is None:
            file = _default_text_stdout()
        self.file = file
        self.width = width
        self.autowidth = width == 0

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
        self.current_item = None

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

        info_bits = []
        if self.length_known:
            bar_length = int(self.pct * self.width)
            bar = self.fill_char * bar_length
            bar += self.empty_char * (self.width - bar_length)
            if show_percent is None:
                show_percent = not self.show_pos
        else:
            if self.finished:
                bar = self.fill_char * self.width
            else:
                bar = list(self.empty_char * (self.width or 1))
                if self.time_per_iteration != 0:
                    bar[int((math.cos(self.pos * self.time_per_iteration)
                        / 2.0 + 0.5) * self.width)] = self.fill_char
                bar = ''.join(bar)

        if self.show_pos:
            info_bits.append(self.format_pos())
        if show_percent:
            info_bits.append(self.format_pct())
        if self.show_eta and self.eta_known and not self.finished:
            info_bits.append(self.format_eta())
        if self.item_show_func is not None:
            item_info = self.item_show_func(self.current_item)
            if item_info is not None:
                info_bits.append(item_info)

        return (self.bar_template % {
            'label': self.label,
            'bar': bar,
            'info': self.info_sep.join(info_bits)
        }).strip()

    def render_progress(self):
        from .termui import get_terminal_size

        if self.is_hidden:
            echo(self.label, file=self.file)
            self.file.flush()
            return

        # Update width in case the terminal has been resized
        if self.autowidth:
            old_width = self.width
            self.width = 0
            clutter_length = term_len(self.format_progress_line())
            new_width = max(0, get_terminal_size()[0] - clutter_length)
            if new_width < old_width:
                self.file.write(BEFORE_BAR)
                self.file.write(' ' * self.max_width)
                self.max_width = new_width
            self.width = new_width

        clear_width = self.width
        if self.max_width is not None:
            clear_width = self.max_width

        self.file.write(BEFORE_BAR)
        line = self.format_progress_line()
        line_len = term_len(line)
        if self.max_width is None or self.max_width < line_len:
            self.max_width = line_len
        # Use echo here so that we get colorama support.
        echo(line, file=self.file, nl=False)
        self.file.write(' ' * (clear_width - line_len))
        self.file.flush()

    def make_step(self, n_steps):
        self.pos += n_steps
        if self.length_known and self.pos >= self.length:
            self.finished = True

        if (time.time() - self.last_eta) < 1.0:
            return

        self.last_eta = time.time()
        self.avg = self.avg[-6:] + [-(self.start - time.time()) / (self.pos)]

        self.eta_known = self.length_known

    def update(self, n_steps):
        self.make_step(n_steps)
        self.render_progress()

    def finish(self):
        self.eta_known = 0
        self.current_item = None
        self.finished = True

    def next(self):
        if self.is_hidden:
            return next(self.iter)
        try:
            rv = next(self.iter)
            self.current_item = rv
        except StopIteration:
            self.finish()
            self.render_progress()
            raise StopIteration()
        else:
            self.update(1)
            return rv

    if not PY2:
        __next__ = next
        del next


def pager(text, color=None):
    """Decide what method to use for paging through text."""
    stdout = _default_text_stdout()
    if not isatty(sys.stdin) or not isatty(stdout):
        return _nullpager(stdout, text, color)
    if 'PAGER' in os.environ:
        if sys.platform == 'win32':
            return _tempfilepager(text, os.environ['PAGER'], color)
        return _pipepager(text, os.environ['PAGER'], color)
    if os.environ.get('TERM') in ('dumb', 'emacs'):
        return _nullpager(stdout, text, color)
    if sys.platform == 'win32' or sys.platform.startswith('os2'):
        return _tempfilepager(text, 'more <', color)
    if hasattr(os, 'system') and os.system('(less) 2>/dev/null') == 0:
        return _pipepager(text, 'less', color)

    import tempfile
    fd, filename = tempfile.mkstemp()
    os.close(fd)
    try:
        if hasattr(os, 'system') and os.system('more "%s"' % filename) == 0:
            return _pipepager(text, 'more', color)
        return _nullpager(stdout, text, color)
    finally:
        os.unlink(filename)


def _pipepager(text, cmd, color):
    """Page through text by feeding it to another program.  Invoking a
    pager through this might support colors.
    """
    import subprocess
    env = dict(os.environ)

    # If we're piping to less we might support colors under the
    # condition that
    cmd_detail = cmd.rsplit('/', 1)[-1].split()
    if color is None and cmd_detail[0] == 'less':
        less_flags = os.environ.get('LESS', '') + ' '.join(cmd_detail[1:])
        if not less_flags:
            env['LESS'] = '-R'
            color = True
        elif 'r' in less_flags or 'R' in less_flags:
            color = True

    if not color:
        text = strip_ansi(text)

    c = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                         env=env)
    try:
        c.stdin.write(text)
        c.stdin.close()
    except IOError:
        pass
    c.wait()


def _tempfilepager(text, cmd, color):
    """Page through text by invoking a program on a temporary file."""
    import tempfile
    filename = tempfile.mktemp()
    if not color:
        text = strip_ansi(text)
    with open_stream(filename, 'w')[0] as f:
        f.write(text)
    try:
        os.system(cmd + ' "' + filename + '"')
    finally:
        os.unlink(filename)


def _nullpager(stream, text, color):
    """Simply print unformatted text.  This is the ultimate fallback."""
    if not color:
        text = strip_ansi(text)
    stream.write(text)


class Editor(object):

    def __init__(self, editor=None, env=None, require_save=True,
                 extension='.txt'):
        self.editor = editor
        self.env = env
        self.require_save = require_save
        self.extension = extension

    def get_editor(self):
        if self.editor is not None:
            return self.editor
        for key in 'VISUAL', 'EDITOR':
            rv = os.environ.get(key)
            if rv:
                return rv
        if sys.platform.startswith('win'):
            return 'notepad'
        for editor in 'vim', 'nano':
            if os.system('which %s &> /dev/null' % editor) == 0:
                return editor
        return 'vi'

    def edit_file(self, filename):
        import subprocess
        editor = self.get_editor()
        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)
        else:
            environ = None
        try:
            c = subprocess.Popen('%s "%s"' % (editor, filename),
                                 env=environ, shell=True)
            exit_code = c.wait()
            if exit_code != 0:
                raise ClickException('%s: Editing failed!' % editor)
        except OSError as e:
            raise ClickException('%s: Editing failed: %s' % (editor, e))

    def edit(self, text):
        import tempfile

        text = text or ''
        if text and not text.endswith('\n'):
            text += '\n'

        fd, name = tempfile.mkstemp(prefix='editor-', suffix=self.extension)
        try:
            if sys.platform.startswith('win'):
                encoding = 'utf-8-sig'
                text = text.replace('\n', '\r\n')
            else:
                encoding = 'utf-8'
            text = text.encode(encoding)

            f = os.fdopen(fd, 'wb')
            f.write(text)
            f.close()
            timestamp = os.path.getmtime(name)

            self.edit_file(name)

            if self.require_save \
               and os.path.getmtime(name) == timestamp:
                return None

            f = open(name, 'rb')
            try:
                rv = f.read()
            finally:
                f.close()
            return rv.decode('utf-8-sig').replace('\r\n', '\n')
        finally:
            os.unlink(name)


def open_url(url, wait=False, locate=False):
    import subprocess

    def _unquote_file(url):
        try:
            import urllib
        except ImportError:
            import urllib
        if url.startswith('file://'):
            url = urllib.unquote(url[7:])
        return url

    if sys.platform == 'darwin':
        args = ['open']
        if wait:
            args.append('-W')
        if locate:
            args.append('-R')
        args.append(_unquote_file(url))
        null = open('/dev/null', 'w')
        try:
            return subprocess.Popen(args, stderr=null).wait()
        finally:
            null.close()
    elif sys.platform.startswith('win'):
        if locate:
            url = _unquote_file(url)
            args = 'explorer /select,"%s"' % _unquote_file(
                url.replace('"', ''))
        else:
            args = 'start %s "" "%s"' % (
                wait and '/WAIT' or '', url.replace('"', ''))
        return os.system(args)

    try:
        if locate:
            url = os.path.dirname(_unquote_file(url)) or '.'
        else:
            url = _unquote_file(url)
        c = subprocess.Popen(['xdg-open', url])
        if wait:
            return c.wait()
        return 0
    except OSError:
        if url.startswith(('http://', 'https://')) and not locate and not wait:
            import webbrowser
            webbrowser.open(url)
            return 0
        return 1


def _translate_ch_to_exc(ch):
    if ch == '\x03':
        raise KeyboardInterrupt()
    if ch == '\x04':
        raise EOFError()


if sys.platform.startswith('win'):
    import msvcrt

    def getchar(echo):
        rv = msvcrt.getch()
        if echo:
            msvcrt.putchar(rv)
        _translate_ch_to_exc(rv)
        if PY2:
            enc = getattr(sys.stdin, 'encoding', None)
            if enc is not None:
                rv = rv.decode(enc, 'replace')
            else:
                rv = rv.decode('cp1252', 'replace')
        return rv
else:
    import tty
    import termios

    def getchar(echo):
        if not isatty(sys.stdin):
            f = open('/dev/tty')
            fd = f.fileno()
        else:
            fd = sys.stdin.fileno()
            f = None
        try:
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = os.read(fd, 32)
                if echo and isatty(sys.stdout):
                    sys.stdout.write(ch)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()
                if f is not None:
                    f.close()
        except termios.error:
            pass
        _translate_ch_to_exc(ch)
        return ch.decode(get_best_encoding(sys.stdin), 'replace')

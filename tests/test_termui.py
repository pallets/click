# -*- coding: utf-8 -*-
import pytest

import click
import time

import click._termui_impl
from click._compat import WIN


class FakeClock(object):
    def __init__(self):
        self.now = time.time()

    def advance_time(self, seconds=1):
        self.now += seconds

    def time(self):
        return self.now


def _create_progress(length=10, length_known=True, **kwargs):
    progress = click.progressbar(tuple(range(length)))
    for key, value in kwargs.items():
        setattr(progress, key, value)
    progress.length_known = length_known
    return progress


def test_progressbar_strip_regression(runner, monkeypatch):
    fake_clock = FakeClock()
    label = '    padded line'

    @click.command()
    def cli():
        with _create_progress(label=label) as progress:
            for thing in progress:
                fake_clock.advance_time()

    monkeypatch.setattr(time, 'time', fake_clock.time)
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    assert label in runner.invoke(cli, []).output


def test_progressbar_length_hint(runner, monkeypatch):
    class Hinted(object):
        def __init__(self, n):
            self.items = list(range(n))

        def __length_hint__(self):
            return len(self.items)

        def __iter__(self):
            return self

        def __next__(self):
            if self.items:
                return self.items.pop()
            else:
                raise StopIteration

        next = __next__

    fake_clock = FakeClock()

    @click.command()
    def cli():
        with click.progressbar(Hinted(10), label='test') as progress:
            for thing in progress:
                fake_clock.advance_time()

    monkeypatch.setattr(time, 'time', fake_clock.time)
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


def test_progressbar_hidden(runner, monkeypatch):
    fake_clock = FakeClock()
    label = 'whatever'

    @click.command()
    def cli():
        with _create_progress(label=label) as progress:
            for thing in progress:
                fake_clock.advance_time()

    monkeypatch.setattr(time, 'time', fake_clock.time)
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: False)
    assert runner.invoke(cli, []).output == ''


@pytest.mark.parametrize('avg, expected', [([], 0.0), ([1, 4], 2.5)])
def test_progressbar_time_per_iteration(runner, avg, expected):
    with _create_progress(2, avg=avg) as progress:
        assert progress.time_per_iteration == expected


@pytest.mark.parametrize('finished, expected', [(False, 5), (True, 0)])
def test_progressbar_eta(runner, finished, expected):
    with _create_progress(2, finished=finished, avg=[1, 4]) as progress:
        assert progress.eta == expected


@pytest.mark.parametrize('eta, expected',
                         [(0, '00:00:00'), (30, '00:00:30'), (90, '00:01:30'), (900, '00:15:00'),
                          (9000, '02:30:00'), (99999999999, '1157407d 09:46:39'), (None, '')])
def test_progressbar_format_eta(runner, eta, expected):
    with _create_progress(1, eta_known=eta is not None, avg=[eta]) as progress:
        assert progress.format_eta() == expected


@pytest.mark.parametrize('pos, length', [(0, 5), (-1, 1), (5, 5), (6, 5), (4, 0)])
def test_progressbar_format_pos(runner, pos, length):
    with _create_progress(length, length_known=length != 0, pos=pos) as progress:
        result = progress.format_pos()
        if progress.length_known:
            assert result == '%s/%s' % (pos, length)
        else:
            assert result == str(pos)


@pytest.mark.parametrize('length, finished, pos, avg, expected',
                         [(8, False, 7, 0, '#######-'),
                          (0, True, 8, 0, '########'),
                          (0, False, 8, 0, '--------'),
                          (0, False, 5, 3, '#-------')
                          ])
def test_progressbar_format_bar(runner, length, finished, pos, avg, expected):
    with _create_progress(length,
                          length_known=length != 0,
                          width=8,
                          pos=pos,
                          finished=finished,
                          avg=[avg]) as progress:
        assert progress.format_bar() == expected


@pytest.mark.parametrize('length, length_known, show_percent, show_pos, pos, expected',
                         [(0, True, True, True, 0, '  [--------]  0/0    0%'),
                          (0, True, False, True, 0, '  [--------]  0/0'),
                          (0, True, False, False, 0, '  [--------]'),
                          (0, False, False, False, 0, '  [--------]'),
                          (8, True, True, True, 8, '  [########]  8/8  100%')
                          ])
def test_progressbar_format_progress_line(runner, length, length_known, show_percent, show_pos, pos, expected):
    with _create_progress(length,
                          length_known,
                          width=8,
                          show_percent=show_percent,
                          pos=pos,
                          show_pos=show_pos) as progress:
        assert progress.format_progress_line() == expected


@pytest.mark.parametrize('test_item', ['test', None])
def test_progressbar_format_progress_line_with_show_func(runner, test_item):

    def item_show_func(item):
        return item

    with _create_progress(item_show_func=item_show_func, current_item=test_item) as progress:
        if test_item:
            assert progress.format_progress_line().endswith(test_item)
        else:
            assert progress.format_progress_line().endswith(progress.format_pct())


def test_progressbar_init_exceptions(runner):
    try:
        click.progressbar()
    except TypeError as e:
        assert str(e) == 'iterable or length is required'
    else:
        assert False, 'Expected an exception because unspecified arguments'


def test_progressbar_iter_outside_with_exceptions(runner):
    try:
        progress = click.progressbar(length=2)
        iter(progress)
    except RuntimeError as e:
        assert str(e) == 'You need to use progress bars in a with block.'
    else:
        assert False, 'Expected an exception because of abort-related inputs.'


def test_choices_list_in_prompt(runner, monkeypatch):
    @click.command()
    @click.option('-g', type=click.Choice(['none', 'day', 'week', 'month']),
                  prompt=True)
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option('-g', type=click.Choice(['none', 'day', 'week', 'month']),
                  prompt=True, show_choices=False)
    def cli_without_choices(g):
        pass

    result = runner.invoke(cli_with_choices, [], input='none')
    assert '(none, day, week, month)' in result.output

    result = runner.invoke(cli_without_choices, [], input='none')
    assert '(none, day, week, month)' not in result.output


def test_secho(runner):
    with runner.isolation() as outstreams:
        click.secho(None, nl=False)
        bytes = outstreams[0].getvalue()
        assert bytes == b''


def test_progressbar_yields_all_items(runner):
    with click.progressbar(range(3)) as progress:
        assert len(list(progress)) == 3


def test_progressbar_update(runner, monkeypatch):
    fake_clock = FakeClock()

    @click.command()
    def cli():
        with click.progressbar(range(4)) as progress:
            for _ in progress:
                fake_clock.advance_time()
                print("")

    monkeypatch.setattr(time, 'time', fake_clock.time)
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    output = runner.invoke(cli, []).output

    lines = [line for line in output.split('\n') if '[' in line]

    assert ' 25%  00:00:03' in lines[0]
    assert ' 50%  00:00:02' in lines[1]
    assert ' 75%  00:00:01' in lines[2]
    assert '100%          ' in lines[3]


@pytest.mark.parametrize(
    'key_char', (u'h', u'H', u'é', u'À', u' ', u'字', u'àH', u'àR')
)
@pytest.mark.parametrize('echo', [True, False])
@pytest.mark.skipif(not WIN, reason='Tests user-input using the msvcrt module.')
def test_getchar_windows(runner, monkeypatch, key_char, echo):
    monkeypatch.setattr(click._termui_impl.msvcrt, 'getwche', lambda: key_char)
    monkeypatch.setattr(click._termui_impl.msvcrt, 'getwch', lambda: key_char)
    monkeypatch.setattr(click.termui, '_getchar', None)
    assert click.getchar(echo) == key_char


@pytest.mark.parametrize('special_key_char, key_char', [(u'\x00', 'a'), (u'\x00', 'b'), (u'\xe0', 'c')])
@pytest.mark.skipif(not WIN, reason='Tests special character inputs using the msvcrt module.')
def test_getchar_special_key_windows(runner, monkeypatch, special_key_char, key_char):
    ordered_inputs = [key_char, special_key_char]
    monkeypatch.setattr(click._termui_impl.msvcrt, 'getwch', lambda: ordered_inputs.pop())
    monkeypatch.setattr(click.termui, '_getchar', None)
    assert click.getchar() == special_key_char + key_char


@pytest.mark.parametrize('key_char', [u'\x03', u'\x1a'])
@pytest.mark.skipif(not WIN, reason='Tests user-input using the msvcrt module.')
def test_getchar_windows_exceptions(runner, monkeypatch, key_char):
    monkeypatch.setattr(click._termui_impl.msvcrt, 'getwch', lambda: key_char)
    monkeypatch.setattr(click.termui, '_getchar', None)
    try:
        click.getchar()
    except KeyboardInterrupt:
        assert key_char == u'\x03'
    except EOFError:
        assert key_char == u'\x1a'
    else:
        assert False, 'Expected an exception because of abort-specific inputs.'

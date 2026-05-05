import time

import pytest

import click
import click._termui_impl


class FakeClock:
    def __init__(self):
        self.now = time.time()

    def advance_time(self, seconds=1):
        self.now += seconds

    def time(self):
        return self.now


def _create_progress(length=10, **kwargs):
    progress = click.progressbar(tuple(range(length)))
    for key, value in kwargs.items():
        setattr(progress, key, value)
    return progress


def test_progressbar_strip_regression(runner, monkeypatch):
    label = "    padded line"

    @click.command()
    def cli():
        with _create_progress(label=label) as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    assert (
        label
        in runner.invoke(cli, [], standalone_mode=False, catch_exceptions=False).output
    )


def test_progressbar_length_hint(runner, monkeypatch):
    class Hinted:
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

    @click.command()
    def cli():
        with click.progressbar(Hinted(10), label="test") as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


def test_progressbar_no_tty(runner, monkeypatch):
    @click.command()
    def cli():
        with _create_progress(label="working") as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: False)
    assert runner.invoke(cli, []).output == "working\n"


def test_progressbar_hidden_manual(runner, monkeypatch):
    @click.command()
    def cli():
        with _create_progress(label="see nothing", hidden=True) as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    assert runner.invoke(cli, []).output == ""


@pytest.mark.parametrize("avg, expected", [([], 0.0), ([1, 4], 2.5)])
def test_progressbar_time_per_iteration(runner, avg, expected):
    with _create_progress(2, avg=avg) as progress:
        assert progress.time_per_iteration == expected


@pytest.mark.parametrize("finished, expected", [(False, 5), (True, 0)])
def test_progressbar_eta(runner, finished, expected):
    with _create_progress(2, finished=finished, avg=[1, 4]) as progress:
        assert progress.eta == expected


@pytest.mark.parametrize(
    "eta, expected",
    [
        (0, "00:00:00"),
        (30, "00:00:30"),
        (90, "00:01:30"),
        (900, "00:15:00"),
        (9000, "02:30:00"),
        (99999999999, "1157407d 09:46:39"),
        (None, ""),
    ],
)
def test_progressbar_format_eta(runner, eta, expected):
    with _create_progress(1, eta_known=eta is not None, avg=[eta]) as progress:
        assert progress.format_eta() == expected


@pytest.mark.parametrize("pos, length", [(0, 5), (-1, 1), (5, 5), (6, 5), (4, 0)])
def test_progressbar_format_pos(runner, pos, length):
    with _create_progress(length, pos=pos) as progress:
        result = progress.format_pos()
        assert result == f"{pos}/{length}"


@pytest.mark.parametrize(
    "length, finished, pos, avg, expected",
    [
        (8, False, 7, 0, "#######-"),
        (0, True, 8, 0, "########"),
    ],
)
def test_progressbar_format_bar(runner, length, finished, pos, avg, expected):
    with _create_progress(
        length, width=8, pos=pos, finished=finished, avg=[avg]
    ) as progress:
        assert progress.format_bar() == expected


@pytest.mark.parametrize(
    "length, show_percent, show_pos, pos, expected",
    [
        (0, True, True, 0, "  [--------]  0/0    0%"),
        (0, False, True, 0, "  [--------]  0/0"),
        (0, False, False, 0, "  [--------]"),
        (0, False, False, 0, "  [--------]"),
        (8, True, True, 8, "  [########]  8/8  100%"),
    ],
)
def test_progressbar_format_progress_line(
    runner, length, show_percent, show_pos, pos, expected
):
    with _create_progress(
        length,
        width=8,
        show_percent=show_percent,
        pos=pos,
        show_pos=show_pos,
    ) as progress:
        assert progress.format_progress_line() == expected


@pytest.mark.parametrize("test_item", ["test", None])
def test_progressbar_format_progress_line_with_show_func(runner, test_item):
    def item_show_func(item):
        return item

    with _create_progress(
        item_show_func=item_show_func, current_item=test_item
    ) as progress:
        if test_item:
            assert progress.format_progress_line().endswith(test_item)
        else:
            assert progress.format_progress_line().endswith(progress.format_pct())


def test_progressbar_init_exceptions(runner):
    with pytest.raises(TypeError, match="iterable or length is required"):
        click.progressbar()


def test_progressbar_iter_outside_with_exceptions(runner):
    progress = click.progressbar(length=2)

    with pytest.raises(RuntimeError, match="with block"):
        iter(progress)


def test_progressbar_is_iterator(runner, monkeypatch):
    @click.command()
    def cli():
        with click.progressbar(range(10), label="test") as progress:
            while True:
                try:
                    next(progress)
                except StopIteration:
                    break

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


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

    monkeypatch.setattr(time, "time", fake_clock.time)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    output = runner.invoke(cli, []).output

    lines = [line for line in output.split("\n") if "[" in line]

    assert "  0%" in lines[0]
    assert " 25%  00:00:03" in lines[1]
    assert " 50%  00:00:02" in lines[2]
    assert " 75%  00:00:01" in lines[3]
    assert "100%          " in lines[4]


def test_progressbar_item_show_func(runner, monkeypatch):
    """item_show_func should show the current item being yielded."""

    @click.command()
    def cli():
        with click.progressbar(range(3), item_show_func=lambda x: str(x)) as progress:
            for item in progress:
                click.echo(f" item {item}")

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    lines = runner.invoke(cli).output.splitlines()

    for i, line in enumerate(x for x in lines if "item" in x):
        assert f"{i}    item {i}" in line


def test_progressbar_update_with_item_show_func(runner, monkeypatch):
    @click.command()
    def cli():
        with click.progressbar(
            length=6, item_show_func=lambda x: f"Custom {x}"
        ) as progress:
            while not progress.finished:
                progress.update(2, progress.pos)
                click.echo()

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    output = runner.invoke(cli, []).output

    lines = [line for line in output.split("\n") if "[" in line]

    assert "Custom 0" in lines[0]
    assert "Custom 2" in lines[1]
    assert "Custom 4" in lines[2]


def test_progress_bar_update_min_steps(runner):
    bar = _create_progress(update_min_steps=5)
    bar.update(3)
    assert bar._completed_intervals == 3
    assert bar.pos == 0
    bar.update(2)
    assert bar._completed_intervals == 0
    assert bar.pos == 5

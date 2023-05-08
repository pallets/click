import platform
import time

import pytest

import click._termui_impl
from click._compat import WIN


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


def test_progressbar_hidden(runner, monkeypatch):
    @click.command()
    def cli():
        with _create_progress(label="working") as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: False)
    assert runner.invoke(cli, []).output == "working\n"


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


def test_choices_list_in_prompt(runner, monkeypatch):
    @click.command()
    @click.option(
        "-g", type=click.Choice(["none", "day", "week", "month"]), prompt=True
    )
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option(
        "-g",
        type=click.Choice(["none", "day", "week", "month"]),
        prompt=True,
        show_choices=False,
    )
    def cli_without_choices(g):
        pass

    result = runner.invoke(cli_with_choices, [], input="none")
    assert "(none, day, week, month)" in result.output

    result = runner.invoke(cli_without_choices, [], input="none")
    assert "(none, day, week, month)" not in result.output


@pytest.mark.parametrize(
    "file_kwargs", [{"mode": "rt"}, {"mode": "rb"}, {"lazy": True}]
)
def test_file_prompt_default_format(runner, file_kwargs):
    @click.command()
    @click.option("-f", default=__file__, prompt="file", type=click.File(**file_kwargs))
    def cli(f):
        click.echo(f.name)

    result = runner.invoke(cli)
    assert result.output == f"file [{__file__}]: \n{__file__}\n"


def test_secho(runner):
    with runner.isolation() as outstreams:
        click.secho(None, nl=False)
        bytes = outstreams[0].getvalue()
        assert bytes == b""


@pytest.mark.skipif(platform.system() == "Windows", reason="No style on Windows.")
@pytest.mark.parametrize(
    ("value", "expect"), [(123, b"\x1b[45m123\x1b[0m"), (b"test", b"test")]
)
def test_secho_non_text(runner, value, expect):
    with runner.isolation() as (out, _):
        click.secho(value, nl=False, color=True, bg="magenta")
        result = out.getvalue()
        assert result == expect


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


@pytest.mark.parametrize("key_char", ("h", "H", "é", "À", " ", "字", "àH", "àR"))
@pytest.mark.parametrize("echo", [True, False])
@pytest.mark.skipif(not WIN, reason="Tests user-input using the msvcrt module.")
def test_getchar_windows(runner, monkeypatch, key_char, echo):
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwche", lambda: key_char)
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwch", lambda: key_char)
    monkeypatch.setattr(click.termui, "_getchar", None)
    assert click.getchar(echo) == key_char


@pytest.mark.parametrize(
    "special_key_char, key_char", [("\x00", "a"), ("\x00", "b"), ("\xe0", "c")]
)
@pytest.mark.skipif(
    not WIN, reason="Tests special character inputs using the msvcrt module."
)
def test_getchar_special_key_windows(runner, monkeypatch, special_key_char, key_char):
    ordered_inputs = [key_char, special_key_char]
    monkeypatch.setattr(
        click._termui_impl.msvcrt, "getwch", lambda: ordered_inputs.pop()
    )
    monkeypatch.setattr(click.termui, "_getchar", None)
    assert click.getchar() == f"{special_key_char}{key_char}"


@pytest.mark.parametrize(
    ("key_char", "exc"), [("\x03", KeyboardInterrupt), ("\x1a", EOFError)]
)
@pytest.mark.skipif(not WIN, reason="Tests user-input using the msvcrt module.")
def test_getchar_windows_exceptions(runner, monkeypatch, key_char, exc):
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwch", lambda: key_char)
    monkeypatch.setattr(click.termui, "_getchar", None)

    with pytest.raises(exc):
        click.getchar()


@pytest.mark.skipif(platform.system() == "Windows", reason="No sed on Windows.")
def test_fast_edit(runner):
    result = click.edit("a\nb", editor="sed -i~ 's/$/Test/'")
    assert result == "aTest\nbTest\n"


@pytest.mark.parametrize(
    ("prompt_required", "required", "args", "expect"),
    [
        (True, False, None, "prompt"),
        (True, False, ["-v"], "Option '-v' requires an argument."),
        (False, True, None, "prompt"),
        (False, True, ["-v"], "prompt"),
    ],
)
def test_prompt_required_with_required(runner, prompt_required, required, args, expect):
    @click.command()
    @click.option("-v", prompt=True, prompt_required=prompt_required, required=required)
    def cli(v):
        click.echo(str(v))

    result = runner.invoke(cli, args, input="prompt")
    assert expect in result.output


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        # Flag not passed, don't prompt.
        pytest.param(None, None, id="no flag"),
        # Flag and value passed, don't prompt.
        pytest.param(["-v", "value"], "value", id="short sep value"),
        pytest.param(["--value", "value"], "value", id="long sep value"),
        pytest.param(["-vvalue"], "value", id="short join value"),
        pytest.param(["--value=value"], "value", id="long join value"),
        # Flag without value passed, prompt.
        pytest.param(["-v"], "prompt", id="short no value"),
        pytest.param(["--value"], "prompt", id="long no value"),
        # Don't use next option flag as value.
        pytest.param(["-v", "-o", "42"], ("prompt", "42"), id="no value opt"),
    ],
)
def test_prompt_required_false(runner, args, expect):
    @click.command()
    @click.option("-v", "--value", prompt=True, prompt_required=False)
    @click.option("-o")
    def cli(value, o):
        if o is not None:
            return value, o

        return value

    result = runner.invoke(cli, args=args, input="prompt", standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


@pytest.mark.parametrize(
    ("prompt", "input", "default", "expect"),
    [
        (True, "password\npassword", None, "password"),
        ("Confirm Password", "password\npassword\n", None, "password"),
        (True, "", "", ""),
        (False, None, None, None),
    ],
)
def test_confirmation_prompt(runner, prompt, input, default, expect):
    @click.command()
    @click.option(
        "--password",
        prompt=prompt,
        hide_input=True,
        default=default,
        confirmation_prompt=prompt,
    )
    def cli(password):
        return password

    result = runner.invoke(cli, input=input, standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect

    if prompt == "Confirm Password":
        assert "Confirm Password: " in result.output


def test_false_show_default_cause_no_default_display_in_prompt(runner):
    @click.command()
    @click.option("--arg1", show_default=False, prompt=True, default="my-default-value")
    def cmd(arg1):
        pass

    # Confirm that the default value is not included in the output when `show_default`
    # is False
    result = runner.invoke(cmd, input="my-input", standalone_mode=False)
    assert "my-default-value" not in result.output

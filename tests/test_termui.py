import contextlib
import io
import platform
import shlex
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

import pytest

import click
import click._termui_impl
from click._compat import WIN
from click._termui_impl import Editor
from click._utils import UNSET
from click.exceptions import BadParameter
from click.exceptions import MissingParameter


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

    result = runner.invoke(cli, input="\n")
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
    with runner.isolation() as (out, _, _):
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


@pytest.mark.skipif(platform.system() == "Windows", reason="No sed on Windows.")
def test_edit(runner):
    with tempfile.NamedTemporaryFile(mode="w") as named_tempfile:
        named_tempfile.write("a\nb\n")
        named_tempfile.flush()

        result = click.edit(filename=named_tempfile.name, editor="sed -i~ 's/$/Test/'")
        assert result is None

        # We need to reopen the file as it becomes unreadable after the edit.
        with open(named_tempfile.name) as reopened_file:
            # POSIX says that when sed writes a pattern space to output then it
            # is immediately followed by a newline and so the expected result
            # should contain the newline.  However, some sed implementations
            # (e.g. GNU sed) does not terminate the last line in the output
            # with the newline in a case the input data missed newline at the
            # end of last line.  Hence the input data (see above) should be
            # terminated by newline too.
            assert reopened_file.read() == "aTest\nbTest\n"


@pytest.mark.parametrize(
    ("editor_cmd", "filenames", "expected_args"),
    [
        pytest.param(
            "myeditor --wait --flag",
            ["file1.txt", "file2.txt"],
            ["myeditor", "--wait", "--flag", "file1.txt", "file2.txt"],
            id="editor with args",
        ),
        pytest.param(
            "vi",
            ['file"; rm -rf / ; echo "'],
            ["vi", 'file"; rm -rf / ; echo "'],
            id="shell metacharacters in filename",
        ),
        # Issue #1026: editor path with spaces must be quoted.
        pytest.param(
            '"C:\\Program Files\\Sublime Text 3\\sublime_text.exe"',
            ["f.txt"],
            ["C:\\Program Files\\Sublime Text 3\\sublime_text.exe", "f.txt"],
            id="quoted windows path with spaces",
        ),
        # PR #1477: pager/editor command with flags, like ``less -FRSX``.
        pytest.param(
            "less -FRSX",
            ["f.txt"],
            ["less", "-FRSX", "f.txt"],
            id="command with flags",
        ),
        # Issue #1026: quoted command with ``--wait`` flag.
        pytest.param(
            '"my command" --option value arg',
            ["f.txt"],
            ["my command", "--option", "value", "arg", "f.txt"],
            id="quoted command with args",
        ),
        # PR #1477: unquoted unix path.
        pytest.param(
            "/usr/bin/vim",
            ["f.txt"],
            ["/usr/bin/vim", "f.txt"],
            id="unix absolute path",
        ),
        # Issue #1026: macOS path with escaped space.
        pytest.param(
            "/Applications/Sublime\\ Text.app/Contents/SharedSupport/bin/subl",
            ["f.txt"],
            ["/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl", "f.txt"],
            id="escaped space in unix path",
        ),
        pytest.param(
            "  vim  ",
            ["f.txt"],
            ["vim", "f.txt"],
            id="leading and trailing whitespace",
        ),
        pytest.param(
            "vim\tf.txt",
            [],
            ["vim", "f.txt"],
            id="tab-separated tokens",
        ),
        pytest.param(
            "'/Applications/My Editor.app/Contents/MacOS/editor'",
            ["f.txt"],
            ["/Applications/My Editor.app/Contents/MacOS/editor", "f.txt"],
            id="single-quoted path with spaces",
        ),
        pytest.param(
            '"my editor" --wait --new-window',
            ["file 1.txt", "file 2.txt"],
            ["my editor", "--wait", "--new-window", "file 1.txt", "file 2.txt"],
            id="quoted editor with multiple flags and filenames with spaces",
        ),
        pytest.param(
            "vim -u NONE -N",
            ["f.txt"],
            ["vim", "-u", "NONE", "-N", "f.txt"],
            id="multiple short flags",
        ),
        pytest.param(
            "editor",
            ['file"name.txt'],
            ["editor", 'file"name.txt'],
            id="filename with double quote",
        ),
        pytest.param(
            "editor",
            ["file'name.txt"],
            ["editor", "file'name.txt"],
            id="filename with single quote",
        ),
    ],
)
def test_editor_path_normalization(editor_cmd, filenames, expected_args):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor=editor_cmd).edit_files(filenames)

        mock_popen.assert_called_once()
        args = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        assert args == expected_args
        assert mock_popen.call_args[1].get("shell") is None


@pytest.mark.skipif(not WIN, reason="Windows-specific editor paths")
@pytest.mark.parametrize(
    ("editor_cmd", "expected_cmd"),
    [
        pytest.param(
            "notepad",
            ["notepad"],
            id="plain notepad",
        ),
        pytest.param(
            '"C:\\Program Files\\Sublime Text 3\\sublime_text.exe" --wait',
            ["C:\\Program Files\\Sublime Text 3\\sublime_text.exe", "--wait"],
            id="quoted path with flag",
        ),
    ],
)
def test_editor_windows_path_normalization(editor_cmd, expected_cmd):
    """Windows-specific tests: verify ``Popen`` receives unquoted paths that
    ``subprocess.list2cmdline`` can re-quote for ``CreateProcess``."""
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor=editor_cmd).edit_files(["f.txt"])

        args = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        assert args == expected_cmd + ["f.txt"]
        assert mock_popen.call_args[1].get("shell") is None


def test_editor_env_passed_through():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor="vi", env={"MY_VAR": "1"}).edit_files(["f.txt"])

        env = mock_popen.call_args[1].get("env")
        assert env is not None
        assert env["MY_VAR"] == "1"


def test_editor_failure_exception():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 1
        with pytest.raises(click.ClickException, match="Editing failed"):
            Editor(editor="vi").edit_files(["f.txt"])


def test_editor_nonexistent_exception():
    with patch("subprocess.Popen", side_effect=OSError("not found")):
        with pytest.raises(click.ClickException, match="not found"):
            Editor(editor="nonexistent").edit_files(["f.txt"])


@pytest.mark.parametrize(
    ("pager_env", "expected_parts"),
    [
        # Simple commands.
        pytest.param("cat", ["cat"], id="simple command"),
        pytest.param("less", ["less"], id="less"),
        pytest.param("less -FRSX", ["less", "-FRSX"], id="command with flags"),
        # Whitespace handling.
        pytest.param("", [], id="empty string"),
        pytest.param("   ", [], id="whitespace only"),
        pytest.param("  less  ", ["less"], id="leading and trailing spaces"),
        pytest.param("less\t-R", ["less", "-R"], id="tab as separator"),
        # Quoted Windows paths: quotes are stripped in POSIX mode (the
        # default), preserving backslashes inside quoted tokens (issue #1026).
        pytest.param(
            '"C:\\Program Files\\Git\\usr\\bin\\less.exe"',
            ["C:\\Program Files\\Git\\usr\\bin\\less.exe"],
            id="quoted windows path with spaces",
        ),
        pytest.param(
            '"C:\\Program Files\\Git\\usr\\bin\\less.exe" -R',
            ["C:\\Program Files\\Git\\usr\\bin\\less.exe", "-R"],
            id="quoted windows path with flag",
        ),
        # Single-quoted path.
        pytest.param(
            "'/usr/local/bin/my pager'",
            ["/usr/local/bin/my pager"],
            id="single-quoted path with spaces",
        ),
        # Unix paths.
        pytest.param("/usr/bin/less", ["/usr/bin/less"], id="unix absolute path"),
        pytest.param(
            "/usr/bin/my\\ pager",
            ["/usr/bin/my pager"],
            id="escaped space in unix path",
        ),
        # PR #1477: POSIX mode (the default) eats unquoted backslashes.
        # On Windows, users must quote paths that contain backslashes.
        pytest.param(
            "C:\\path\\to\\exe /test other\\path",
            ["C:pathtoexe", "/test", "otherpath"],
            id="unquoted backslashes eaten in POSIX mode",
        ),
    ],
)
def test_pager_shlex_split(pager_env, expected_parts):
    """Verify shlex.split produces the expected argv for PAGER values.

    Tests the splitting logic used by :func:`click._termui_impl.pager` to
    turn the ``PAGER`` environment variable into an ``argv`` list. See
    issue #1026, PR #1477, PR #1543, PR #2775.
    """
    assert shlex.split(pager_env) == expected_parts


def _get_real_pager_command() -> str:
    """Return a platform pager used to exercise the BinaryIO pager branch."""
    pager_name = "more" if WIN else "cat"
    pager_path = shutil.which(pager_name)
    assert pager_path is not None, f"{pager_name} not available"
    return pager_path


def _run_get_pager_file_with_real_pager(monkeypatch, capfd, writer, color=False):
    """Run through the pipe pager backend selected by ``PAGER``."""
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setitem(
        click._termui_impl.os.environ, "PAGER", _get_real_pager_command()
    )

    with click.get_pager_file(color=color) as pager:
        writer(pager)

    # The real pager writes to the process stdout; stderr should stay quiet.
    out, err = capfd.readouterr()
    assert err == ""
    return out


def _write_pager_from_multiple_sites(pager):
    pager.write("prefix\n")
    click.echo("middle", file=pager)
    pager.write("suffix\n")


@pytest.mark.parametrize(
    ("writer", "color", "expected"),
    [
        pytest.param(
            _write_pager_from_multiple_sites,
            False,
            "prefix\nmiddle\nsuffix\n",
            id="multiple write sites",
        ),
        pytest.param(
            lambda pager: pager.write("hello\n"), False, "hello\n", id="plain text"
        ),
        pytest.param(
            lambda pager: pager.write(click.style("hello", fg="red") + "\n"),
            False,
            "hello\n",
            id="strip ansi",
        ),
        pytest.param(
            lambda pager: pager.write(click.style("hello", fg="red") + "\n"),
            True,
            click.style("hello", fg="red") + "\n",
            id="preserve ansi",
        ),
        pytest.param(lambda pager: pager.write(""), False, "", id="empty string"),
    ],
)
def test_get_pager_file_with_real_pager_binary_stream(
    monkeypatch, capfd, writer, color, expected
):
    """A real pager should exercise the BinaryIO branch on Unix and Windows."""
    output = _run_get_pager_file_with_real_pager(
        monkeypatch, capfd, writer, color=color
    )

    assert output == expected


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        pytest.param(False, "hello\n", id="strip ansi"),
        pytest.param(True, click.style("hello", fg="red") + "\n", id="preserve ansi"),
    ],
)
def test_echo_via_pager_real_pager_handles_ansi(monkeypatch, capfd, color, expected):
    """``echo_via_pager`` should honor ``color`` like ``get_pager_file``."""
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setitem(
        click._termui_impl.os.environ, "PAGER", _get_real_pager_command()
    )

    click.echo_via_pager(click.style("hello", fg="red"), color=color)

    out, err = capfd.readouterr()
    assert err == ""
    assert out == expected


def test_get_pager_file_pager_missing_binary_falls_back(monkeypatch, tmp_path):
    """``PAGER`` pointing to a nonexistent binary falls back to the text stdout."""
    pager_out = tmp_path / "pager_out.txt"

    monkeypatch.setitem(
        click._termui_impl.os.environ,
        "PAGER",
        "click-tests-nonexistent-pager-9b3f2",
    )
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )

        with click.get_pager_file() as pager:
            pager.write("hello\n")

    assert pager_out.read_text(encoding="utf-8") == "hello\n"


def test_get_pager_file_pager_unset_falls_back_when_no_default(monkeypatch, tmp_path):
    """``PAGER`` unset still works when the platform default isn't installed."""
    pager_out = tmp_path / "pager_out.txt"

    monkeypatch.delitem(click._termui_impl.os.environ, "PAGER", raising=False)
    monkeypatch.delitem(click._termui_impl.os.environ, "TERM", raising=False)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setattr(shutil, "which", lambda _name: None)

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )

        with click.get_pager_file() as pager:
            pager.write("hello\n")

    assert pager_out.read_text(encoding="utf-8") == "hello\n"


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        pytest.param(False, "hello\n", id="strip ansi"),
        pytest.param(True, click.style("hello", fg="red") + "\n", id="preserve ansi"),
    ],
)
def test_get_pager_file_nullpager_wraps_textio_stream(
    monkeypatch, tmp_path, color, expected
):
    """When paging falls back to a real TextIO stream, ``.buffer`` is wrapped."""
    pager_out = tmp_path / "pager_out.txt"

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )
        monkeypatch.setattr(
            click._termui_impl, "isatty", lambda stream: stream is not sys.stdin
        )

        with click.get_pager_file(color=color) as pager:
            pager.write(click.style("hello", fg="red") + "\n")

    assert pager_out.read_text(encoding="utf-8") == expected


def test_get_pager_file_nullpager_keeps_stringio_stream(monkeypatch):
    """The no-stdout fallback should keep a text-only stream and set ``.color``."""

    created = []

    def make_stringio():
        stream = io.StringIO()
        created.append(stream)
        return stream

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(click._termui_impl, "StringIO", make_stringio)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: False)

    styled_text = click.style("hello", fg="red")

    with click.get_pager_file(color=False) as pager:
        assert pager is created[0]
        pager.write(styled_text)

    assert created[0].getvalue() == styled_text


def test_get_pager_file_flushes_stream_on_exception(monkeypatch):
    """Exceptions should still flush the yielded stream in ``finally``."""

    class FlushableTextStream(io.StringIO):
        def __init__(self):
            super().__init__()
            self.color = None
            self.flush_calls = 0

        def flush(self):
            self.flush_calls += 1

    stream = FlushableTextStream()

    @contextlib.contextmanager
    def pager_contextmanager(color=None):
        yield stream, "utf-8", color

    monkeypatch.setattr(
        click._termui_impl, "_pager_contextmanager", pager_contextmanager
    )

    with pytest.raises(RuntimeError, match="boom"):
        with click.get_pager_file() as pager:
            assert pager is stream
            raise RuntimeError("boom")

    assert stream.flush_calls == 1


def test_editor_unclosed_quote():
    """An unclosed quote in the editor command raises ValueError."""
    with pytest.raises(ValueError, match="No closing quotation"):
        Editor(editor='"unclosed').edit_files(["f.txt"])


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
        (True, "\n\n", "", ""),
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


@pytest.mark.parametrize(
    ("show_default", "default", "user_input", "in_prompt", "not_in_prompt"),
    [
        # Regular string replaces the actual default in the prompt.
        ("custom", "actual", "\n", "(custom)", "actual"),
        # String with spaces.
        ("custom label", "actual", "\n", "(custom label)", "actual"),
        # Unicode characters.
        ("∞", "0", "\n", "(∞)", None),
        # Numeric default: custom string hides the number.
        ("unlimited", 42, "\n", "(unlimited)", "42"),
        # Explicit default=None: custom string still appears, must provide input.
        ("computed at runtime", None, "value\n", "(computed at runtime)", None),
        # No default kwarg at all (internal UNSET sentinel): same as None.
        ("computed at runtime", UNSET, "value\n", "(computed at runtime)", None),
        # Empty string is falsy: suppresses any default display.
        ("", "actual", "\n", None, "actual"),
    ],
    ids=[
        "simple-string",
        "string-with-spaces",
        "unicode",
        "numeric-default",
        "default-is-none",
        "default-is-unset",
        "empty-string-is-falsy",
    ],
)
def test_string_show_default_in_prompt(
    runner, show_default, default, user_input, in_prompt, not_in_prompt
):
    """When show_default is a string, the prompt should display that
    string in parentheses instead of the actual default value,
    matching the help text behavior. See pallets/click#2836."""

    option_kwargs = {"show_default": show_default, "prompt": True}
    if default is not UNSET:
        option_kwargs["default"] = default

    @click.command()
    @click.option("--arg1", **option_kwargs)
    def cmd(arg1):
        click.echo(arg1)

    result = runner.invoke(cmd, input=user_input, standalone_mode=False)
    prompt_line = result.output.split("\n")[0]
    if in_prompt is not None:
        assert in_prompt in prompt_line
    if not_in_prompt is not None:
        assert not_in_prompt not in prompt_line


REPEAT = object()
"""Sentinel value to indicate that the prompt is expected to be repeated.

I.e. the value provided by the user is not satisfactory and need to be re-prompted.
"""

INVALID = object()
"""Sentinel value to indicate that the prompt is expected to be invalid.

On invalid input, Click will output an error message and re-prompt the user.
"""

BOOLEAN_FLAG_PROMPT_CASES = [
    ###
    ### Test cases with prompt=True explicitly enabled for the flag.
    ###
    # Prompt is allowed and the flag has no default, so it prompts.
    ({"prompt": True}, [], "[y/N]", "y", True),
    ({"prompt": True}, [], "[y/N]", "n", False),
    # Empty input default to False.
    ({"prompt": True}, [], "[y/N]", "", False),
    # Changing the default to True, makes the prompt change to [Y/n].
    ({"prompt": True, "default": True}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True}, [], "[Y/n]", "n", False),
    # False is the default's default, so it prompts with [y/N].
    ({"prompt": True, "default": False}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False}, [], "[y/N]", "n", False),
    # Defaulting to None, prompts with [y/n], which makes the user explicitly choose
    # between True or False.
    ({"prompt": True, "default": None}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None}, [], "[y/n]", "n", False),
    # Random string default is treated as a truthy value, so it prompts with [Y/n].
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "n", False),
    ###
    ### Test cases with required=True explicitly enabled for the flag.
    ###
    # A required flag just raises an error unless a default is set.
    ({"required": True}, [], None, None, MissingParameter),
    ({"required": True, "default": True}, [], None, None, True),
    ({"required": True, "default": False}, [], None, None, False),
    ({"required": True, "default": None}, [], None, None, None),
    ({"required": True, "default": "on"}, [], None, None, True),
    ({"required": True, "default": "off"}, [], None, None, False),
    ({"required": True, "default": "foo"}, [], None, None, BadParameter),
    ###
    ### Explicitly passing the flag to the CLI bypass any prompt, whatever the
    ### configuration of the flag.
    ###
    # Flag allowing a prompt.
    ({"prompt": True}, ["--flag"], None, None, True),
    ({"prompt": True}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": None}, ["--flag"], None, None, True),
    ({"prompt": True, "default": None}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": True}, ["--flag"], None, None, True),
    ({"prompt": True, "default": True}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": False}, ["--flag"], None, None, True),
    ({"prompt": True, "default": False}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": "foo"}, ["--flag"], None, None, True),
    ({"prompt": True, "default": "foo"}, ["--no-flag"], None, None, False),
    # Required flag.
    ({"required": True}, ["--flag"], None, None, True),
    ({"required": True}, ["--no-flag"], None, None, False),
    ({"required": True, "default": None}, ["--flag"], None, None, True),
    ({"required": True, "default": None}, ["--no-flag"], None, None, False),
    ({"required": True, "default": True}, ["--flag"], None, None, True),
    ({"required": True, "default": True}, ["--no-flag"], None, None, False),
    ({"required": True, "default": False}, ["--flag"], None, None, True),
    ({"required": True, "default": False}, ["--no-flag"], None, None, False),
    ({"required": True, "default": "foo"}, ["--flag"], None, None, True),
    ({"required": True, "default": "foo"}, ["--no-flag"], None, None, False),
]

FLAG_VALUE_PROMPT_CASES = [
    ###
    ### Test cases with prompt=True explicitly enabled for the flag.
    ###
    # Prompt is allowed and the flag has no default, so it prompts.
    # But the flag_value is not set, so it defaults to a string.
    ({"prompt": True}, [], "", "", REPEAT),
    ({"prompt": True}, [], "", "y", "y"),
    ({"prompt": True}, [], "", "n", "n"),
    ({"prompt": True}, [], "", "foo", "foo"),
    # This time we provide a boolean flag_value, which makes the flag behave like a
    # boolean flag, and use the appropriate variation of [y/n].
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "", False),
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "y", True),
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "n", False),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "", False),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "n", False),
    # Other flag values changes the auto-detection of the flag type.
    ({"prompt": True, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "flag_value": None}, [], "", "n", "n"),
    ({"prompt": True, "flag_value": "foo"}, [], "", "", REPEAT),
    ({"prompt": True, "flag_value": "foo"}, [], "", "y", "y"),
    ({"prompt": True, "flag_value": "foo"}, [], "", "n", "n"),
    ###
    ### Test cases with a flag_value and a default.
    ###
    # default=True
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "n", False),
    # For boolean flags, default=True is a literal value, not a sentinel meaning
    # "activate flag", so the prompt shows [Y/n] with default=True. See:
    # https://github.com/pallets/click/issues/3111
    # https://github.com/pallets/click/pull/3239
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "n", False),
    # default=False
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "n", False),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "n", False),
    # default=None
    (
        {"prompt": True, "default": None, "flag_value": True},
        [],
        "[y/n]",
        "",
        INVALID,
    ),
    ({"prompt": True, "default": None, "flag_value": True}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None, "flag_value": True}, [], "[y/n]", "n", False),
    (
        {"prompt": True, "default": None, "flag_value": False},
        [],
        "[y/n]",
        "",
        INVALID,
    ),
    ({"prompt": True, "default": None, "flag_value": False}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None, "flag_value": False}, [], "[y/n]", "n", False),
    # If the flag_value is None, the flag behave like a string flag, whatever the
    # default is.
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "n", "n"),
    (
        {"prompt": True, "default": False, "flag_value": None},
        [],
        "[False]",
        "",
        "False",
    ),
    ({"prompt": True, "default": False, "flag_value": None}, [], "[False]", "y", "y"),
    ({"prompt": True, "default": False, "flag_value": None}, [], "[False]", "n", "n"),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "n", "n"),
]


@pytest.mark.parametrize(
    ("opt_decls", "opt_params", "args", "prompt", "input", "expected"),
    # Boolean flag prompt cases.
    [("--flag/--no-flag", *case_params) for case_params in BOOLEAN_FLAG_PROMPT_CASES]
    # Non-boolean flag prompt cases.
    + [("--flag", *case_params) for case_params in FLAG_VALUE_PROMPT_CASES],
)
def test_flag_value_prompt(
    runner, opt_decls, opt_params, args, prompt, input, expected
):
    """Check how flag value are prompted and handled by all combinations of
    ``prompt``, ``default``, and ``flag_value`` parameters.

    Covers concerns raised in issue https://github.com/pallets/click/issues/1992.
    """

    @click.command()
    @click.option(opt_decls, **opt_params)
    def cli(flag):
        click.echo(repr(flag))

    invoke_options = {"standalone_mode": False}
    if input is not None:
        assert isinstance(input, str)
        invoke_options["input"] = f"{input}\n"

    result = runner.invoke(cli, args, **invoke_options)

    if expected in (MissingParameter, BadParameter):
        assert isinstance(result.exception, expected)
        assert not result.output
        assert result.exit_code == 1

    else:
        expected_output = ""
        if prompt is not None:
            # Build the expected prompt.
            assert isinstance(prompt, str)
            expected_prompt = f"Flag {prompt}: " if prompt else "Flag: "

            # Add the user input to the expected output.
            assert isinstance(input, str)
            expected_output += f"{expected_prompt}{input}\n"

            if expected is INVALID:
                expected_output += "Error: invalid input\n"

            # The prompt is expected to be repeated.
            if expected in (REPEAT, INVALID):
                expected_output += expected_prompt

        if expected not in (REPEAT, INVALID):
            expected_output += f"{expected!r}\n"

        assert result.output == expected_output
        assert not result.stderr
        assert result.exit_code == 0 if expected not in (REPEAT, INVALID) else 1


class _CustomTypeNoValue(click.ParamType):
    name = "custom"

    def convert(self, value, param, ctx):
        if len(value) < 4:
            self.fail("Password must be at least 4 characters", param, ctx)
        return value


class _CustomTypeWithRawValue(click.ParamType):
    name = "custom_raw"

    def convert(self, value, param, ctx):
        if value == "bad":
            self.fail(f"rejected: {value}", param, ctx)
        return value


class _PasswordLengthType(click.ParamType):
    """Mirrors the issue's original use case: a password validator
    that references the user-typed value in its error message without
    quoting it.
    """

    name = "password"

    def convert(self, value, param, ctx):
        if len(value) < 10:
            self.fail(f"{value} is too short", param, ctx)
        return value


class _MixedQuotedAndRawType(click.ParamType):
    """Custom type that mentions the user input both quoted (built-in
    pattern) and raw within the same message.
    """

    name = "mixed"

    def convert(self, value, param, ctx):
        self.fail(f"got {value!r} which is the same as {value}", param, ctx)


class _StaticMessageType(click.ParamType):
    """Custom type whose error message never references the value."""

    name = "static"

    def convert(self, value, param, ctx):
        self.fail("Authentication failed for this account", param, ctx)


class _RejectAllRawType(click.ParamType):
    """Always rejects, with the raw value (unquoted) in the message."""

    name = "reject_all_raw"

    def convert(self, value, param, ctx):
        self.fail(f"rejected: {value}", param, ctx)


class _MultiRawType(click.ParamType):
    """Mentions the raw value multiple times in the same message."""

    name = "multi_raw"

    def convert(self, value, param, ctx):
        self.fail(f"got {value} but {value} is bad", param, ctx)


class _MultiReprType(click.ParamType):
    """Mentions ``repr(value)`` multiple times in the same message."""

    name = "multi_repr"

    def convert(self, value, param, ctx):
        self.fail(f"got {value!r} and {value!r}", param, ctx)


class _ApostropheReprType(click.ParamType):
    """Custom type whose ``repr(value)`` switches to double quotes when
    the value itself contains a single quote.
    """

    name = "apostrophe_repr"

    def convert(self, value, param, ctx):
        self.fail(f"rejected {value!r}", param, ctx)


@pytest.mark.parametrize(
    ("type", "user_input", "expected_fragment", "unexpected_fragment"),
    [
        pytest.param(
            click.INT,
            "bad",
            "'***' is not a valid integer",
            "bad",
            id="builtin-int-masks-repr-value",
        ),
        pytest.param(
            _CustomTypeNoValue(),
            "bad",
            "Password must be at least 4 characters",
            None,
            id="custom-no-value-shows-message",
        ),
        pytest.param(
            _CustomTypeWithRawValue(),
            "bad",
            "rejected: '***'",
            "bad",
            id="custom-raw-value-masked",
        ),
        pytest.param(
            _PasswordLengthType(),
            "PASSWORD",
            "'***' is too short",
            "PASSWORD",
            id="unquoted-custom-message-should-mask-not-fallback",
        ),
        pytest.param(
            _MixedQuotedAndRawType(),
            "leakybits",
            "got '***' which is the same as '***'",
            "leakybits",
            id="mixed-quoted-and-raw-both-masked-at-source",
        ),
        pytest.param(
            click.IntRange(min=10, max=99),
            "1",
            "is not in the range",
            None,
            id="intrange-numeric-substring-falls-back-to-generic",
        ),
        pytest.param(
            _StaticMessageType(),
            "ent",
            "Authentication failed for this account",
            None,
            id="partial-word-match-falls-back-to-generic",
        ),
        # When the raw (unquoted) value appears in the message, mask it instead
        # of replacing the whole message with a generic fallback that throws
        # useful information away.
        pytest.param(
            _RejectAllRawType(),
            "secret",
            "rejected: '***'",
            "secret",
            id="raw-value-should-be-masked-not-fallback",
        ),
        # When the raw value occurs more than
        # once unquoted, every occurrence must be masked.
        pytest.param(
            _MultiRawType(),
            "secret",
            "got '***' but '***' is bad",
            "secret",
            id="multi-occurrence-raw-mask-all",
        ),
        pytest.param(
            _MultiReprType(),
            "secret",
            "got '***' and '***'",
            "secret",
            id="multi-occurrence-repr-mask-all",
        ),
        pytest.param(
            _PasswordLengthType(),
            "a.b*c+",
            "'***' is too short",
            "a.b*c+",
            id="regex-special-chars-must-be-escaped",
        ),
        pytest.param(
            _PasswordLengthType(),
            "пароль",
            "'***' is too short",
            "пароль",
            id="unicode-value-masked",
        ),
        pytest.param(
            _ApostropheReprType(),
            "it's",
            "rejected '***'",
            "it's",
            id="apostrophe-in-value-uses-double-quote-repr",
        ),
        pytest.param(
            _MixedQuotedAndRawType(),
            "leakybits",
            "got '***' which is the same as '***'",
            "leakybits",
            id="mixed-quoted-and-raw-mask-both",
        ),
    ],
)
def test_hide_input_error_message(
    runner, type, user_input, expected_fragment, unexpected_fragment
):
    """https://github.com/pallets/click/issues/2809"""

    @click.command()
    @click.option("--password", prompt=True, hide_input=True, type=type)
    def cli(password):
        click.echo(password)

    result = runner.invoke(cli, input=user_input)
    assert expected_fragment in result.output
    if unexpected_fragment is not None:
        assert unexpected_fragment not in result.output


def test_hide_input_confirmation_prompt_mismatch_unaffected(runner):
    """The ``hide_input`` mask logic only applies to ``value_proc``
    failures. The separate ``confirmation_prompt`` mismatch path must
    keep emitting its own message, with no value leak from either entry.
    """

    @click.command()
    @click.option("--password", prompt=True, confirmation_prompt=True, hide_input=True)
    def cli(password):
        click.echo(f"got: {password}")

    # First pair mismatches, second pair matches.
    result = runner.invoke(cli, input="firstone\nsecondone\nfinalone\nfinalone\n")
    assert "Error: The two entered values do not match." in result.output
    assert "firstone" not in result.output
    assert "secondone" not in result.output
    # Successful prompt echoes the final value back via the command body.
    assert "got: finalone" in result.output
    assert result.exit_code == 0


def test_hide_input_value_never_leaks_when_err_true(runner):
    """``click.prompt(..., err=True)`` routes its error message to
    stderr. The masking logic must apply on that path too: the raw
    input must not appear on either stream.
    """

    @click.command()
    def cli():
        value = click.prompt(
            "Password",
            hide_input=True,
            type=_PasswordLengthType(),
            err=True,
        )
        click.echo(value)

    result = runner.invoke(cli, input="leaky\n", mix_stderr=False)
    assert "leaky" not in result.stdout
    assert "leaky" not in result.stderr

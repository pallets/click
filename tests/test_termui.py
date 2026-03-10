import platform
import shlex
import tempfile
import time
from unittest.mock import patch

import pytest

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


@pytest.mark.parametrize(
    ("type", "expected_fragment", "unexpected_fragment"),
    [
        pytest.param(
            click.INT,
            "'***' is not a valid integer",
            "bad",
            id="builtin-int-masks-repr-value",
        ),
        pytest.param(
            _CustomTypeNoValue(),
            "Password must be at least 4 characters",
            None,
            id="custom-no-value-shows-message",
        ),
        pytest.param(
            _CustomTypeWithRawValue(),
            "The value you entered was invalid",
            "bad",
            id="custom-raw-value-falls-back-to-generic",
        ),
    ],
)
def test_hide_input_error_message(runner, type, expected_fragment, unexpected_fragment):
    """https://github.com/pallets/click/issues/2809"""

    @click.command()
    @click.option("--password", prompt=True, hide_input=True, type=type)
    def cli(password):
        click.echo(password)

    result = runner.invoke(cli, input="bad")
    assert expected_fragment in result.output
    if unexpected_fragment is not None:
        assert unexpected_fragment not in result.output

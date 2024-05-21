import os
import pathlib
import stat
import sys
from io import StringIO

import pytest

import click._termui_impl
import click.utils
from click._compat import WIN


def test_echo(runner):
    with runner.isolation() as outstreams:
        click.echo("\N{SNOWMAN}")
        click.echo(b"\x44\x44")
        click.echo(42, nl=False)
        click.echo(b"a", nl=False)
        click.echo("\x1b[31mx\x1b[39m", nl=False)
        bytes = outstreams[0].getvalue().replace(b"\r\n", b"\n")
        assert bytes == b"\xe2\x98\x83\nDD\n42ax"

    # if wrapped, we expect bytes to survive.
    @click.command()
    def cli():
        click.echo(b"\xf6")

    result = runner.invoke(cli, [])
    assert result.stdout_bytes == b"\xf6\n"

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        click.echo(bytearray(b"\x1b[31mx\x1b[39m"), nl=False)
        assert outstreams[0].getvalue() == b"\x1b[31mx\x1b[39m"


def test_echo_custom_file():
    import io

    f = io.StringIO()
    click.echo("hello", file=f)
    assert f.getvalue() == "hello\n"


def test_echo_no_streams(monkeypatch, runner):
    """echo should not fail when stdout and stderr are None with pythonw on Windows."""
    with runner.isolation():
        sys.stdout = None
        sys.stderr = None
        click.echo("test")
        click.echo("test", err=True)


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"bg": 91}, "\x1b[48;5;91mx y\x1b[0m"),
        ({"bg": (135, 0, 175)}, "\x1b[48;2;135;0;175mx y\x1b[0m"),
        ({"bold": True}, "\x1b[1mx y\x1b[0m"),
        ({"dim": True}, "\x1b[2mx y\x1b[0m"),
        ({"underline": True}, "\x1b[4mx y\x1b[0m"),
        ({"overline": True}, "\x1b[53mx y\x1b[0m"),
        ({"italic": True}, "\x1b[3mx y\x1b[0m"),
        ({"blink": True}, "\x1b[5mx y\x1b[0m"),
        ({"reverse": True}, "\x1b[7mx y\x1b[0m"),
        ({"strikethrough": True}, "\x1b[9mx y\x1b[0m"),
        ({"bold": False}, "\x1b[22mx y\x1b[0m"),
        ({"dim": False}, "\x1b[22mx y\x1b[0m"),
        ({"underline": False}, "\x1b[24mx y\x1b[0m"),
        ({"overline": False}, "\x1b[55mx y\x1b[0m"),
        ({"italic": False}, "\x1b[23mx y\x1b[0m"),
        ({"blink": False}, "\x1b[25mx y\x1b[0m"),
        ({"reverse": False}, "\x1b[27mx y\x1b[0m"),
        ({"strikethrough": False}, "\x1b[29mx y\x1b[0m"),
        ({"fg": "black", "reset": False}, "\x1b[30mx y"),
    ],
)
def test_styling(styles, ref):
    assert click.style("x y", **styles) == ref
    assert click.unstyle(ref) == "x y"


@pytest.mark.parametrize(("text", "expect"), [("\x1b[?25lx y\x1b[?25h", "x y")])
def test_unstyle_other_ansi(text, expect):
    assert click.unstyle(text) == expect


def test_filename_formatting():
    assert click.format_filename(b"foo.txt") == "foo.txt"
    assert click.format_filename(b"/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt", shorten=True) == "foo.txt"
    assert click.format_filename(b"/x/\xff.txt", shorten=True) == "�.txt"


def test_prompts(runner):
    @click.command()
    def test():
        if click.confirm("Foo"):
            click.echo("yes!")
        else:
            click.echo("no :(")

    result = runner.invoke(test, input="y\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: y\nyes!\n"

    result = runner.invoke(test, input="\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: \nno :(\n"

    result = runner.invoke(test, input="n\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: n\nno :(\n"

    @click.command()
    def test_no():
        if click.confirm("Foo", default=True):
            click.echo("yes!")
        else:
            click.echo("no :(")

    result = runner.invoke(test_no, input="y\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: y\nyes!\n"

    result = runner.invoke(test_no, input="\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: \nyes!\n"

    result = runner.invoke(test_no, input="n\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: n\nno :(\n"


def test_confirm_repeat(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--a/--no-a"], default=None, prompt=True)]
    )
    result = runner.invoke(cli, input="\ny\n")
    assert result.output == "A [y/n]: \nError: invalid input\nA [y/n]: y\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
def test_prompts_abort(monkeypatch, capsys):
    def f(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("click.termui.hidden_prompt_func", f)

    try:
        click.prompt("Password", hide_input=True)
    except click.Abort:
        click.echo("interrupted")

    out, err = capsys.readouterr()
    assert out == "Password:\ninterrupted\n"


def _test_gen_func():
    yield "a"
    yield "b"
    yield "c"
    yield "abc"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize("cat", ["cat", "cat ", "cat "])
@pytest.mark.parametrize(
    "test",
    [
        # We need lambda here, because pytest will
        # reuse the parameters, and then the generators
        # are already used and will not yield anymore
        ("just text\n", lambda: "just text"),
        ("iterable\n", lambda: ["itera", "ble"]),
        ("abcabc\n", lambda: _test_gen_func),
        ("abcabc\n", lambda: _test_gen_func()),
        ("012345\n", lambda: (c for c in range(6))),
    ],
)
def test_echo_via_pager(monkeypatch, capfd, cat, test):
    monkeypatch.setitem(os.environ, "PAGER", cat)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    expected_output = test[0]
    test_input = test[1]()

    click.echo_via_pager(test_input)

    out, err = capfd.readouterr()
    assert out == expected_output


"""
    These variables are used for the next three tests.

    _text_str is guranteeing that each color test is using the same
    string.

    _styled_text_str is running _text_str through click.style with fg
    set to red. This gurantees that each test is getting the same styled text.

    expected_stripped_text is using an fstring on _text_str to add a newline chracter
    to the end of it.

    expected_unstripped_text is using an fstring on_styled_text_str to add a newline
    character to the end of it.

    Each expected variable is what is being used in the asserts to gurantee the output
    is correct.

    The unstripped version is for when an the ANSI style should stay applied.
    The stripped version is for when the ANSI style should be removed from the text.

    These can be removed if you would rather have the parametrize values be explict
    in the following tests. The variables could also be extended and the tests truncated
    by adding isatty and jupyter_kernel variables here. Expanding the parametrize
    matrix to use those within the test instead of it being explict based on tests.
"""
_text_str = "test"
_styled_text_str = click.style(_text_str, fg="red")
expected_stripped_text = f"{_text_str}\n"
expected_unstripped_text = f"{_styled_text_str}\n"


@pytest.mark.parametrize(
    "color, text, stylized_text, expected",
    [
        (False, _text_str, _styled_text_str, expected_stripped_text),
        (True, _text_str, _styled_text_str, expected_unstripped_text),
        (None, _text_str, _styled_text_str, expected_unstripped_text),
    ],
)
def test_echo_color_flag_atty_and_not_jupyter_kernel(
    monkeypatch, capfd, color, text, stylized_text, expected
):
    """
    This is the test for echo color when the stream is a tty and
    not a jupyter kernel output.

    If color is set to False, then the text should strip the ANSI values regardless
    of operating system.

    If color is set to True, then we are forcing click to not care about
    the type of stream or operating system. This means ANSI style codes will be applied
    even if the output would not support them. Instances of this would be piping an
    echo to a file.

    If color is set to None / not set, then click will check if the stream is a tty.
    This test is forcing that to always be true, and will then mean that the output
    should keep the ANSI style.

    The mocking of _is_jupyter_kernel_output is not needed, but was added to keep it
    consistent with the other tests.
    """
    isatty = True
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)

    jupyter_kernel = False
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: jupyter_kernel
    )

    styled_text = click.style(text, fg="red")
    assert styled_text == stylized_text

    click.echo(styled_text, color=color)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "color, text, stylized_text, expected",
    [
        (False, _text_str, _styled_text_str, expected_stripped_text),
        (True, _text_str, _styled_text_str, expected_unstripped_text),
        (None, _text_str, _styled_text_str, expected_unstripped_text),
    ],
)
def test_echo_color_flag_jupyter_kernel_and_not_atty(
    monkeypatch, capfd, color, text, stylized_text, expected
):
    """
    This is the test for echo color when the stream is not a tty and
    is a jupyter kernel output.

    If color is set to False, then the text should strip the ANSI values regardless
    of operating system.

    If color is set to True, then we are forcing click to not care about
    the type of stream or operating system. This means ANSI style codes will be applied
    even if the output would not support them. Instances of this would be piping an
    echo to a file.

    If color is set to None / not set, then click will check if the stream is a tty.
    Which is being forced to be False so, the strip function will next check if
    the stream is a jupyter kernel output which is being set as True. This means
    that the ANSI style should not be stripped.
    """
    jupyter_kernel = True
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: jupyter_kernel
    )
    isatty = False
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)

    styled_text = click.style(text, fg="red")
    assert styled_text == stylized_text

    click.echo(styled_text, color=color)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "color, text, stylized_text, expected",
    [
        (False, _text_str, _styled_text_str, expected_stripped_text),
        (True, _text_str, _styled_text_str, expected_unstripped_text),
        (None, _text_str, _styled_text_str, expected_stripped_text),
    ],
)
def test_echo_color_flag_not_atty_and_not_jupyter_kernel(
    monkeypatch, capfd, color, text, stylized_text, expected
):
    """
    This is the test for echo color when the stream is not a tty nor a jupyter kernel
    output.

    If color is set to False, then the text should strip the ANSI values regardless
    of operating system.

    If color is set to True, then we are forcing click to not care about
    the type of stream or operating system. This means ANSI style codes will be applied
    even if the output would not support them. Instances of this would be piping an
    echo to a file.

    If color is set to None / not set, then click will check that the stream is neither
    a tty nor a jupyter notebook. This means the styling should be stripped regardless
    of the operating system.
    """
    isatty = False
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)
    jupyter_kernel = False
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: jupyter_kernel
    )

    styled_text = click.style(text, fg="red")
    assert styled_text == stylized_text

    click.echo(styled_text, color=color)
    out, err = capfd.readouterr()
    assert out == expected


def test_prompt_cast_default(capfd, monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO("\n"))
    value = click.prompt("value", default="100", type=int)
    capfd.readouterr()
    assert type(value) is int  # noqa E721


@pytest.mark.skipif(WIN, reason="Test too complex to make work windows.")
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        monkeypatch.setattr(sys, "stdin", StringIO(text))

    click.echo("Echo to standard output")
    out, err = capfd.readouterr()
    assert out == "Echo to standard output\n"
    assert err == ""

    click.echo("Echo to standard error", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Echo to standard error\n"

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin: "
    assert err == ""

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == " "
    assert err == "Prompt to stderr:"

    emulate_input("y\n")
    click.confirm("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin [y/N]: "
    assert err == ""

    emulate_input("y\n")
    click.confirm("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == " "
    assert err == "Prompt to stderr [y/N]:"

    monkeypatch.setattr(click.termui, "isatty", lambda x: True)
    monkeypatch.setattr(click.termui, "getchar", lambda: " ")

    click.pause("Pause to stdout")
    out, err = capfd.readouterr()
    assert out == "Pause to stdout\n"
    assert err == ""

    click.pause("Pause to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Pause to stderr\n"


def test_echo_with_capsys(capsys):
    click.echo("Capture me.")
    out, err = capsys.readouterr()
    assert out == "Capture me.\n"


def test_open_file(runner):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        with click.open_file(filename) as f:
            click.echo(f.read())

        click.echo("meep")

    with runner.isolated_filesystem():
        with open("hello.txt", "w") as f:
            f.write("Cool stuff")

        result = runner.invoke(cli, ["hello.txt"])
        assert result.exception is None
        assert result.output == "Cool stuff\nmeep\n"

        result = runner.invoke(cli, ["-"], input="foobar")
        assert result.exception is None
        assert result.output == "foobar\nmeep\n"


def test_open_file_pathlib_dash(runner):
    @click.command()
    @click.argument(
        "filename", type=click.Path(allow_dash=True, path_type=pathlib.Path)
    )
    def cli(filename):
        click.echo(str(type(filename)))

        with click.open_file(filename) as f:
            click.echo(f.read())

        result = runner.invoke(cli, ["-"], input="value")
        assert result.exception is None
        assert result.output == "pathlib.Path\nvalue\n"


def test_open_file_ignore_errors_stdin(runner):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        with click.open_file(filename, errors="ignore") as f:
            click.echo(f.read())

    result = runner.invoke(cli, ["-"], input=os.urandom(16))
    assert result.exception is None


def test_open_file_respects_ignore(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("Hello world!")

        with click.open_file("test.txt", encoding="utf8", errors="ignore") as f:
            assert f.errors == "ignore"


def test_open_file_ignore_invalid_utf8(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"\xe2\x28\xa1")

        with click.open_file("test.txt", encoding="utf8", errors="ignore") as f:
            f.read()


def test_open_file_ignore_no_encoding(runner):
    with runner.isolated_filesystem():
        with open("test.bin", "wb") as f:
            f.write(os.urandom(16))

        with click.open_file("test.bin", errors="ignore") as f:
            f.read()


@pytest.mark.skipif(WIN, reason="os.chmod() is not fully supported on Windows.")
@pytest.mark.parametrize("permissions", [0o400, 0o444, 0o600, 0o644])
def test_open_file_atomic_permissions_existing_file(runner, permissions):
    with runner.isolated_filesystem():
        with open("existing.txt", "w") as f:
            f.write("content")
        os.chmod("existing.txt", permissions)

        @click.command()
        @click.argument("filename")
        def cli(filename):
            click.open_file(filename, "w", atomic=True).close()

        result = runner.invoke(cli, ["existing.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("existing.txt").st_mode) == permissions


@pytest.mark.skipif(WIN, reason="os.stat() is not fully supported on Windows.")
def test_open_file_atomic_permissions_new_file(runner):
    with runner.isolated_filesystem():

        @click.command()
        @click.argument("filename")
        def cli(filename):
            click.open_file(filename, "w", atomic=True).close()

        # Create a test file to get the expected permissions for new files
        # according to the current umask.
        with open("test.txt", "w"):
            pass
        permissions = stat.S_IMODE(os.stat("test.txt").st_mode)

        result = runner.invoke(cli, ["new.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("new.txt").st_mode) == permissions


def test_iter_keepopenfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        for e_line, a_line in zip(expected, click.utils.KeepOpenFile(f)):
            assert e_line == a_line.strip()


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click.utils.LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf):
                assert e_line == a_line.strip()


class MockMain:
    __slots__ = "__package__"

    def __init__(self, package_name):
        self.__package__ = package_name


@pytest.mark.parametrize(
    ("path", "main", "expected"),
    [
        ("example.py", None, "example.py"),
        (str(pathlib.Path("/foo/bar/example.py")), None, "example.py"),
        ("example", None, "example"),
        (str(pathlib.Path("example/__main__.py")), "example", "python -m example"),
        (str(pathlib.Path("example/cli.py")), "example", "python -m example.cli"),
        (str(pathlib.Path("./example")), "", "example"),
    ],
)
def test_detect_program_name(path, main, expected):
    assert click.utils._detect_program_name(path, _main=MockMain(main)) == expected


def test_expand_args(monkeypatch):
    user = os.path.expanduser("~")
    assert user in click.utils._expand_args(["~"])
    monkeypatch.setenv("CLICK_TEST", "hello")
    assert "hello" in click.utils._expand_args(["$CLICK_TEST"])
    assert "pyproject.toml" in click.utils._expand_args(["*.toml"])
    assert os.path.join("docs", "conf.py") in click.utils._expand_args(["**/conf.py"])
    assert "*.not-found" in click.utils._expand_args(["*.not-found"])
    # a bad glob pattern, such as a pytest identifier, should return itself
    assert click.utils._expand_args(["test.py::test_bad"])[0] == "test.py::test_bad"


@pytest.mark.parametrize(
    ("value", "max_length", "expect"),
    [
        pytest.param("", 10, "", id="empty"),
        pytest.param("123 567 90", 10, "123 567 90", id="equal length, no dot"),
        pytest.param("123 567 9. aaaa bbb", 10, "123 567 9.", id="sentence < max"),
        pytest.param("123 567\n\n 9. aaaa bbb", 10, "123 567", id="paragraph < max"),
        pytest.param("123 567 90123.", 10, "123 567...", id="truncate"),
        pytest.param("123 5678 xxxxxx", 10, "123...", id="length includes suffix"),
        pytest.param(
            "token in ~/.netrc ciao ciao",
            20,
            "token in ~/.netrc...",
            id="ignore dot in word",
        ),
    ],
)
@pytest.mark.parametrize(
    "alter",
    [
        pytest.param(None, id=""),
        pytest.param(
            lambda text: "\n\b\n" + "  ".join(text.split(" ")) + "\n", id="no-wrap mark"
        ),
    ],
)
def test_make_default_short_help(value, max_length, alter, expect):
    assert len(expect) <= max_length

    if alter:
        value = alter(value)

    out = click.utils.make_default_short_help(value, max_length)
    assert out == expect

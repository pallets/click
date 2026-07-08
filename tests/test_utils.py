import os
import pathlib
import stat
from decimal import Decimal
from fractions import Fraction

import pytest

import click._termui_impl
import click.utils
from click._compat import WIN
from click._utils import UNSET


def test_unset_sentinel():
    value = UNSET

    assert value
    assert value is UNSET
    assert value == UNSET
    assert repr(value) == "Sentinel.UNSET"
    assert str(value) == "Sentinel.UNSET"
    assert bool(value) is True

    # Try all native Python values that can be falsy or truthy.
    # See: https://docs.python.org/3/library/stdtypes.html#truth-value-testing
    real_values = (
        None,
        True,
        False,
        0,
        1,
        0.0,
        1.0,
        0j,
        1j,
        Decimal(0),
        Decimal(1),
        Fraction(0, 1),
        Fraction(1, 1),
        "",
        "a",
        "UNSET",
        "Sentinel.UNSET",
        [1],
        (1),
        {1: "a"},
        set(),
        set([1]),
        frozenset(),
        frozenset([1]),
        range(0),
        range(1),
    )

    for real_value in real_values:
        assert value != real_value
        assert value is not real_value

    assert value not in real_values


def test_filename_formatting():
    assert click.format_filename(b"foo.txt") == "foo.txt"
    assert click.format_filename(b"/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt", shorten=True) == "foo.txt"
    assert click.format_filename("/x/\ufffd.txt", shorten=True) == "�.txt"


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
    # On non-Windows, prompt is passed directly to getpass, not echoed separately
    assert out == "\ninterrupted\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize(
    ("call", "expected_prompt"),
    [
        (lambda: click.prompt("Name"), "Name: "),
        (lambda: click.prompt("Pw", hide_input=True), "Pw: "),
        (lambda: click.prompt("IP", prompt_suffix="."), "IP."),
        (lambda: click.confirm("OK"), "OK [y/N]: "),
    ],
    ids=["prompt", "prompt-hidden", "prompt-custom-suffix", "confirm"],
)
def test_full_prompt_passed_to_readline(monkeypatch, call, expected_prompt):
    """On non-Windows, prompt and confirm pass the full prompt text to the
    underlying prompt function so readline handles editing correctly.

    https://github.com/pallets/click/issues/2968
    https://github.com/pallets/click/pull/2969
    """
    received = []

    def capture(text):
        received.append(text)
        return "y"

    monkeypatch.setattr("click.termui.visible_prompt_func", capture)
    monkeypatch.setattr("click.termui.hidden_prompt_func", capture)
    call()
    assert received == [expected_prompt]


def test_prompts_eof(runner):
    """If too few lines of input are given, prompt should exit, not hang."""

    @click.command
    def echo():
        for _ in range(3):
            click.echo(click.prompt("", type=int))

    # only provide two lines of input for three prompts
    result = runner.invoke(echo, input="1\n2\n")
    assert result.exit_code == 1


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
        for e_line, a_line in zip(expected, click.utils.KeepOpenFile(f), strict=False):
            assert e_line == a_line.strip()


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click.utils.LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf, strict=False):
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
    assert os.path.join("tests", "conftest.py") in click.utils._expand_args(
        ["**/conftest.py"]
    )
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

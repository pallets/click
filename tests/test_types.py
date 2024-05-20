import os.path
import pathlib
import platform
import tempfile

import pytest

import click
from click import FileError


@pytest.mark.parametrize(
    ("type", "value", "expect"),
    [
        (click.IntRange(0, 5), "3", 3),
        (click.IntRange(5), "5", 5),
        (click.IntRange(5), "100", 100),
        (click.IntRange(max=5), "5", 5),
        (click.IntRange(max=5), "-100", -100),
        (click.IntRange(0, clamp=True), "-1", 0),
        (click.IntRange(max=5, clamp=True), "6", 5),
        (click.IntRange(0, min_open=True, clamp=True), "0", 1),
        (click.IntRange(max=5, max_open=True, clamp=True), "5", 4),
        (click.FloatRange(0.5, 1.5), "1.2", 1.2),
        (click.FloatRange(0.5, min_open=True), "0.51", 0.51),
        (click.FloatRange(max=1.5, max_open=True), "1.49", 1.49),
        (click.FloatRange(0.5, clamp=True), "-0.0", 0.5),
        (click.FloatRange(max=1.5, clamp=True), "inf", 1.5),
    ],
)
def test_range(type, value, expect):
    assert type.convert(value, None, None) == expect


@pytest.mark.parametrize(
    ("type", "value", "expect"),
    [
        (click.IntRange(0, 5), "6", "6 is not in the range 0<=x<=5."),
        (click.IntRange(5), "4", "4 is not in the range x>=5."),
        (click.IntRange(max=5), "6", "6 is not in the range x<=5."),
        (click.IntRange(0, 5, min_open=True), 0, "0<x<=5"),
        (click.IntRange(0, 5, max_open=True), 5, "0<=x<5"),
        (click.FloatRange(0.5, min_open=True), 0.5, "x>0.5"),
        (click.FloatRange(max=1.5, max_open=True), 1.5, "x<1.5"),
    ],
)
def test_range_fail(type, value, expect):
    with pytest.raises(click.BadParameter) as exc_info:
        type.convert(value, None, None)

    assert expect in exc_info.value.message


def test_float_range_no_clamp_open():
    with pytest.raises(TypeError):
        click.FloatRange(0, 1, max_open=True, clamp=True)

    sneaky = click.FloatRange(0, 1, max_open=True)
    sneaky.clamp = True

    with pytest.raises(RuntimeError):
        sneaky.convert("1.5", None, None)


@pytest.mark.parametrize(
    ("nargs", "multiple", "default", "expect"),
    [
        (2, False, None, None),
        (2, False, (None, None), (None, None)),
        (None, True, None, ()),
        (None, True, (None, None), (None, None)),
        (2, True, None, ()),
        (2, True, [(None, None)], ((None, None),)),
        (-1, None, None, ()),
    ],
)
def test_cast_multi_default(runner, nargs, multiple, default, expect):
    if nargs == -1:
        param = click.Argument(["a"], nargs=nargs, default=default)
    else:
        param = click.Option(["-a"], nargs=nargs, multiple=multiple, default=default)

    cli = click.Command("cli", params=[param], callback=lambda a: a)
    result = runner.invoke(cli, standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


@pytest.mark.parametrize(
    ("cls", "expect"),
    [
        (None, "a/b/c.txt"),
        (str, "a/b/c.txt"),
        (bytes, b"a/b/c.txt"),
        (pathlib.Path, pathlib.Path("a", "b", "c.txt")),
    ],
)
def test_path_type(runner, cls, expect):
    cli = click.Command(
        "cli",
        params=[click.Argument(["p"], type=click.Path(path_type=cls))],
        callback=lambda p: p,
    )
    result = runner.invoke(cli, ["a/b/c.txt"], standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


def _symlinks_supported():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        target = os.path.join(tempdir, "target")
        open(target, "w").close()
        link = os.path.join(tempdir, "link")

        try:
            os.symlink(target, link)
            return True
        except OSError:
            return False


@pytest.mark.skipif(
    not _symlinks_supported(), reason="The current OS or FS doesn't support symlinks."
)
def test_path_resolve_symlink(tmp_path, runner):
    test_file = tmp_path / "file"
    test_file_str = os.fspath(test_file)
    test_file.write_text("")

    path_type = click.Path(resolve_path=True)
    param = click.Argument(["a"], type=path_type)
    ctx = click.Context(click.Command("cli", params=[param]))

    test_dir = tmp_path / "dir"
    test_dir.mkdir()

    abs_link = test_dir / "abs"
    abs_link.symlink_to(test_file)
    abs_rv = path_type.convert(os.fspath(abs_link), param, ctx)
    assert abs_rv == test_file_str

    rel_link = test_dir / "rel"
    rel_link.symlink_to(pathlib.Path("..") / "file")
    rel_rv = path_type.convert(os.fspath(rel_link), param, ctx)
    assert rel_rv == test_file_str


def _non_utf8_filenames_supported():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        try:
            f = open(os.path.join(tempdir, "\udcff"), "w")
        except OSError:
            return False

        f.close()
        return True


@pytest.mark.skipif(
    not _non_utf8_filenames_supported(),
    reason="The current OS or FS doesn't support non-UTF-8 filenames.",
)
def test_path_surrogates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    type = click.Path(exists=True)
    path = pathlib.Path("\udcff")

    with pytest.raises(click.BadParameter, match="'�' does not exist"):
        type.convert(path, None, None)

    type = click.Path(file_okay=False)
    path.touch()

    with pytest.raises(click.BadParameter, match="'�' is a file"):
        type.convert(path, None, None)

    path.unlink()
    type = click.Path(dir_okay=False)
    path.mkdir()

    with pytest.raises(click.BadParameter, match="'�' is a directory"):
        type.convert(path, None, None)

    path.rmdir()

    def no_access(*args, **kwargs):
        """Test environments may be running as root, so we have to fake the result of
        the access tests that use os.access
        """
        p = args[0]
        assert p == path, f"unexpected os.access call on file not under test: {p!r}"
        return False

    path.touch()
    type = click.Path(readable=True)

    with pytest.raises(click.BadParameter, match="'�' is not readable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    type = click.Path(readable=False, writable=True)

    with pytest.raises(click.BadParameter, match="'�' is not writable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    type = click.Path(readable=False, executable=True)

    with pytest.raises(click.BadParameter, match="'�' is not executable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    path.unlink()


@pytest.mark.parametrize(
    "type",
    [
        click.File(mode="r"),
        click.File(mode="r", lazy=True),
    ],
)
def test_file_surrogates(type, tmp_path):
    path = tmp_path / "\udcff"

    with pytest.raises(click.BadParameter, match="�': No such file or directory"):
        type.convert(path, None, None)


def test_file_error_surrogates():
    message = FileError(filename="\udcff").format_message()
    assert message == "Could not open file '�': unknown error"


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Filepath syntax differences."
)
def test_invalid_path_with_esc_sequence():
    with pytest.raises(click.BadParameter) as exc_info:
        with tempfile.TemporaryDirectory(prefix=r"my\ndir") as tempdir:
            click.Path(dir_okay=False).convert(tempdir, None, None)

    expected = "my\\\\ndir"
    assert expected in exc_info.value.message

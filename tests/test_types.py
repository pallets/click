import os.path
import pathlib

import pytest

import click
from .helpers import assert_no_surrogates
from .helpers import IMPOSSIBLE_UTF8_SURROGATE_STR
from .helpers import non_utf8_filenames_supported
from .helpers import symlinks_supported


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
    ("type", "value", "expect"),
    [
        (click.Path(resolve_path=True), "foo/bar", os.path.realpath("foo/bar")),
        (click.Path(resolve_path=True), b"foo/bar", os.path.realpath("foo/bar")),
        (
            click.Path(resolve_path=True),
            pathlib.Path("foo/bar"),
            os.path.realpath("foo/bar"),
        ),
        (click.Path(), "foo/bar", "foo/bar"),
        (click.Path(), b"foo/bar", b"foo/bar"),
        (click.Path(path_type=None), "foo/bar", "foo/bar"),
        (click.Path(path_type=None), b"foo/bar", b"foo/bar"),
        (click.Path(path_type=str), "foo/bar", "foo/bar"),
        (click.Path(path_type=str), b"foo/bar", "foo/bar"),
        (click.Path(path_type=bytes), "foo/bar", b"foo/bar"),
        (click.Path(path_type=bytes), b"foo/bar", b"foo/bar"),
        (click.Path(path_type=pathlib.Path), "foo/bar", pathlib.Path("foo/bar")),
        (click.Path(path_type=pathlib.Path), b"foo/bar", pathlib.Path("foo/bar")),
    ],
)
def test_path(type, value, expect):
    assert type.convert(value, None, None) == expect


@pytest.mark.skipif(
    not symlinks_supported, reason="The current OS or FS doesn't support symlinks."
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


@pytest.mark.skipif(
    not non_utf8_filenames_supported,
    reason="The current OS or FS doesn't support non-UTF8 filenames.",
)
def test_path_surrogates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    path = pathlib.Path(IMPOSSIBLE_UTF8_SURROGATE_STR)

    type = click.Path(exists=True)
    with pytest.raises(click.BadParameter, match="'�' does not exist") as exc_info:
        type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))

    type = click.Path(file_okay=False)
    path.touch()
    with pytest.raises(click.BadParameter, match="'�' is a file") as exc_info:
        type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))
    path.unlink()

    type = click.Path(dir_okay=False)
    path.mkdir()
    with pytest.raises(click.BadParameter, match="'�' is a directory") as exc_info:
        type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))
    path.rmdir()

    def no_access(*args, **kwargs):
        """Test environments may be running as root, so we have to fake the result of
        the access tests that use os.access
        """
        p = args[0]
        assert p == path, f"unexpected os.acess call on file not under test: {p!r}"
        return False

    path.touch()

    type = click.Path(readable=True)
    with pytest.raises(click.BadParameter, match="'�' is not readable") as exc_info:
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))

    type = click.Path(readable=False, writable=True)
    with pytest.raises(click.BadParameter, match="'�' is not writable") as exc_info:
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))

    type = click.Path(readable=False, executable=True)
    with pytest.raises(click.BadParameter, match="'�' is not executable") as exc_info:
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))

    path.unlink()


@pytest.mark.parametrize(
    "type",
    [
        click.File(mode="r"),
        click.File(mode="r", lazy=True),
        click.File(mode="rb"),
        click.File(mode="rb", lazy=True),
    ],
)
def test_file_read(type, tmp_path):
    filename = tmp_path / "foo"
    value = "Hello, world!"

    if "b" in type.mode:
        value = value.encode("utf-8")
        filename.write_bytes(value)
    else:
        filename.write_text(value)

    with type.convert(filename, None, None) as f:
        assert f.read() == value

    with type.convert(os.fsencode(filename), None, None) as f:
        assert f.read() == value

    with type.convert(str(filename), None, None) as f:
        assert f.read() == value


@pytest.mark.parametrize(
    "type",
    [
        click.File(mode="r"),
        click.File(mode="r", lazy=True),
    ],
)
def test_file_surrogates(type, tmp_path):
    path = tmp_path / f"foo{IMPOSSIBLE_UTF8_SURROGATE_STR}.mp3"
    with pytest.raises(click.BadParameter) as exc_info:
        type.convert(path, None, None)
    assert_no_surrogates(str(exc_info.value))


@pytest.mark.parametrize("mode", ["w", "wb"])
@pytest.mark.parametrize("lazy", [True, False], ids=["lazy", "eager"])
@pytest.mark.parametrize("atomic", [True, False], ids=["atomic", "non-atomic"])
def test_file_write(tmp_path, mode, lazy, atomic):
    type = click.File(mode=mode, lazy=lazy, atomic=atomic)
    value = "Hello, world!"
    read_mode = "r"

    if "b" in type.mode:
        value = value.encode("utf-8")
        read_mode = "rb"

    filename_path = tmp_path / "foo_path"
    filename_bytes = os.fsencode(tmp_path / "foo_bytes")
    filename_str = str(tmp_path / "foo_str")

    with type.convert(filename_path, None, None) as f:
        f.write(value)

    with open(filename_path, read_mode) as f:
        assert f.read() == value

    with type.convert(filename_bytes, None, None) as f:
        f.write(value)

    with open(filename_bytes, read_mode) as f:
        assert f.read() == value

    with type.convert(filename_str, None, None) as f:
        f.write(value)

    with open(filename_str, read_mode) as f:
        assert f.read() == value

import os
import pathlib
import stat

import pytest

import click
from click._compat import WIN


def _fd_is_open(fd):
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False


def _count_open_fds():
    import resource

    soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    return sum(1 for fd in range(soft) if _fd_is_open(fd))


def test_open_file(runner, tmp_path):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        with click.open_file(filename) as f:
            click.echo(f.read())

        click.echo("meep")

    hello = tmp_path / "hello.txt"
    hello.write_text("Cool stuff")

    result = runner.invoke(cli, [str(hello)])
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


def test_open_file_respects_ignore(tmp_path):
    path = tmp_path / "test.txt"
    path.write_text("Hello world!")

    with click.open_file(str(path), encoding="utf8", errors="ignore") as f:
        assert f.errors == "ignore"


def test_open_file_ignore_invalid_utf8(tmp_path):
    path = tmp_path / "test.txt"
    path.write_bytes(b"\xe2\x28\xa1")

    with click.open_file(str(path), encoding="utf8", errors="ignore") as f:
        f.read()


def test_open_file_ignore_no_encoding(tmp_path):
    path = tmp_path / "test.bin"
    path.write_bytes(os.urandom(16))

    with click.open_file(str(path), errors="ignore") as f:
        f.read()


@pytest.mark.skipif(WIN, reason="os.chmod() is not fully supported on Windows.")
@pytest.mark.parametrize("permissions", [0o400, 0o444, 0o600, 0o644])
def test_open_file_atomic_permissions_existing_file(runner, tmp_path, permissions):
    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    os.chmod(existing, permissions)

    @click.command()
    @click.argument("filename")
    def cli(filename):
        click.open_file(filename, "w", atomic=True).close()

    result = runner.invoke(cli, [str(existing)])
    assert result.exception is None
    assert stat.S_IMODE(os.stat(existing).st_mode) == permissions


@pytest.mark.skipif(WIN, reason="os.stat() is not fully supported on Windows.")
def test_open_file_atomic_permissions_new_file(runner, tmp_path):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        click.open_file(filename, "w", atomic=True).close()

    # Create a test file to get the expected permissions for new files
    # according to the current umask.
    probe = tmp_path / "test.txt"
    with open(probe, "w"):
        pass
    permissions = stat.S_IMODE(os.stat(probe).st_mode)

    new = tmp_path / "new.txt"
    result = runner.invoke(cli, [str(new)])
    assert result.exception is None
    assert stat.S_IMODE(os.stat(new).st_mode) == permissions


@pytest.mark.skipif(WIN, reason="fchmod/descriptor semantics differ on Windows.")
def test_open_file_atomic_closes_fd_when_mode_set_fails(tmp_path, monkeypatch):
    """If setting the mode on the temp file fails, the open file descriptor
    must be closed and the temp file removed (no descriptor leak)."""
    import errno

    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    os.chmod(existing, 0o644)

    def fail_fchmod(fd, mode):
        raise OSError(errno.EPERM, "fchmod denied", fd)

    monkeypatch.setattr(os, "fchmod", fail_fchmod)

    before = _count_open_fds()
    with pytest.raises(OSError):
        click.open_file(str(existing), "w", atomic=True)
    after = _count_open_fds()

    assert after == before, f"file descriptor leaked: {after - before}"
    # The temp file must be cleaned up as well.
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".__atomic-write")]


@pytest.mark.skipif(
    WIN or not hasattr(os, "fchmod"),
    reason="Test relies on fchmod being used instead of path-based chmod.",
)
def test_open_file_atomic_sets_mode_via_fd_not_path(tmp_path, monkeypatch):
    """The mode must be set on the open fd (fchmod) rather than via the temp
    path (os.chmod follows symlinks, so a concurrent replacement of the temp
    name could redirect the mode change to an unrelated file)."""
    dest = tmp_path / "dest.txt"
    dest.write_text("dest")
    os.chmod(dest, 0o600)
    victim = tmp_path / "victim.txt"
    victim.write_text("secret")
    os.chmod(victim, 0o600)

    chmod_paths = []
    real_chmod = os.chmod

    def spying_chmod(path, mode, *args, **kwargs):
        chmod_paths.append(os.fspath(path))
        return real_chmod(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "chmod", spying_chmod)

    # The atomic write must succeed (fchmod is used, so the temp path is
    # never chmod'ed)...
    f = click.open_file(str(dest), "w", atomic=True)
    f.write("new content")
    f.close()

    # ...and no path-based chmod may target the internal temp file.
    assert not [
        p for p in chmod_paths if os.path.basename(p).startswith(".__atomic-write")
    ]
    # The unrelated victim file must keep its mode regardless.
    assert stat.S_IMODE(os.stat(victim).st_mode) == 0o600
    # The destination content and preserved mode are correct.
    assert dest.read_text() == "new content"
    assert stat.S_IMODE(os.stat(dest).st_mode) == 0o600

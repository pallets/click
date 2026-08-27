import os
import pathlib
import stat

import pytest

import click
from click._compat import WIN


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

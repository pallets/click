import builtins
import os

import pytest

import click


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click.utils._LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf, strict=False):
                assert e_line == a_line.strip()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are not supported.")
def test_lazyfile_does_not_eagerly_open_fifo(tmp_path, monkeypatch):
    """Issue #2645: lazy read-mode files must not consume FIFO input early."""
    path = tmp_path / "input"
    os.mkfifo(path)

    def unexpected_open(*args, **kwargs):
        raise AssertionError("lazy FIFO setup should not open the file")

    monkeypatch.setattr(builtins, "open", unexpected_open)
    lazy_file = click.utils._LazyFile(path, "rb")

    assert lazy_file._f is None

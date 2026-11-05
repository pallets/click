import pytest

import click


@pytest.mark.parametrize(
    "type",
    [
        click.File(mode="r"),
        click.File(mode="r", lazy=True),
    ],
)
def test_file_surrogates(type, tmp_path):
    """Ensures that the error handling in ``click.File`` is robust.

    ``EILSEQ`` shows up with rootless Podman (FUSE-backed paths) and on filesystems that
    reject non-UTF-8 names, like ZFS with ``utf8only=on``.

    The test matches these errors instead of using the skip of ``test_path_surrogates``,
    which also skips macOS, where this test passes.
    """
    path = tmp_path / "\udcff"
    match = (
        # Common case: �': No such file or directory.
        r"(�': No such file or directory"
        # BSD/macOS libc special case (EILSEQ).
        r"|Illegal byte sequence"
        # glibc special case (EILSEQ).
        r"|Invalid or incomplete multibyte or wide character)"
    )
    with pytest.raises(click.BadParameter, match=match):
        type.convert(path, None, None)

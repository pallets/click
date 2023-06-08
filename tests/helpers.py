import os
import tempfile

import pytest

IMPOSSIBLE_UTF8_BYTE = b"\xff"
IMPOSSIBLE_UTF8_SURROGATE_STR = IMPOSSIBLE_UTF8_BYTE.decode("utf-8", "surrogateescape")


def _check_symlinks_supported():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        target = os.path.join(tempdir, "target")
        open(target, "w").close()
        link = os.path.join(tempdir, "link")

        try:
            os.symlink(target, link)
            return True
        except OSError:
            return False


def _check_non_utf8_filenames():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        target = os.path.join(tempdir, IMPOSSIBLE_UTF8_SURROGATE_STR)
        try:
            f = open(target, "w")
        except OSError:
            return False
        else:
            f.close()
            return True


symlinks_supported = _check_symlinks_supported()
non_utf8_filenames_supported = _check_non_utf8_filenames()


def assert_no_surrogates(value: str) -> None:
    """This fixture returns a function that can be used to assert that a string
    can be printed to a stream in which errors='strict' (e.g. stdout), i.e. has no
    surrogates.

    You *must not remove this from tests*, as many (most?) systems in which our tests
    will run are already configured with a locale which makes printing surrogates work
    fine.

    Here are some typical scenarios in which strings with surrogates wouldn't cause an
    error:

    - You're printing to stderr

      Python uses the `backslashreplace` error handler for stderr.

    - You're using the official Python docker image which sets LANG=C.UTF-8

      Since Python 3.5, the stdin and stdour error handler is `surrogateescape` when the
      `C` locale is used. Python 3.7 extends this to the `POSIX` locale (via PEP 540)
      and additionally the `C.UTF-8` and `UTF-8` locales (via PEP 538).

    - You're using a minimal Debian (e.g. a docker image) and don't have LANG/LC_* set.

      Since Python 3.7, Python will coerce your locale to `C.UTF-8` (PEP 538), and
      therefore changes the error handler for stdin and stdout to `surrogateescape`.

    - You're on a system where the locale is explicitly `C` or `POSIX`.

      As above, Python will coerce your locale to `C.UTF-8` (PEP 538).

    - You're using PEP 540's UTF-8 mode explicitly via `PYTHONUTF8=1` or `-X utf8`.

      PEP 540 changes the stdout and stdin error handlers to `surrogateescape`.

    A typical scenario in which the `strict` error handler is used for stdin and stdout
    is when you have a locale like `LANG=en_GB.UTF-8`. It is these systems where we need
    to be sure we aren't printing surrogates to stdout!
    """
    __tracebackhide__ = True
    assert isinstance(value, str), "this fixture is only for checking strings"
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        if exc.reason == "surrogates not allowed":
            pytest.fail("string contains surrogates")
        else:
            raise

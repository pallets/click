import os
import shutil
import tempfile

import pytest

from click.testing import CliRunner


@pytest.fixture(scope="function")
def runner(request):
    return CliRunner()


def check_symlink_impl():
    """This function checks if using symlinks is allowed
    on the host machine"""
    tempdir = tempfile.mkdtemp(prefix="click-")
    test_pth = os.path.join(tempdir, "check_sym_impl")
    sym_pth = os.path.join(tempdir, "link")
    open(test_pth, "w").close()
    rv = True
    try:
        os.symlink(test_pth, sym_pth)
    except (NotImplementedError, OSError):
        # Creating symlinks on Windows require elevated access.
        # OSError is thrown if the function is called without it.
        rv = False
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)
    return rv

import pytest

from click._compat import should_strip_ansi
from click._compat import WIN


@pytest.mark.xfail(WIN, reason="Jupyter not tested/supported on Windows")
def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert not should_strip_ansi(stream=JupyterKernelFakeStream())

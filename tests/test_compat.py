from click._compat import should_strip_ansi


def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert not should_strip_ansi(stream=JupyterKernelFakeStream())

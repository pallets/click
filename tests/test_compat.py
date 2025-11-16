from __future__ import annotations

import sys

import pytest

import click


def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert click._compat._is_jupyter_kernel_output(stream=JupyterKernelFakeStream())


@pytest.mark.parametrize(
    "stream",
    [None, sys.stdin, sys.stderr, sys.stdout],
)
@pytest.mark.parametrize(
    "color,expected_override",
    [
        (True, False),
        (False, True),
        (None, None),
    ],
)
@pytest.mark.parametrize(
    "isatty,is_jupyter,expected",
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
    ],
)
def test_should_strip_ansi(
    monkeypatch,
    stream,
    color: bool | None,
    expected_override: bool | None,
    isatty: bool,
    is_jupyter: bool,
    expected: bool,
) -> None:
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: is_jupyter
    )

    if expected_override is not None:
        expected = expected_override
    assert click._compat.should_strip_ansi(stream=stream, color=color) == expected

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


class _TextOnlyNoWritable:
    """A writable text stream with no native ``writable()`` method."""

    def write(self, s: str) -> int:
        if isinstance(s, (bytes, bytearray)):
            raise TypeError("expected str")
        return len(s)


class _BinaryOnlyNoWritable:
    """A writable binary stream with no native ``writable()`` method."""

    def write(self, b: bytes) -> int:
        if not isinstance(b, (bytes, bytearray)):
            raise TypeError("expected bytes")
        return len(b)


class _NotWritableNoWritable:
    def write(self, x: object) -> int:
        raise OSError("stream is closed")


@pytest.mark.parametrize(
    ("stream", "expected"),
    [
        (_TextOnlyNoWritable(), True),
        (_BinaryOnlyNoWritable(), True),
        (_NotWritableNoWritable(), False),
    ],
)
def test_fixupstream_writable_probe(stream: object, expected: bool) -> None:
    # When the wrapped stream has no native ``writable()``, ``_FixupStream``
    # probes with a binary then a text write. The text fallback must actually
    # write ``str`` (not ``bytes`` again), otherwise a text-only stream is
    # wrongly reported as not writable.
    assert click._compat._FixupStream(stream).writable() is expected


@pytest.mark.parametrize(
    "stream",
    [None, sys.stdin, sys.stderr, sys.stdout],
)
@pytest.mark.parametrize(
    ("color", "expected_override"),
    [
        (True, False),
        (False, True),
        (None, None),
    ],
)
@pytest.mark.parametrize(
    ("isatty", "is_jupyter", "expected"),
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

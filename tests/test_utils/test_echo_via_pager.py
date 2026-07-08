import os
import subprocess
import sys
from collections import namedtuple
from contextlib import nullcontext
from functools import partial
from unittest.mock import patch

import pytest

import click
from click._compat import WIN

EchoViaPagerTest = namedtuple(
    "EchoViaPagerTest",
    (
        "description",
        "test_input",
        "expected_pager",
        "expected_stdout",
        "expected_stderr",
        "expected_error",
    ),
)


def _test_gen_func():
    yield "a"
    yield "b"
    yield "c"
    yield "abc"


def _test_gen_func_fails():
    raise RuntimeError("This is a test.")
    yield  # unreachable, keeps this a generator function


def _test_gen_func_yields_then_fails():
    yield "test"
    raise RuntimeError("This is a test.")


def _test_gen_func_echo(file=None):
    yield "test"
    click.echo("hello", file=file)
    yield "test"


def _test_simulate_keyboard_interrupt(file=None):
    yield "output_before_keyboard_interrupt"
    raise KeyboardInterrupt()


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize(
    "pager_cmd", ["cat", "cat ", " cat ", "less", " less", " less "]
)
@pytest.mark.parametrize(
    "test",
    [
        # We need to pass a parameter function instead of a plain param
        # as pytest.mark.parametrize will reuse the parameters causing the
        # generators to be used up so they will not yield anymore
        EchoViaPagerTest(
            description="Plain string argument",
            test_input=lambda: "just text",
            expected_pager="just text\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Iterable argument",
            test_input=lambda: ["itera", "ble"],
            expected_pager="iterable\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Generator function argument",
            test_input=lambda: _test_gen_func,
            expected_pager="abcabc\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="String generator argument",
            test_input=lambda: _test_gen_func(),
            expected_pager="abcabc\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Number generator expression argument",
            test_input=lambda: (c for c in range(6)),
            expected_pager="012345\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Exception in generator function argument",
            test_input=lambda: _test_gen_func_fails,
            # Because generator throws early on, the pager did not have
            # a chance yet to write the file.
            expected_pager="",
            expected_stdout="",
            expected_stderr="",
            expected_error=RuntimeError,
        ),
        EchoViaPagerTest(
            description="Exception in generator argument",
            test_input=lambda: _test_gen_func_fails,
            # Because generator throws early on, the pager did not have a
            # chance yet to write the file.
            expected_pager="",
            expected_stdout="",
            expected_stderr="",
            expected_error=RuntimeError,
        ),
        EchoViaPagerTest(
            description="Keyboard interrupt should not terminate the pager",
            test_input=lambda: _test_simulate_keyboard_interrupt(),
            # Due to the keyboard interrupt during pager execution, click program
            # should abort, but the pager should stay open.
            # This allows users to cancel the program and search in the pager
            # output, before they decide to terminate the pager.
            expected_pager="output_before_keyboard_interrupt",
            expected_stdout="",
            expected_stderr="",
            expected_error=KeyboardInterrupt,
        ),
        EchoViaPagerTest(
            description="Writing to stdout during generator execution",
            test_input=lambda: _test_gen_func_echo(),
            expected_pager="testtest\n",
            expected_stdout="hello\n",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Writing to stderr during generator execution",
            test_input=lambda: _test_gen_func_echo(file=sys.stderr),
            expected_pager="testtest\n",
            expected_stdout="",
            expected_stderr="hello\n",
            expected_error=None,
        ),
    ],
)
def test_echo_via_pager(monkeypatch, capfd, pager_cmd, test, tmp_path):
    monkeypatch.setitem(os.environ, "PAGER", pager_cmd)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    test_input = test.test_input()
    expected_pager = test.expected_pager
    expected_stdout = test.expected_stdout
    expected_stderr = test.expected_stderr
    expected_error = test.expected_error

    check_raise = pytest.raises(expected_error) if expected_error else nullcontext()

    pager_out_tmp = tmp_path / "pager_out.txt"
    with pager_out_tmp.open("w") as f:
        force_subprocess_stdout = patch.object(
            subprocess,
            "Popen",
            partial(subprocess.Popen, stdout=f),
        )
        with force_subprocess_stdout:
            with check_raise:
                click.echo_via_pager(test_input)

    out, err = capfd.readouterr()

    pager = pager_out_tmp.read_text()

    assert pager == expected_pager, (
        f"Unexpected pager output in test case '{test.description}'"
    )
    assert out == expected_stdout, (
        f"Unexpected stdout in test case '{test.description}'"
    )
    assert err == expected_stderr, (
        f"Unexpected stderr in test case '{test.description}'"
    )


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
def test_echo_via_pager_yields_before_exception(monkeypatch, tmp_path):
    """A generator that yields then raises: click writes the partial output to
    the pager stream before propagating the exception.

    The pager file content is intentionally NOT asserted: pipe-drain timing
    between click and the pager subprocess is outside click's control
    (#2899, #3470). Spying on ``MaybeStripAnsi.write`` records what click sent
    to the pager, which is deterministic regardless of scheduling.
    """
    monkeypatch.setitem(os.environ, "PAGER", "cat")
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    writes: list[str] = []
    real_write = click._termui_impl.MaybeStripAnsi.write

    def spy(self, text):
        writes.append(text)
        return real_write(self, text)

    monkeypatch.setattr(click._termui_impl.MaybeStripAnsi, "write", spy)

    pager_out_tmp = tmp_path / "pager_out.txt"
    with (
        pager_out_tmp.open("w") as f,
        patch.object(subprocess, "Popen", partial(subprocess.Popen, stdout=f)),
        pytest.raises(RuntimeError, match="This is a test."),
    ):
        click.echo_via_pager(_test_gen_func_yields_then_fails())

    assert "".join(writes) == "test", (
        f"click should have written the yielded chunk before exception, got {writes!r}"
    )


@pytest.mark.stress
@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize("_", range(1000))
def test_stress_echo_via_pager_exception_cleanup(_, monkeypatch, tmp_path):
    """Repeated exceptions during ``echo_via_pager`` must not leak subprocesses.

    Regression coverage for the cleanup path in ``_pipepager``'s exception
    handler (issue #2899, PR #3470). Each iteration spawns a real pager
    subprocess, raises before any data is written and check there is no leak.
    """
    monkeypatch.setitem(os.environ, "PAGER", "cat")
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    spawned: list[subprocess.Popen] = []
    real_popen = subprocess.Popen

    def tracking_popen(*args, **kwargs):
        p = real_popen(*args, **kwargs)
        spawned.append(p)
        return p

    pager_out_tmp = tmp_path / "pager_out.txt"
    with (
        pager_out_tmp.open("w") as f,
        patch.object(subprocess, "Popen", partial(tracking_popen, stdout=f)),
        pytest.raises(RuntimeError),
    ):
        click.echo_via_pager(_test_gen_func_fails())

    assert spawned, "pager subprocess was never started"
    for p in spawned:
        assert p.returncode is not None, "pager subprocess not reaped"

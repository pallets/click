"""Tests for ``CliRunner`` stream lifecycle and ownership.

Covers the stream management bugs tracked across:
- Issue #824: ``ValueError`` on closed file when logging interacts with ``CliRunner``
- Issue #2993: Race condition in ``StreamMixer`` finalization (multi-threaded)
- Issue #3110: Regression from PR #2991's ``__del__`` fix breaking logging
- PR #3139: The fix - prevent ``_NamedTextIOWrapper`` from closing owned buffers

The tests are organized by category:

1. Stream ownership: ``_NamedTextIOWrapper`` must not close buffers it wraps
2. ``StreamMixer`` lifecycle: buffers survive wrapper garbage collection
3. Logging interaction: ``CliRunner`` works with active logging handlers
4. Multi-threaded safety: concurrent threads don't cause I/O-on-closed-file
5. Sequential invocations: multiple ``invoke()`` calls don't corrupt state
6. Stress tests (marked ``stress``): high-iteration reproducers for races

How to run locally
------------------

Standard tests (fast, ~0.8s) with stress tests excluded by default:

.. code-block:: shell-session

    $ pytest tests/test_stream_lifecycle.py -v

Stress tests only (30k iterations, ~52min):

.. code-block:: shell-session

    $ pytest tests/test_stream_lifecycle.py -m stress -x --override-ini="addopts="

Everything:

.. code-block:: shell-session

    $ pytest tests/test_stream_lifecycle.py --override-ini="addopts=" -x
"""

from __future__ import annotations

import gc
import io
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import click
from click.testing import _NamedTextIOWrapper
from click.testing import BytesIOCopy
from click.testing import CliRunner
from click.testing import StreamMixer

# ---------------------------------------------------------------------------
# Category 1: Stream ownership - ``_NamedTextIOWrapper`` must not close buffers
# ---------------------------------------------------------------------------


def test_wrapper_close_does_not_close_underlying_buffer():
    """Calling ``close()`` on the wrapper must leave the buffer open."""
    buf = io.BytesIO()
    wrapper = _NamedTextIOWrapper(buf, encoding="utf-8", name="t", mode="w")
    wrapper.write("hello")
    wrapper.flush()
    wrapper.close()
    assert not buf.closed
    assert buf.getvalue() == b"hello"


def test_wrapper_del_does_not_close_underlying_buffer():
    """Garbage-collecting the wrapper must leave the buffer open."""
    buf = io.BytesIO()
    wrapper = _NamedTextIOWrapper(buf, encoding="utf-8", name="t", mode="w")
    wrapper.write("world")
    wrapper.flush()
    del wrapper
    gc.collect()
    assert not buf.closed
    assert buf.getvalue() == b"world"


def test_multiple_wrappers_same_buffer():
    """Multiple wrappers on the same buffer can be closed independently."""
    buf = io.BytesIO()
    w1 = _NamedTextIOWrapper(buf, encoding="utf-8", name="a", mode="w")
    w2 = _NamedTextIOWrapper(buf, encoding="utf-8", name="b", mode="w")
    w1.write("one")
    w1.flush()
    w1.close()
    # buf survives, second wrapper can still write
    w2.write("two")
    w2.flush()
    w2.close()
    assert not buf.closed
    assert buf.getvalue() == b"onetwo"


def test_wrapper_preserves_name_and_mode():
    buf = io.BytesIO()
    wrapper = _NamedTextIOWrapper(buf, encoding="utf-8", name="<stdout>", mode="w")
    assert wrapper.name == "<stdout>"
    assert wrapper.mode == "w"


# ---------------------------------------------------------------------------
# Category 2: ``StreamMixer`` lifecycle
# ---------------------------------------------------------------------------


def test_mixer_buffers_survive_wrapper_gc():
    """After wrappers are garbage-collected, mixer buffers remain open."""
    mixer = StreamMixer()
    out_w = _NamedTextIOWrapper(
        mixer.stdout, encoding="utf-8", name="<stdout>", mode="w"
    )
    err_w = _NamedTextIOWrapper(
        mixer.stderr, encoding="utf-8", name="<stderr>", mode="w"
    )
    out_w.write("out")
    out_w.flush()
    err_w.write("err")
    err_w.flush()

    del out_w, err_w
    gc.collect()

    assert not mixer.stdout.closed
    assert not mixer.stderr.closed
    assert not mixer.output.closed
    assert mixer.stdout.getvalue() == b"out"
    assert mixer.stderr.getvalue() == b"err"
    assert mixer.output.getvalue() == b"outerr"


def test_getvalue_after_isolation_exit():
    """After the isolation context exits, stream values are readable."""
    runner = CliRunner()

    @click.command()
    def cli():
        click.echo("stdout-msg")
        click.echo("stderr-msg", err=True)

    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert result.stdout == "stdout-msg\n"
    assert result.stderr == "stderr-msg\n"
    assert "stdout-msg" in result.output
    assert "stderr-msg" in result.output


def test_no_streammixer_del():
    """``StreamMixer`` should not have a ``__del__`` method.

    PR #2991 added ``__del__`` which caused issue #3110. PR #3139 removes it.
    """
    has_del = hasattr(StreamMixer, "__del__")
    if has_del:
        assert StreamMixer.__del__ is object.__del__  # type: ignore[attr-defined]


def test_bytesiocopy_writes_to_both():
    """``BytesIOCopy`` writes to itself and to ``copy_to``."""
    target = io.BytesIO()
    copier = BytesIOCopy(copy_to=target)
    copier.write(b"data")
    copier.flush()
    assert copier.getvalue() == b"data"
    assert target.getvalue() == b"data"


def test_bytesiocopy_flush_propagates():
    """``BytesIOCopy.flush()`` also flushes ``copy_to``."""
    target = io.BytesIO()
    copier = BytesIOCopy(copy_to=target)
    copier.write(b"abc")
    copier.flush()
    assert target.getvalue() == b"abc"


# ---------------------------------------------------------------------------
# Category 3: Logging interaction (issues #824, #3110)
# ---------------------------------------------------------------------------


def test_invoke_with_logger_warning():
    """Basic ``logging.warning()`` inside a command must not crash."""
    logger = logging.getLogger("test_invoke_with_logger_warning")

    @click.command()
    def cli():
        logger.warning("a warning")
        click.echo("done")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "done" in result.output


def test_invoke_with_logger_and_prompt():
    """Logging + prompt (the exact #824 reproducer)."""
    logger = logging.getLogger("test_invoke_with_logger_and_prompt")

    @click.command()
    @click.option("--name", prompt="Your name")
    def hello(name):
        logger.warning("greeting %s", name)
        click.echo(f"Hello, {name}!")

    runner = CliRunner()
    result = runner.invoke(hello, input="Peter")
    assert result.exit_code == 0
    assert "Your name:" in result.output


def test_sequential_invokes_with_logging():
    """Multiple sequential ``invoke()`` calls with logging (#3110 reproducer).

    Issue #3110: the ``__del__`` from PR #2991 caused logging failures on
    the second invocation because the first ``StreamMixer``'s ``__del__`` would
    close buffers that logging still referenced.
    """
    logger = logging.getLogger("test_sequential_invokes_with_logging")

    @click.command()
    @click.argument("msg")
    def cli(msg):
        logger.warning("log: %s", msg)
        click.echo(msg)

    runner = CliRunner()
    for i in range(5):
        result = runner.invoke(cli, [f"msg-{i}"])
        assert result.exit_code == 0, f"Failed on invocation {i}: {result.exception}"
        assert f"msg-{i}" in result.output


def test_invoke_with_stream_handler_on_stderr():
    """A ``StreamHandler`` explicitly attached to stderr must survive ``invoke()``."""
    logger = logging.getLogger("test_stream_handler_stderr")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    try:

        @click.command()
        def cli():
            logger.info("message from inside invoke")
            click.echo("ok")

        runner = CliRunner()
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert "ok" in result.output
    finally:
        logger.removeHandler(handler)


def test_logging_with_cli_log_level():
    """Simulate what ``--log-cli-level`` does: add a handler to root
    before invoke.

    This reproduces the original #824 scenario without needing pytest
    CLI flags.
    """
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.WARNING)
    root_logger.addHandler(handler)
    original_level = root_logger.level
    root_logger.setLevel(logging.WARNING)
    try:

        @click.command()
        def cli():
            logging.warning("live log message")
            click.echo("output")

        runner = CliRunner()
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert "output" in result.output
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(original_level)


# ---------------------------------------------------------------------------
# Category 4: Multi-threaded safety (issue #2993)
# ---------------------------------------------------------------------------


def test_invoke_with_thread_pool():
    """Basic ``ThreadPoolExecutor`` usage inside a command."""

    @click.command()
    def cli():
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(lambda x: x * 2, i) for i in range(4)]
            results = [f.result() for f in futures]
        click.echo(f"results={results}")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "results=" in result.output


def test_invoke_with_threads_writing_to_streams():
    """Threads writing to ``click.echo()`` during invocation."""

    @click.command()
    def cli():
        barrier = threading.Barrier(3)

        def worker(n):
            barrier.wait(timeout=5)
            click.echo(f"worker-{n}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        click.echo("main-done")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "main-done" in result.output


def test_invoke_with_thread_pool_and_exit():
    """``ThreadPoolExecutor`` + ``SystemExit`` (the exact #2993 reproducer)."""

    @click.command()
    @click.argument("args", nargs=-1)
    def cli(**_kw):
        with ThreadPoolExecutor() as executor:
            executor.submit(lambda: None).result()
        raise SystemExit(1)

    runner = CliRunner()
    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 1


def test_sequential_threaded_invokes():
    """Multiple sequential invocations with threads don't leak state."""

    @click.command()
    @click.argument("n", type=int)
    def cli(n):
        with ThreadPoolExecutor(max_workers=2) as pool:
            val = pool.submit(lambda x: x + 1, n).result()
        click.echo(str(val))

    runner = CliRunner()
    for i in range(10):
        result = runner.invoke(cli, [str(i)])
        assert result.exit_code == 0
        assert result.output.strip() == str(i + 1)


# ---------------------------------------------------------------------------
# Category 5: Sequential invocations and state isolation
# ---------------------------------------------------------------------------


def test_output_isolation_across_invokes():
    """Each ``invoke()`` must capture only its own output."""

    @click.command()
    @click.argument("msg")
    def cli(msg):
        click.echo(msg)

    runner = CliRunner()
    for word in ("alpha", "beta", "gamma"):
        result = runner.invoke(cli, [word])
        assert result.exit_code == 0
        assert result.output.strip() == word


def test_stderr_isolation_across_invokes():
    """Each ``invoke()`` must capture only its own stderr."""

    @click.command()
    @click.argument("msg")
    def cli(msg):
        click.echo(msg, err=True)

    runner = CliRunner()
    for word in ("err1", "err2", "err3"):
        result = runner.invoke(cli, [word])
        assert result.exit_code == 0
        assert result.stderr.strip() == word
        assert result.stdout.strip() == ""


def test_mixed_output_order_preserved():
    """stdout/stderr interleaving is captured in order."""

    @click.command()
    def cli():
        click.echo("out1")
        click.echo("err1", err=True)
        click.echo("out2")
        click.echo("err2", err=True)

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.output == "out1\nerr1\nout2\nerr2\n"
    assert result.stdout == "out1\nout2\n"
    assert result.stderr == "err1\nerr2\n"


def test_exception_does_not_corrupt_next_invoke():
    """A failed invoke must not break subsequent invocations."""
    call_count = 0

    @click.command()
    def cli():
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("intentional")
        click.echo(f"call-{call_count}")

    runner = CliRunner()

    r1 = runner.invoke(cli)
    assert r1.exit_code == 0
    assert "call-1" in r1.output

    r2 = runner.invoke(cli)
    assert r2.exit_code == 1
    assert isinstance(r2.exception, RuntimeError)

    r3 = runner.invoke(cli)
    assert r3.exit_code == 0
    assert "call-3" in r3.output


def test_sys_streams_restored_after_invoke():
    """``sys.stdout``/``stderr``/``stdin`` are restored after ``invoke()``."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    original_stdin = sys.stdin

    @click.command()
    def cli():
        click.echo("inside")

    runner = CliRunner()
    runner.invoke(cli)

    assert sys.stdout is original_stdout
    assert sys.stderr is original_stderr
    assert sys.stdin is original_stdin


def test_sys_streams_restored_after_exception():
    """sys streams are restored even when the command raises."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    @click.command()
    def cli():
        raise RuntimeError("boom")

    runner = CliRunner()
    runner.invoke(cli)

    assert sys.stdout is original_stdout
    assert sys.stderr is original_stderr


# ---------------------------------------------------------------------------
# Category 6: Stress tests - high-iteration reproducers for race conditions
#
# These are marked with ``pytest.mark.stress`` so they can be included or
# excluded independently. The CI workflow runs them in a separate job.
# ---------------------------------------------------------------------------


@pytest.mark.stress
@pytest.mark.parametrize("_", range(10_000))
def test_stress_thread_pool_with_exit(_):
    """Exact #2993 reproducer: ``ThreadPoolExecutor`` + ``SystemExit``."""

    @click.command()
    @click.argument("args", nargs=-1)
    def cli(**_kw):
        with ThreadPoolExecutor() as executor:
            executor.submit(lambda: None).result()
        raise SystemExit(1)

    runner = CliRunner()
    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 1


@pytest.mark.stress
@pytest.mark.parametrize("_", range(10_000))
def test_stress_logging_sequential_invocations(_):
    """#3110/#824 reproducer: sequential invocations with logging."""
    logger = logging.getLogger("stress_sequential")

    @click.command()
    def cli():
        logger.warning("msg")
        click.echo("ok")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0


@pytest.mark.stress
@pytest.mark.parametrize("_", range(10_000))
def test_stress_gc_between_invocations(_):
    """Force GC after each invocation to provoke finalizer races."""

    @click.command()
    def cli():
        click.echo("output")
        click.echo("error", err=True)

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "output" in result.output
    gc.collect()

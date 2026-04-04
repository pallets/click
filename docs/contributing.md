# Contributing to Click

These guidelines are particular to Click and complement the `general ones for all Pallets projects <https://palletsprojects.com/contributing/>`_.

## Running the Test Suite

The default invocation runs the fast unit tests:

```shell-session
$ tox
```

Or without tox:

```shell-session
$ pytest
```

### Stress Tests

These are a collection of long-running tests that reproduce race conditions in `CliRunner`. They are marked with `@pytest.mark.stress`.

Run them with the dedicated tox environment:

```shell-session
$ tox -e stress-py3.14
```

Or directly with pytest:

```shell-session
$ pytest tests/test_stream_lifecycle.py -m stress -x --override-ini="addopts="
```

These tests run 30_000 iterations each and take a long time. Use `-x` to stop at the first failure.

### Randomized & Parallel Tests

Runs the full test suite in random order across multiple processes to detect test pollution and race conditions. This uses `pytest-randomly` and `pytest-xdist`.

```shell-session
$ tox -e random
```

You can reproduce a specific ordering by passing the seed printed at the start of the run:

```shell-session
$ tox -e random -- -p randomly -p no:randomly -p randomly --randomly-seed=12345
```

### Flask Smoke Tests

A CI workflow (`.github/workflows/test-flask.yaml`) runs Flask's own test suite against Click's `main` branch. This catches regressions that would break Flask, Click's primary downstream consumer.

The workflow clones Flask, installs it, then overrides Click with the current branch. To replicate locally:

```shell-session
$ git clone https://github.com/pallets/flask
$ cd flask
$ uv venv --python 3.14
$ uv sync --all-extras
$ uv run --with "git+https://github.com/pallets/click.git@main" -- pytest
```

Replace `@main` with your branch or a local path (`-e /path/to/click`) to test local changes.

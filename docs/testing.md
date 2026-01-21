# Testing Click Applications

```{eval-rst}
.. currentmodule:: click.testing
```

Click provides the {ref}`click.testing <testing>` module to help you invoke command line applications and check their behavior.

These tools should only be used for testing since they change
the entire interpreter state for simplicity. They are not thread-safe!

The examples use [pytest](https://docs.pytest.org/en/stable/) style tests.

```{contents}
:depth: 1
:local: true
```

## Basic Example

The key pieces are:
  - {class}`CliRunner` - used to invoke commands as command line scripts.
  - {class}`Result` - returned from {meth}`CliRunner.invoke`. Captures output data, exit code, optional exception, and captures the output as bytes and binary data.

```{code-block} python
:caption: hello.py

import click

@click.command()
@click.argument('name')
def hello(name):
   click.echo(f'Hello {name}!')
```

```{code-block} python
:caption: test_hello.py

from click.testing import CliRunner
from hello import hello

def test_hello_world():
  runner = CliRunner()
  result = runner.invoke(hello, ['Peter'])
  assert result.exit_code == 0
  assert result.output == 'Hello Peter!\n'
```

## Subcommands

A subcommand name must be specified in the `args` parameter {meth}`CliRunner.invoke`:

```{code-block} python
:caption: sync.py

import click

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
   click.echo(f"Debug mode is {'on' if debug else 'off'}")

@cli.command()
def sync():
   click.echo('Syncing')
```

```{code-block} python
:caption: test_sync.py

from click.testing import CliRunner
from sync import cli

def test_sync():
  runner = CliRunner()
  result = runner.invoke(cli, ['--debug', 'sync'])
  assert result.exit_code == 0
  assert 'Debug mode is on' in result.output
  assert 'Syncing' in result.output
```

## Context Settings

Additional keyword arguments passed to {meth}`CliRunner.invoke` will be used to construct the initial {class}`Context object <click.Context>`.
For example, setting a fixed terminal width equal to 60:

```{code-block} python
:caption: sync.py

import click

@click.group()
def cli():
   pass

@cli.command()
def sync():
   click.echo('Syncing')
```

```{code-block} python
:caption: test_sync.py

from click.testing import CliRunner
from sync import cli

def test_sync():
  runner = CliRunner()
  result = runner.invoke(cli, ['sync'], terminal_width=60)
  assert result.exit_code == 0
  assert 'Debug mode is on' in result.output
  assert 'Syncing' in result.output
```

## File System Isolation

The {meth}`CliRunner.isolated_filesystem` context manager sets the current working directory to a new, empty folder.

```{code-block} python
:caption: cat.py

import click

@click.command()
@click.argument('f', type=click.File())
def cat(f):
   click.echo(f.read())
```

```{code-block} python
:caption: test_cat.py

from click.testing import CliRunner
from cat import cat

def test_cat():
   runner = CliRunner()
   with runner.isolated_filesystem():
      with open('hello.txt', 'w') as f:
          f.write('Hello World!')

      result = runner.invoke(cat, ['hello.txt'])
      assert result.exit_code == 0
      assert result.output == 'Hello World!\n'
```

Pass in a path to control where the temporary directory is created.
In this case, the directory will not be removed by Click. Its useful
to integrate with a framework like Pytest that manages temporary files.

```{code-block} python
:caption: test_cat.py

from click.testing import CliRunner
from cat import cat

def test_cat_with_path_specified():
   runner = CliRunner()
   with runner.isolated_filesystem('~/test_folder'):
      with open('hello.txt', 'w') as f:
          f.write('Hello World!')

      result = runner.invoke(cat, ['hello.txt'])
      assert result.exit_code == 0
      assert result.output == 'Hello World!\n'
```

## Input Streams

The test wrapper can provide input data for the input stream (stdin). This is very useful for testing prompts.

```{code-block} python
:caption: prompt.py

import click

@click.command()
@click.option('--foo', prompt=True)
def prompt(foo):
   click.echo(f"foo={foo}")
```

```{code-block} python
:caption: test_prompt.py

from click.testing import CliRunner
from prompt import prompt

def test_prompts():
   runner = CliRunner()
   result = runner.invoke(prompt, input='wau wau\n')
   assert not result.exception
   assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
```

Prompts will be emulated so they write the input data to
the output stream as well. If hidden input is expected then this
does not happen.

## Running Click's Test Suite

This section covers running Click's own test suite, which is useful for contributors.

### Parallel Test Execution with Tox

Click's tests can be run in parallel using tox:

```bash
# Run all tox environments in parallel
tox p

# Or run pytest with parallel execution (requires pytest-xdist)
pytest -n auto
```

### Testing Pager Functionality

Click's `echo_via_pager()` function pipes output to an external pager command
(like `less` or `cat`). Testing this requires special consideration for parallel
test execution.

#### The Problem with Global Patching

Avoid globally patching `subprocess.Popen` to capture pager output:

```{code-block} python
:caption: DON'T DO THIS - causes race conditions in parallel tests

from unittest.mock import patch
from functools import partial

with patch.object(subprocess, "Popen", partial(subprocess.Popen, stdout=f)):
    click.echo_via_pager(test_input)
```

This approach fails in parallel tests because:

1. **Global state modification**: Patching `subprocess.Popen` affects all
   processes, not just the current test.
2. **Race conditions**: Multiple test processes compete to patch/unpatch
   the same global object.

#### The Solution: Fake Pager Script

Instead, use a "fake pager" approach with pytest's `tmp_path` fixture:

```{code-block} python
:caption: conftest.py or test file

@pytest.fixture
def fake_pager(tmp_path):
    """Create a fake pager script that writes stdin to a unique output file."""
    output_file = tmp_path / "pager_output.txt"
    pager_script = tmp_path / "fake_pager.sh"

    pager_script.write_text(f'#!/bin/sh\ncat > "{output_file}"\n')
    pager_script.chmod(0o755)

    return pager_script, output_file
```

```{code-block} python
:caption: test_pager.py

def test_echo_via_pager(monkeypatch, fake_pager):
    pager_script, output_file = fake_pager
    monkeypatch.setitem(os.environ, "PAGER", str(pager_script))
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    click.echo_via_pager("hello world")

    assert output_file.read_text() == "hello world\n"
```

This works because:

- Each test gets unique script and output files via `tmp_path`
- No global Python state is modified
- Tests run in complete isolation

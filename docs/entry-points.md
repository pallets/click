# Packaging Entry Points

```{eval-rst}
.. currentmodule:: click
```

It's recommended to write command line utilities as installable packages with
entry points instead of telling users to run ``python hello.py``.

A distribution package is a ``.whl`` file you install with pip or another Python
installer. You use a ``pyproject.toml`` file to describe the project and how it
is built into a package. You might upload this package to PyPI, or distribute it
to your users in another way.

Python installers create executable scripts that will run a specified Python
function. These are known as "entry points". The installer knows how to create
an executable regardless of the operating system, so it will work on Linux,
Windows, MacOS, etc.

## Project Files

To install your app with an entry point, all you need is the script and a
``pyproject.toml`` file. Here's an example project directory:

```text
hello-project/
    src/
        hello/
            __init__.py
            hello.py
    pyproject.toml
```

Contents of ``hello.py``:

```{eval-rst}
.. click:example::
    import click

    @click.command()
    def cli():
        """Prints a greeting."""
        click.echo("Hello, World!")
```

Contents of ``pyproject.toml``:

```toml
[project]
name = "hello"
version = "1.0.0"
description = "Hello CLI"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
]

[project.scripts]
hello = "hello.hello:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"
```

The magic is in the ``project.scripts`` section. Each line identifies one executable
script. The first part before the equals sign (``=``) is the name of the script that
should be generated, the second part is the import path followed by a colon
(``:``) with the function to call (the Click command).

## Installation

When your package is installed, the installer will create an executable script
based on the configuration. During development, you can install in editable
mode using the ``-e`` option. Remember to use a virtual environment!

```console
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install -e .
```

Afterwards, your command should be available:

```console
$ hello
Hello, World!
```

# Standalone Application with Nuitka

[Nuitka](https://nuitka.net/) compiles a Python project into a native
executable. It bundles a Python interpreter and all dependencies, so the
result runs on a machine with no Python installed.

- Compiles Python to C, then to machine code.
- Produces one executable file, or a folder of files.
- Builds for the operating system and architecture it runs on: macOS,
    Windows, and Linux.

This page outlines the basics of packaging a Click application with
Nuitka. Be sure to read its
[user manual](https://nuitka.net/user-documentation/) and use
``python -m nuitka --help`` to understand what features are available.

## Installation

Install Nuitka in the virtual environment:

```shell-session
$ pip install "nuitka[onefile]"
```

The ``onefile`` extra installs the compression library Nuitka uses to pack
the executable into a single file.

Nuitka compiles to C, so it needs a C compiler too. On macOS, install the
Xcode command line tools with ``xcode-select --install``. On Linux, install
``gcc``. On Windows, Nuitka uses the newest installed Visual Studio
compiler, and it asks to download MinGW64 when it finds none.

## Configuration

The build on this page takes every setting from the command line, so
Nuitka needs no configuration file for it. It takes the package to compile
as an argument, and it finds the dependencies in the virtual environment
it runs in.

Given a Click application with the following project structure:

```text
hello-cli/
    src/
        hello_cli/
            __init__.py
            app.py
    LICENSE
    pyproject.toml
```

Where ``app.py`` contains a Click command:

```python
import click


@click.command()
@click.argument("name", default="World")
@click.option("--count", default=1, help="Number of times to greet.")
def main(name, count):
    """Greet someone by NAME (default: World)."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

Declare the dependencies and the command in ``pyproject.toml``, the way
{doc}`entry-points` describes:

```toml
[project]
name = "hello-cli"
version = "0.0.1"
description = "My first application"
dependencies = [
    "click>=8.1",
]

[project.scripts]
hello-cli = "hello_cli.app:main"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"
```

Install the project in the virtual environment:

```shell-session
$ pip install .
```

The install gives Nuitka the dependencies to bundle. It also makes the
package metadata available to the build, which
[Package Metadata](#package-metadata) needs.

## Entry Point

Nuitka compiles the package's ``__main__.py`` into the executable and runs
it as the main program, so a ``__main__.py`` file **must** exist in the
package. Without it, the build stops with
``can't find '__main__' module``.

Create ``__main__.py`` in the package directory and call the Click command:

```python
from hello_cli.app import main

if __name__ == "__main__":
    main()
```

## Building

Compile the package from the project root:

```shell-session
$ python -m nuitka --mode=onefile --output-dir=dist --output-filename=hello-cli --remove-output src/hello_cli
```

The key parts of the command are:

- ``--mode=onefile``: produce one self-contained executable file.
    ``--mode=standalone`` produces a folder with the executable and the
    files it needs instead. A onefile executable unpacks itself into a
    temporary directory every time it starts, which a standalone one does
    not.
- ``--output-dir=dist``: write the build output to ``dist`` instead of the
    current directory.
- ``--output-filename=hello-cli``: name the executable. Without it, the
    executable is named after the package and gets a ``.bin`` suffix on
    Linux and macOS. Windows adds ``.exe`` whether you name the file or
    not. A standalone build puts the executable in a folder named after
    the package and ending with ``.dist``, whatever name this option
    gives.
- ``--remove-output``: delete the intermediate build folders and keep only
    the executable.
- ``src/hello_cli``: the package to compile. Pass the directory that holds
    ``__main__.py``. Nuitka warns if you pass the file itself.

Compiling takes longer than running a script, because Nuitka compiles every
module it bundles, Click and the standard library included. The executable
it produces runs with no Python installed, on the operating system and
architecture it was built for.

Nuitka builds for the operating system it runs on. To publish an executable
for each platform, run the build on each one, which a continuous
integration workflow usually does.

## Running the Executable

Run it and pass arguments to it:

```shell-session
$ dist/hello-cli World
Hello, World!
$ dist/hello-cli World --count 2
Hello, World!
Hello, World!
```

The executable reports its own file name as the program name, so help and
errors read like the ones the installed ``hello-cli`` command produces:

```shell-session
$ dist/hello-cli --help
Usage: hello-cli [OPTIONS] [NAME]

  Greet someone by NAME (default: World).

Options:
  --count INTEGER  Number of times to greet.
  --help           Show this message and exit.
```

## Package Metadata

{func}`click.version_option` reads the version from the package metadata
with {mod}`importlib.metadata`. A compiled executable carries no package
metadata by default, so the option raises
``RuntimeError: 'hello_cli' is not installed.`` The message also suggests
passing ``package_name`` instead.

Add ``--include-distribution-metadata=hello-cli`` to the build command,
naming the distribution from ``[project] name``. The option reads the
metadata of an installed distribution, which is what the ``pip install .``
step above provides. Give the distribution name, not the import name:
``hello-cli``, not ``hello_cli``. Nuitka resolves ``hello_cli`` too, then
warns that the distribution is really named ``hello-cli``.

Pass ``version`` to the decorator instead, if you would rather not bundle
the metadata:

```python
@click.version_option(version="0.0.1")
```

## Lazily Loaded Subcommands

Nuitka follows the imports it finds in the source. A group that loads its
subcommands at run time, like the one in
[Lazily Loading Subcommands](complex.md#lazily-loading-subcommands), names
them as strings, so Nuitka leaves those modules out of the executable. The
subcommand then fails with ``ModuleNotFoundError``.

Add the package that holds the subcommands to the build command, with
``--include-package=hello_cli.commands``. ``--include-package`` adds every
module below a package, and ``--include-module`` adds a single module.

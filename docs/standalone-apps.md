# Standalone Application with Briefcase

[Briefcase](https://briefcase.beeware.org/) is a tool for packaging Python
projects as standalone native applications. It can produce installers and
executables for macOS, Windows, and Linux that do not require the user to
install Python or any dependencies.

- Produces platform-native installers (``.pkg`` on macOS, ``.msi`` on
    Windows, ``.deb``/``.rpm`` on Linux).
- Bundles a Python interpreter and all dependencies.
- Supports passing command line arguments to the app.

This page outlines the basics of packaging a Click application with
Briefcase. Be sure to read its
[documentation](https://briefcase.beeware.org/en/stable/how-to/building/cli-apps/)
and use ``briefcase --help`` to understand what features are available.

## Installation

Install Briefcase in the virtual environment:

```console
pip install briefcase
```

## Configuration

Add a ``[tool.briefcase]`` section and a
``[tool.briefcase.app.<app-name>]`` section to ``pyproject.toml``.
Set ``console_app = true`` so Briefcase treats the project as a command
line application rather than a GUI application.

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

Add the following Briefcase configuration to ``pyproject.toml``:

```toml
[tool.briefcase]
project_name = "Hello CLI"
bundle = "com.example"
version = "0.0.1"
url = "https://example.com/hello-cli"
license.file = "LICENSE"
author = "Your Name"
author_email = "you@example.com"

[tool.briefcase.app.hello-cli]
formal_name = "Hello CLI"
description = "My first application"
long_description = """More details about the app should go here.
"""
sources = [
    "src/hello_cli",
]
console_app = true
requires = [
    "click",
]
```

The key settings are:

- ``console_app = true`` -- tells Briefcase this is a terminal
    application, not a GUI.
- ``sources`` -- the list of source packages to include.
- ``requires`` -- the Python dependencies to bundle (Click and any other
    libraries the project needs).

## Entry Point

Briefcase launches the application by running the package with
``python -m <package>``, so a ``__main__.py`` file **must** exist in the
package. Without it, Briefcase will not be able to start the application.

Create ``__main__.py`` in the package directory and call the Click
command:

```python
from hello_cli.app import main

if __name__ == "__main__":
    main()
```

## Running

Use ``briefcase dev`` to run the application directly from the source
tree. Pass command line arguments after ``--``:

```console
$ briefcase dev -- World
Hello, World!
$ briefcase dev -- World --count 2
Hello, World!
Hello, World!
```

## Building and Packaging

To create a distributable executable, run the following commands:

```console
briefcase create
briefcase build
briefcase package
```

``briefcase create`` downloads a Python interpreter and installs
dependencies into an isolated app bundle. ``briefcase build`` compiles
the app, and ``briefcase package`` produces the final platform installer.

On macOS, this produces a ``.pkg`` installer. On Windows, it produces a
``.msi`` installer. On Linux, it produces a system package (``.deb``,
``.rpm``, etc.) for the current distribution.

Once installed, users can run the application directly from the terminal:

```console
$ hello-cli World
Hello, World!
$ hello-cli World --count 2
Hello, World!
Hello, World!
```

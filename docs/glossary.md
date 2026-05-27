(glossary)=

# Glossary of Terms

```{contents}
---
depth: 1
local: true
---
```

This glossary defines terms as they are used in Click's documentation. It
allows us to be internally consistent in our usage and helps clarify
ambiguous terms that may have different meanings in other contexts.

## Command Line Terms

(command-line-application)=

### Command Line Application

A **command line application** is a program that is executed by typing
commands in a terminal or shell. In Click, a command line application is
created by defining a function decorated with {func}`command` and calling
it. The application processes user input, executes the appropriate
callback, and produces output.

```python
@click.command()
def cli():
    click.echo("Hello, World!")
```

(command-line-utility)=

### Command Line Utility

A **command line utility** is a command line application designed to
perform a specific task or set of related tasks. Utilities are typically
smaller programs that can be combined with other tools. Click excels at
building command line utilities due to its composable nature.

Examples of command line utilities include `ls`, `grep`, `curl`, and
custom tools built with Click.

(terminal)=

### Terminal

A **terminal** (also called a terminal emulator) is a program that
provides a text-based interface to interact with the operating system.
It displays the shell prompt and allows users to type commands and view
output. Common terminals include GNOME Terminal, Terminal.app, Windows
Terminal, and iTerm2.

In Click's documentation, "terminal" refers to the environment where
the command line application runs and where its output is displayed.

## Click-Specific Terms

(option)=

### Option

An **option** in Click is a named parameter that modifies the behavior
of a command. Options are typically prefixed with `` -- `` (long form) or
`` - `` (short form). They can accept values, be flags, or be prompted for
input.

```python
@click.command()
@click.option("--name", "-n", default="World", help="Who to greet")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose mode")
def greet(name, verbose):
    if verbose:
        click.echo(f"Hello, {name}!")
    else:
        click.echo(f"Hi {name}")
```

Options are created using the {func}`option` decorator or the
{class}`Option` class directly. They are distinct from
{ref}`positional arguments <arguments>`.

See {ref}`options` for detailed documentation on creating and using
options.

(flag)=

### Flag

A **flag** is a special type of option that does not accept a value.
Instead, it acts as a boolean switch -- its presence indicates `` True ``
and its absence indicates `` False ``. Flags are created by setting
`` is_flag=True `` when defining an option.

```python
@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose mode")
@click.option("--debug/--no-debug", default=False, help="Toggle debug mode")
def cli(verbose, debug):
    if verbose:
        click.echo("Verbose mode enabled")
    if debug:
        click.echo("Debug mode enabled")
```

Click supports two syntaxes for flags:

- **Simple flags**: `` --verbose `` (uses `` is_flag=True ``)
- **Boolean flags**: `` --debug/--no-debug `` (creates paired flags)

Flags are commonly used for enabling features, toggling modes, or
controlling output verbosity.

(parameter)=

### Parameter

A **parameter** is a general term for any input that a command accepts.
In Click, parameters include:

- {ref}`Options <option>` (`` --name value ``)
- {ref}`Arguments <arguments>` (`` filename ``)
- {ref}`Flags <flag>` (`` --verbose ``)

Parameters are processed in a specific order and can be configured with
types, validation, callbacks, and more.

(command)=

### Command

A **command** in Click is a callable unit of work that processes
parameters and executes a callback function. Commands are created using
the {func}`command` decorator.

```python
@click.command()
@click.argument("name")
def hello(name):
    click.echo(f"Hello, {name}!")
```

Commands can be:

- **Standalone**: A single command that runs directly
- **Grouped**: Part of a {ref}`group` with subcommands

(group)=

### Group

A **group** is a command that contains other commands (subcommands).
Groups are created using the {func}`group` decorator and allow building
hierarchical command line interfaces.

```python
@click.group()
def cli():
    pass

@cli.command()
def init():
    click.echo("Initialized")

@cli.command()
def status():
    click.echo("Status")
```

Groups can be nested to create complex command structures.

(argument)=

### Argument

An **argument** is a positional parameter passed to a command. Unlike
{ref}`options <option>`, arguments don't have names -- they are identified
by their position in the command invocation.

```python
@click.command()
@click.argument("filename")
@click.argument("count", type=int, default=1)
def repeat(filename, count):
    with open(filename) as f:
        for _ in range(count):
            click.echo(f.read())
```

Arguments are created using the {func}`argument` decorator or the
{class}`Argument` class.

(callback)=

### Callback

A **callback** is the function that Click invokes when a command is
executed. It receives the parsed parameters as arguments and performs
the actual work of the command.

```python
@click.command()
@click.option("--name", default="World")
def hello(name):
    # This function is the callback
    click.echo(f"Hello, {name}!")
```

Callbacks can also be used with parameters for validation or
processing before the main command executes.

(context)=

### Context

The **context** ({class}`Context`) is an object that carries state
throughout the execution of a Click application. It stores the parent
command or group, parameter values, configuration settings, and
invocation information.

Contexts form a hierarchy -- each command invocation has its own context
that links to parent contexts in group structures.

```python
@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj["debug"] = True

@cli.command()
@click.pass_context
def subcommand(ctx):
    if ctx.obj["debug"]:
        click.echo("Debug mode")
```

(decorator)=

### Decorator

In Click, a **decorator** is a function that modifies a command
function. Click provides several decorators for adding parameters and
behavior:

- {func}`command` -- Creates a command from a function
- {func}`group` -- Creates a group from a function
- {func}`option` -- Adds an option to a command
- {func}`argument` -- Adds an argument to a command
- {func}`pass_context` -- Passes the context to the callback

Decorators are applied in a specific order and can be stacked.

```python
@click.command()
@click.option("--name", default="World")
@click.pass_context
def hello(ctx, name):
    click.echo(f"Hello, {name}!")
```

## General Terms

### Standard Input (stdin)

**Standard input** (stdin) is the default input stream for a program.
In Click, you can read from stdin using `click.get_text_stream("stdin")`
or by using `` - `` as a filename argument.

### Standard Output (stdout)

**Standard output** (stdout) is the default output stream for a
program. Click's {func}`echo` function writes to stdout by default.
You can redirect stdout to files or pipe it to other commands.

### Standard Error (stderr)

**Standard error** (stderr) is a separate output stream used for
error messages and diagnostic output. Click's {func}`secho` function
can write to stderr, and error messages are typically sent there.

### Exit Code

An **exit code** (or return code) is a numeric value returned by a
program to indicate success or failure. By convention, `` 0 `` means
success and non-zero means error or failure.

Click allows setting exit codes with `sys.exit` or by returning
values from callbacks.

---

```{eval-rst}
.. seealso::

   :doc:`quickstart`
       For a hands-on introduction to Click.

   :doc:`click-concepts`
       For detailed explanations of Click's design.

   :doc:`options`
       For detailed documentation on options.

   :doc:`arguments`
       For detailed documentation on arguments.
```

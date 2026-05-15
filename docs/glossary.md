(glossary)=

# Glossary

```{currentmodule} click
```

This glossary defines key terms as they are used throughout the Click
documentation. It allows us to be internally consistent in our usage.

```{glossary}
Argument
    A positional parameter passed to a command. Arguments are defined with
    the {func}`argument` decorator or the {class}`Argument` class. Unlike
    options, arguments are positional and do not have names prefixed with
    dashes. See {doc}`arguments`.

Callback
    A function that is invoked when a command is executed. In Click, the
    decorated function itself is the command's callback. Parameter
    callbacks are invoked when a parameter value is resolved.

Command
    A single action in a CLI application. Commands are defined using the
    {func}`command` decorator or the {class}`Command` class. A command
    accepts parameters (options and arguments) and executes a callback
    when invoked.

Command Line Application
    A program that is operated through a terminal by typing text commands.
    Click is a toolkit for building command line applications in Python.

Command Line Utility
    A command line application designed to perform a specific task, often
    as part of a larger workflow. Examples include `pip`, `git`, and
    `black`.

Context
    An object that holds state during the execution of a Click command.
    The {class}`Context` carries information such as the parent context
    (for nested commands), whether to run in standalone mode, and other
    invocation metadata. Accessed via {func}`get_current_context` or the
    `ctx` parameter.

Decorator
    A Python function that wraps another function. Click uses decorators
    such as {func}`command`, {func}`option`, {func}`argument`, and
    {func}`group` to declare CLI parameters and structure.

Environment Variable
    A value set in the operating system's environment that Click can read
    as a default for a parameter. Both options and arguments can be
    configured to pull values from environment variables.

Flag
    A boolean option that is either present or absent on the command line.
    Flags do not take a value argument. For example, `--verbose` is a
    flag. In Click, flags are created by setting `is_flag=True` on an
    option, or by using {func}`option` with `flag_value`.

Group
    A command that contains subcommands. Groups are defined using the
    {func}`group` decorator or the {class}`Group` class. They allow
    building multi-command CLI applications with nested command structures.

Parameter
    A generic term covering both {term}`options <Option>` and
    {term}`arguments <Argument>`. Parameters are the values a user passes
    to a command. In Click, all parameters are instances of the
    {class}`Parameter` class.

Option
    A named parameter prefixed with one or two dashes (e.g., `--name` or
    `-n`). Options are defined with the {func}`option` decorator or the
    {class}`Option` class. They can take values, act as {term}`flags`,
    and accept various configuration such as defaults, types, and
    environment variable names. See {doc}`options`.

Parameter Type
    The type of a parameter's value, such as `str`, `int`, `float`, or a
    custom {class}`ParamType`. Click uses parameter types to validate and
    convert input. See {doc}`parameter-types`.

Subcommand
    A command that is nested inside a {term}`Group`. Subcommands are
    added to a group using {meth}`Group.add_command` or the
    {func}`group` decorator's lazy loading features.

Terminal
    The text-based interface through which a user interacts with a
    command line application. Also referred to as a console, shell, or
    command prompt. Click applications read input from and write output
    to the terminal.
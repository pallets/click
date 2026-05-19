(glossary)=

# Glossary

```{currentmodule} click
```

This glossary defines key terms as they are used throughout the Click
documentation. Consistent use of these terms helps avoid ambiguity,
especially when terms have different meanings in other CLI frameworks.

```{contents}
:depth: 1
:local: true
```

## General Terms

(application)=

### Application

A complete command line program built with Click. An application consists
of one or more {ref}`commands <command>`, handles {ref}`parameters
<parameter>` provided by the user, and produces output via the {ref}`terminal`.
Also referred to as a *command line application*.

(command-line-utility)=

### Command Line Utility

A command line program designed for a single, focused task. In Click, a
utility is typically a single {ref}`command <command>` without
{ref}`subcommands <subcommand>`. Compare with {ref}`application`, which
may be composed of multiple commands via a {ref}`group`.

(terminal)=

### Terminal

The environment in which a Click application runs and interacts with the
user. This includes the shell (bash, zsh, cmd, PowerShell), the standard
input/output streams, and the capabilities of the terminal emulator (such
as color support and window size). Click detects terminal properties
automatically through {mod}`click.termui`.

## Command Structure

(command)=

### Command

A function decorated with {func}`~click.command` that performs an action
when invoked. A command accepts {ref}`parameters <parameter>` and is the
basic unit of execution in Click. See {doc}`commands`.

(group)=

### Group

A {ref}`command <command>` that contains {ref}`subcommands <subcommand>`.
Created with {func}`~click.group`. Groups allow building nested CLI
structures where the group's callback runs before the subcommand. See
{doc}`commands-and-groups`.

(subcommand)=

### Subcommand

A {ref}`command <command>` registered under a {ref}`group`. Subcommands
are invoked by name after the group, e.g., `mycli subcommand`. Each
subcommand has its own {ref}`parameters <parameter>` and {ref}`callback
<callback>`.

## Parameters

(parameter)=

### Parameter

A generic term covering both {ref}`options <option>` and {ref}`arguments
<argument>`. Parameters are defined using decorators ({func}`~click.option`,
{func}`~click.argument`) and are passed to the {ref}`callback` as Python
function arguments. See {doc}`parameters`.

(option)=

### Option

A named {ref}`parameter <parameter>` prefixed with `--` (long form) or `-`
(short form). Options are optional by default and can accept values, act as
{ref}`flags <flag>`, or be prompted for interactively. See {doc}`options`.

(flag)=

### Flag

A boolean {ref}`option <option>` that takes no value. Flags toggle a
setting on or off. Click supports two styles:

- Simple flags: `--verbose` (sets the value to `True`)
- Paired flags: `--debug/--no-debug` (explicit on/off toggle)

(argument)=

### Argument

A positional {ref}`parameter <parameter>`. Arguments are defined with
{func}`~click.argument` and are identified by position on the command line
rather than by name. See {doc}`arguments`.

## Callbacks and Context

(callback)=

### Callback

The function that Click invokes when a {ref}`command <command>` runs. This
is the function decorated by {func}`~click.command` (or {func}`~click.group`).
Callbacks receive resolved parameter values as Python arguments. See
{ref}`Callback Evaluation Order <callback-evaluation-order>`.

(context)=

### Context

An object created each time a {ref}`command <command>` is invoked, carrying
runtime state such as parsed parameters, parent context, and configuration.
Contexts form a stack: each {ref}`subcommand`'s context links to its
{ref}`group`'s context. The context is accessible via the `ctx` parameter
or {func}`~click.get_current_context`. See {doc}`advanced`.

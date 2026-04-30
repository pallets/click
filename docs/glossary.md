# Glossary

```{currentmodule} click
```

This glossary defines key terms as they are used throughout the Click
documentation. Having a shared vocabulary helps keep the docs internally
consistent and reduces ambiguity for new users.

## Terms

**Application**
:   A complete command line program built with Click. May consist of a
    single command or a tree of commands and groups. Used interchangeably
    with "command line application" in this documentation.

**Argument**
:   A positional parameter passed to a command. Arguments are
    required by default and are identified by their position on the
    command line, not by name. See {doc}`arguments`.

**Command**
:   A single callable unit in a Click application. Created with
    {func}`~click.command`. A command can accept
    {class}`~click.Option` and {class}`~click.Argument` parameters.
    See {doc}`commands`.

**Command line application**
:   A program that is operated by typing text commands into a terminal.
    In Click, this is any program built using the Click framework.
    Used interchangeably with "application".

**Command line utility**
:   A command line application designed for a specific task, often
    without a persistent interactive session. Examples include ``ls``,
    ``grep``, and ``curl``. In Click documentation, "application" is
    preferred for clarity.

**Flag**
:   An option that takes no value, acting as a boolean switch. Created
    by passing `is_flag=True` to {func}`~click.option`. Example:
    ``--verbose``. See {ref}`is-flag`.

**Group**
:   A command that contains subcommands. Created with
    {func}`~click.group`. Groups enable nested CLI structures where
    the first argument selects a subcommand. See {doc}`commands-and-groups`.

**Option**
:   A named parameter passed to a command using ``--name value`` or
    ``--name=value`` syntax. Options are optional by default. See
    {doc}`options`.

**Parameter**
:   A generic term covering both {term}`options <Option>` and
    {term}`arguments <Argument>`. See {doc}`parameters`.

**Terminal**
:   The text-based interface where a command line application is
    executed. Also called a "console", "shell", or "command prompt".
    Click uses "terminal" throughout its documentation.

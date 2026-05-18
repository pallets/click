(glossary)=

# Glossary

```{currentmodule} click
```

This glossary defines key terms as they are used throughout the
Click documentation. It helps us be internally consistent in how
we refer to concepts.

```{glossary}

Command Line Application
    A program that is operated through a command-line interface
    (CLI). A command line application accepts text commands,
    options, and arguments typed into a terminal. Click is a
    toolkit for building command line applications in Python.

    Many command line applications provide multiple {term}`commands`,
    each performing a different action. For example, `git` is a
    command line application with commands like `git commit` and
    `git push`.

    See {doc}`quickstart` for getting started.

Command Line Utility
    A command line application designed to perform a specific,
    focused task. The terms "command line application" and
    "command line utility" are largely interchangeable, but
    "utility" emphasizes a narrower, task-oriented purpose.

    Examples of command line utilities include `black` (code
    formatter), `pip` (package installer), and `flake8` (linter).

Flag
    An {term}`option` that takes no value. A flag is either
    present or absent on the command line. Click implements
    flags as boolean options using {func}`option` with
    ``is_flag=True``.

    A common pattern is the boolean flag pair, where ``--flag``
    sets a value and ``--no-flag`` unsets it. This is
    Click's default for boolean options.

    See {ref}`option-boolean-flag` for details.

Option
    A named parameter passed to a {term}`command` on the command
    line. Options are prefixed with dashes (``--verbose``,
    ``-v``) and are defined with the {func}`option` decorator
    or the {class}`Option` class.

    Options can accept values (``--name Alice``), act as
    {term}`flags <flag>` (``--verbose``), or count occurrences
    (``-vvv``). Options are positional with respect to commands
    but not positional with respect to other arguments on the
    command line.

    See {doc}`options` for the full reference.

Terminal
    A text-based interface for interacting with a computer. The
    terminal (also called console, shell, or command prompt)
    allows users to type commands and see output. When Click
    runs, it reads input from and writes output to the terminal.

    Click handles terminal interaction through utilities like
    {func}`echo`, {func}`prompt`, and {func}`confirm`, which
    adapt to the capabilities of the user's terminal, including
    color support and Unicode rendering.

    See {doc}`quickstart` for an introduction to using Click
    from the terminal.
```

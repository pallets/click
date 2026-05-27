# General Command Line Topics

```{currentmodule} click
```

```{contents}
---
depth: 1
local: true
---
```

(cli-glossary)=
## Glossary

This section defines the command-line terms used throughout Click's
reference docs. Keeping these meanings consistent helps avoid ambiguity
when describing how a Click program is declared and how a user invokes it.

- **Command line application**: A program that a user runs from a shell by
  entering a command name and, optionally, parameters. In Click, a command
  line application is built from one or more commands.
- **Command line utility**: A command line application that performs a focused
  task, often designed to compose well with other commands or scripts.
- **Terminal**: The interactive text environment where a user enters commands
  and reads output. The terminal is distinct from the shell that parses the
  command line before Click receives it.
- **Parameter**: A value that Click parses from the command line. Options and
  arguments are both parameters.
- **Option**: A parameter identified by one or more prefixed names, such as
  `--count` or `-c`. Options are usually optional and can accept values,
  behave as flags, or be provided multiple times.
- **Flag**: An option that changes behavior by being present, rather than by
  requiring a separate value. Boolean flags such as `--verbose` commonly switch
  a value from `False` to `True`, while feature-switch flags can choose from a
  fixed set of values.
- **Argument**: A parameter identified by its position on the command line,
  rather than by a prefixed option name.

(exit-codes)=
## Exit Codes

When a command is executed from the command line, then an exit code is return. The exit code, also called exit status or exit status code, is a positive integer that tells you whether the command executed with or without errors.

| Exit Code | Meaning                                         |
|-----------|-------------------------------------------------|
| 0         | Success — the command completed without errors. |
| > 0       | Executed with errors                            |

Exit codes greater than zero mean are specific to the Operating System, Shell, and/or command.

To access the exit code, execute the command, then do the following depending:

```{eval-rst}
.. tabs::

    .. group-tab:: Powershell

        .. code-block:: powershell

           > echo $LASTEXITCODE

    .. group-tab:: Bash

        .. code-block:: bash

            $ echo $?

    .. group-tab:: Command Prompt


        .. code-block:: text

            > echo %ERRORLEVEL%
```

For Click specific behavior on exit codes, see {ref}`exception-handling-exit-codes`.

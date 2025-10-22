# General Command Line Topics

```{currentmodule} click
```

```{contents}
---
depth: 1
local: true
---
```

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



For Click specific behavior on exit codes, see {ref}`exception-handling-exit-codes`.

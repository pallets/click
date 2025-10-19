# General Command Line Topics

```{currentmodule} click
```

```{contents}
---
depth: 2
local: true
---
```

## Exit Codes

When a command is executed from the command line, then an exit code is return. The exit code, also called exit status or exit status code, is a integer that tells you whether the command executed without errors or with errors. Exit code 0 means the command executed without errors. All of the other exit codes are defined by the Operating System, Shell, and/or command.

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

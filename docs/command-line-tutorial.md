# Command line basics

TThis tutorial shows the developer the basics of using the command line. It should take about 20 minutes to complete.

```{contents}
:depth: 2
:local:
```

## What is a Command Line Interface (CLI)?

A Command Line Interface (CLI) is a text-based way to interact with your computer.
Instead of clicking icons or buttons, you type commands into a terminal. Some examples
of terminals include:

-   **Bash** (Bourne Again SHell): Common on macOS and Linux systems.
-   **cmd.exe**: The traditional command prompt on Windows.

## How does it work?

Users type commands into a CLI shell (e.g., Bash, cmd), which interprets and executes them:

**Shell Role:** Acts as an intermediary between the user and the operating system<br>
**Command Process:**
The shell parses the command, identifying the action, options, and arguments. It locates the command in the system’s PATH and executes it. The system returns output (e.g., data, error messages) to the CLI.

## Prerequisites

-   A computer with a shell (macOS / Linux / Windows).
-   A text editor you can run from the terminal (nano, vi, notepad, code, etc.).

## Interacting with your command line

Before using the command line, it's helpful to know which operating system and shell you are running. Different systems have slightly different commands; the examples below are grouped by platform so you can copy the commands that match your environment.

````{tabs}
```{tab} macOS / Linux
```bash
# Show OS/version information
uname -a

# Print working directory and list files
pwd
ls -la

# Move around the filesystem
cd /tmp
cd ~
cd ..

# Create a directory and an empty file
mkdir -p myproject
touch myproject/hello.txt

# Edit the file (simple editor)
nano myproject/hello.txt
# What to put in the file
# Hello from the command line!

# Print file contents
cat myproject/hello.txt

# Search inside the file
grep "Hello" myproject/hello.txt

# Show a CLI's help message (mycli here refers to any command line program e.g git, python, etc.)
mycli --help
python -m mycli --help
````

````

```{tab} Windows (cmd.exe)
```bat
REM Show OS/version information
ver

REM Current directory and list files
echo %CD%
dir

REM Move around
cd /d C:\Temp
cd /d %USERPROFILE%
cd ..

REM Create directory and file
mkdir myproject
type nul > myproject\hello.txt

REM Edit with notepad
notepad myproject\hello.txt

REM Print file contents
type myproject\hello.txt

REM Search for Hello (findstr)
findstr "Hello" myproject\hello.txt

REM Show help for a CLI (mycli here refers to any command line program e.g git, python, etc.)
mycli --help
python -m mycli --help
````

```

```

## Short explanations (why these commands matter)

-   Operating system information helps you choose the right commands and troubleshoot issues.
-   Directories (folders) contain files and other directories. Paths can be absolute (start at the filesystem root) or relative (start from your current directory).
-   Moving around with `cd` changes your working directory; many commands operate relative to it.
-   Creating and editing small files is how you try things quickly from the terminal without opening a full IDE.
-   Grep-style searching is essential for finding text in logs, configs, or code.
-   Most CLIs expose `--help` (or `-h`) which documents commands, options, and usage.

## Quick reference (cheat sheet)

macOS / Linux

```bash
pwd             # print working directory
ls -la          # list files
cd <dir>        # change directory
mkdir -p <dir>  # make directory
touch <file>    # create empty file
nano <file>     # edit
cat <file>      # print contents
grep <pat> <f>  # search
mycli --help    # CLI help (mycli here refers to any command line program e.g git, python, etc.)
```

Windows (cmd.exe)

```bat
echo %CD%
dir
cd /d <dir>
mkdir <dir>
type nul > <file>
notepad <file>
type <file>
findstr <pat> <file>
mycli --help
```

## Conclusion

Congratulations! You've completed the command line basics tutorial.
You now have the foundational skills to navigate and interact with your computer using the command line. And you are ready to explore Click-based CLIs and build your own!

## Next steps and Further Reading

These resources will take you deeper:

-   Shell basics tutorial: https://swcarpentry.github.io/shell-novice/
-   Bash manual: https://www.gnu.org/software/bash/manual/
-   Grep manual (GNU): https://www.gnu.org/software/grep/manual/grep.html
-   Filesystem hierarchy (Linux): https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard
-   Windows filesystem and paths: https://learn.microsoft.com/windows/win32/fileio/file-paths

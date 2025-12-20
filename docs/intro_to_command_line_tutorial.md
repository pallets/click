# Command line basics — Introduction to command line interfaces (CLIs)

This short, hands-on tutorial gives developers the minimal set of command-line skills needed to start using or building Click-based CLIs.
It is written for beginners who may have little or no command line experience.
All examples provide commands for both macOS/Linux (Bash) and Windows (cmd).

```{contents}
:depth: 2
:local:
```

First Let's understand what a command line interface is.

## What is a Command Line Interface (CLI)?

A Command Line Interface (CLI) is a text-based way to interact with your computer.
Instead of clicking icons or buttons, you type commands into a terminal or console window.
CLIs are powerful tools for developers and system administrators because they allow for automation, scripting, and remote access to systems.
Examples of popular CLIs include:

- **Bash** (Bourne Again SHell): Common on macOS and Linux systems.
- **cmd.exe**: The traditional command prompt on Windows.

## How does it work?

Users type commands into a CLI shell (e.g., Bash, cmd), which interprets and executes them:

**Shell Role:** Acts as an intermediary between the user and the operating system<br>
**Command Process:**
The shell parses the command, identifying the action, options, and arguments. It locates the command in the system’s PATH and executes it. The system returns output (e.g., data, error messages) to the CLI.

## What you will learn

By the end of this tutorial, you will be able to:

- Identify your OS and shell
- See the difference between files and directories, and how paths work
- Move around the filesystem, create a directory and a file
- Edit the file and print its contents in the terminal
- Search inside a file (grep-style)
- View a CLI's help output

## Prerequisites

- A computer with a shell (macOS / Linux / Windows).
- A text editor you can run from the terminal (nano, vi, notepad, code, etc.).

## Interacting with your command line

Before using the command line, it's helpful to know which operating system and shell you are running. Different systems have slightly different commands; the examples below are grouped by platform so you can copy the commands that match your environment.

### macOS / Linux

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
```

### Windows (cmd.exe)

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
```

Save and exit the editor, then verify with `cat` / `type` depending on your shell.

## Further Reading

- [SW Carpentry](https://swcarpentry.github.io/shell-novice/)
- [Microsoft Powershell](https://learn.microsoft.com/powershell/)
- [Ubuntu](https://ubuntu.com/tutorials/command-line-for-beginners)
- [Python](https://docs.python.org/3/tutorial/venv.html)

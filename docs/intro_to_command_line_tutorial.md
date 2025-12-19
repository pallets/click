# Command Line Basics

This tutorial introduces the minimal set of command line concepts needed to use or develop **Click-based command line interfaces (CLIs)**.
It is written for beginners who may have little or no command line experience.
All examples provide commands for both macOS/Linux (Bash) and Windows (PowerShell).

```{contents}
:depth: 2
:local:
```

## Understanding Your System

Before using the command line, it's important to know which operating system and shell you are running.
Different systems have slightly different commands, so this knowledge will help you follow tutorials and avoid errors.

**macOS / Linux**
```bash
uname -a # Display OS version and system information
````

**Windows (PowerShell)**
```powershell
Get-ComputerInfo | Select-Object WindowsVersion, OsName, OsBuildNumber
````

> **Tip**
>
> Knowing your OS helps you troubleshoot problems more effectively.


> **Common mistake:**
>
> Trying to run a Linux command on Windows without an appropriate shell like WSL.


## Files, Directories, and Paths
Command-line tools interact with files and directories:
- **File**: A piece of stored data (text, code, image, etc.).
- **Directory (folder)**: A container for files or other directories.
- **Path**: A reference to a file or directory location, either relative or absolute.

**macOS / Linux**
```bash
pwd # Print working directory
ls # List files and directories
````

**Windows (PowerShell)**
```powershell
Get-Location
Get-ChildItem
````

> **Tip**
>
>Relative paths start from your current directory; absolute paths start from the root.


> **Common mistake:**
>
> Confusing relative and absolute paths, which can cause “file not found” errors.


## Navigating the Filesystem
You can move around directories using the `cd` command:

**macOS / Linux**
```bash
cd /tmp  # Go to /tmp
cd ~     # Go to your home directory
cd ..    # Go up one directory level
````

**Windows (PowerShell)**
```powershell
cd C:\Temp
cd $HOME
cd ..
````

> **Tip**
>
> Use `pwd` (Linux/macOS) or `Get-Location` (Windows) to check your current directory.


> **Common mistake:**
>
> Forgetting that commands like `cd` are case-sensitive on Linux/macOS.


## Creating Directories
To organize your files, create a directory using:

**macOS / Linux**
```bash
mkdir myproject  # Make a new directory called myproject
````

**Windows (PowerShell)**
```powershell
New-Item -ItemType Directory -Name myproject
````

> **Tip**
>
>You can create nested directories with `mkdir -p myproject/subdir` on Linux/macOS.


> **Common mistake:**
>
> Trying to create a directory that already exists will fail unless using the `-p` flag.


## Creating Files
Create an empty file inside a directory:

**macOS / Linux**
```bash
touch myproject/hello.txt
````

**Windows (PowerShell)**
```powershell
New-Item -ItemType File myproject/hello.txt
````

> **Tip**
>
>Files can be created in any directory you have write permissions for.


> **Common mistake:**
>
> Forgetting to specify the directory and ending up creating the file in the wrong place.


## Editing Files
You can open and edit files with a text editor of your choice:

**macOS / Linux**
```bash
nano myproject/hello.txt
````

**Windows (PowerShell)**
```powershell
notepad myproject/hello.txt
````

Add the following line to the file:

```
Hello from the command line!
```

> **Tip**
>
>Try a simple editor like nano or notepad first; later you can use VS Code for larger projects.


> **Common mistake:**
>
> Forgetting to save the file before exiting the editor.


## Viewing File Contents
Check the contents of a file using these commands:

**macOS / Linux**
```bash
cat myproject/hello.txt
````

**Windows (PowerShell)**
```powershell
Get-Content myproject/hello.txt
````

> **Tip**
>
>Use these commands to quickly verify your edits.


> **Common mistake:**
>
> Using `cat` on very large files can flood the terminal; use `less` instead.


## Searching Within Files
Search for specific text inside a file:

**macOS / Linux**
```bash
grep "Hello" myproject/hello.txt
````

**Windows (PowerShell)**
```powershell
Select-String -Pattern "Hello" -Path myproject/hello.txt
````
> **Tip**
>
> Use search to verify that text exists or to debug issues in configuration files.


> **Common mistake:**
>
> Forgetting to quote search patterns with spaces, which can break the command.


## Getting Help for a CLI

Click-based CLIs support the `--help` option, which lists commands and options:
```
mycli --help
```

If the CLI is implemented as a Python module:

```
python -m mycli --help
```

## Further Reading

- [SW Carpentry](https://swcarpentry.github.io/shell-novice/)
- [Microsoft Powershell](https://learn.microsoft.com/powershell/)
- [Ubuntu](https://ubuntu.com/tutorials/command-line-for-beginners)
- [Python](https://docs.python.org/3/tutorial/venv.html)

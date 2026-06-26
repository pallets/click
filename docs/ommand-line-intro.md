# Introduction to the Command Line

This tutorial introduces the basics of working in a terminal — the same
environment you use when running Click applications. It takes about 15 minutes
to complete.

## What is a Terminal?

A **terminal** (also called a shell, command prompt, or console) is a
text-based interface for running programs on your computer. When you run a
Click application, your users interact with it through a terminal.

Common terminals: `bash` and `zsh` on macOS/Linux, PowerShell or CMD on
Windows.

## Navigating the File System

Your terminal always has a **current directory** — the folder it is "inside"
right now.

### Print your current location

```bash
pwd
```

Output example: `/home/alice/projects`

### List files and directories

```bash
ls          # short listing
ls -l       # detailed listing with sizes and dates
ls -la      # include hidden files (starting with .)
```

### Change directory

```bash
cd projects          # move into the projects/ folder
cd ..                # move one level up
cd ~                 # move to your home directory
cd /tmp              # move to an absolute path
```

## Creating Files and Directories

### Create a directory

```bash
mkdir my-project
mkdir -p my-project/src/utils   # create nested directories at once
```

### Create an empty file

```bash
touch hello.py
```

### Write content to a file

```bash
echo "print('hello')" > hello.py    # overwrite
echo "print('world')" >> hello.py   # append
```

## Reading File Contents

```bash
cat hello.py          # print entire file
head -n 5 hello.py    # first 5 lines
tail -n 5 hello.py    # last 5 lines
```

## Searching with grep

`grep` searches for text inside files.

```bash
grep "hello" hello.py              # lines containing "hello"
grep -r "import click" .           # search recursively in current directory
grep -n "def " my_app.py           # show line numbers
```

## Getting Help

Almost every CLI program accepts `--help`:

```bash
python hello.py --help
ls --help
git --help
```

This is the same flag Click adds to your applications automatically.

## Next Steps

Now that you are comfortable in the terminal, you are ready to build your
first Click application. See the [Quickstart](quickstart.md) guide to get
started.

**Further reading:**

- [The Linux Command Line (free book)](https://linuxcommand.org/tlcl.php)
- [Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- [explainshell.com](https://explainshell.com/) — paste any command to get an explanation

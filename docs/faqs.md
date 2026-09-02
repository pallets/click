# Frequently Asked Questions

```{contents}
:depth: 2
:local: true
```

## General

### Calling a command as a regular function

I decorated a function with `@click.command()` to make it a CLI. When I import that name and call it from Python, it does not run my function. It parses arguments, prints a usage error and exits the process:

```pytb
>>> nasa_date_to_iso("2017-090")
Usage: cli [OPTIONS] DATESTR
Try 'cli --help' for help.

Error: Got unexpected extra arguments (0 1 7 - 0 9 0)
SystemExit: 2
```

#### Answer

This is not a bug in Click. The decorator replaced the function with a {class}`Command` object. Calling that object runs the Click pipeline, and its argument is the list of command line arguments to parse, not the function's parameters.

The recommended pattern is to keep a plain function and wrap it with a thin command:

```python
def nasa_date_to_iso(datestr): ...


@click.command("nasa_date_to_iso")
@click.argument("datestr")
def nasa_date_to_iso_command(datestr):
    click.echo(nasa_date_to_iso(datestr))
```

The function stays available as a Python API, and the command adds the CLI on top. Extracting behavior into a shared function used by several entry points is a common refactor.

If you still want to run the command itself from Python, call it with a list of arguments and `standalone_mode=False` so it returns the result instead of exiting. This runs the Click pipeline, including parsing, validation and callbacks:

```python
nasa_date_to_iso_command(["2017-090"], standalone_mode=False)
```

An alternative form is:

```python
nasa_date_to_iso_command.main(["2017-090"], standalone_mode=False)
```

### Shell Variable Expansion On Windows

I have a simple Click app :

```
import click

@click.command()
@click.argument('message')
def main(message: str):
    click.echo(message)

if __name__ == '__main__':
    main()

```

When you pass an environment variable in the argument, it expands it:

```{code-block} powershell
> Desktop python foo.py '$M0/.viola/2025-01-25-17-20-23-307878'
> M:/home/ramrachum/.viola/2025-01-25-17-20-23-307878
>
```
Note that I used single quotes above, so my shell is not expanding the environment variable, Click does. How do I get Click to not expand it?

#### Answer

If you don't want Click to emulate (as best it can) unix expansion on Windows, pass windows_expand_args=False when calling the CLI.
Windows command line doesn't do any *, ~, or $ENV expansion. It also doesn't distinguish between double quotes and single quotes (where the later means "don't expand here"). Click emulates the expansion so that the app behaves similarly on both platforms, but doesn't receive information about what quotes were used.

### `UnicodeEncodeError` on Windows

A Click CLI that uses Unicode characters in its help text or `echo` output can raise `UnicodeEncodeError`:

```pytb
UnicodeEncodeError: 'charmap' codec can't encode character '\u2023' in position 62: character maps to <undefined>
```

This is not a bug in Click. When `<stdout>` is a console, Click relies on the Windows console API, which supports full Unicode rendering. But when `<stdout>` is redirected, it cannot use that API, so Python falls back to encoding the stream with the system's code page (often `cp1252`) and `errors="strict"`. That codec cannot represent every Unicode character, so the write fails.

#### Answer

Run Python in [UTF-8 mode](https://docs.python.org/3/library/os.html#utf8-mode) so that redirected streams use UTF-8 instead of the code page.

You can enforce that by:
- Setting the `PYTHONUTF8=1` environment variable, or
- Passing `-X utf8` to the `python` executable, or
- Setting `PYTHONIOENCODING=utf8`, which configures only the standard streams, or
- From your code, call `sys.stdout.reconfigure(encoding="utf-8")` and `sys.stderr.reconfigure(encoding="utf-8")` before producing output.

This is not a bug for Click to fix, but a system configuration. It will naturally go away with UTF-8 mode becoming the default in Python 3.15 (see [PEP 686](https://peps.python.org/pep-0686/)).

#### For library authors

Click intentionally does not fix this in code: it has no way to know what the caller expects. Reconfiguring the stream itself would mix encodings within one process: `echo` could write UTF-8 to a redirected file while a bare `print()` still writes the code page. A loud `UnicodeEncodeError` is easier to diagnose than silently interleaved encodings.

But if your own CLI knows the environment it runs under, it can choose to degrade its output:

```python
import sys

encoding = getattr(sys.stdout, "encoding", "") or ""
ascii_only = not encoding.lower().startswith("utf")
```

Note that the check we recommend here is against `sys.stdout.encoding`, not `sys.flags.utf8_mode`: only the former reports UTF-8 for all three options listed below.

| Invocation                              | `sys.flags.utf8_mode` | `sys.stdout.encoding` |
| :-------------------------------------- | :-------------------: | :-------------------: |
| `PYTHONIOENCODING=utf8`                 |          `0`          |        `utf-8`        |
| `python -X utf8`                        |          `1`          |        `utf-8`        |
| `sys.stdout.reconfigure(encoding=…)`    |          `0`          |        `utf-8`        |

Do not rely on `sys.getfilesystemencoding()` on Windows either: [PEP 529](https://peps.python.org/pep-0529/) makes it `utf-8` regardless of the actual stream encoding.

(edit-wait)=
### The `edit` utility fails to open Visual Studio Code

Let's say our default editor is Visual Studio Code. A Click CLI calling `edit()` is supposed to open a new VSCode window on a temporary file then wait for us to edit that file before returning back the CLI execution.

But VSCode (and some other editors) returns immediately: the file is deleted before you had a chance to edit it. With `require_save=True` (the default), the function also returns `None` instead of the edited content.

This is not a bug in Click. In that particular case, the `code` command (VSCode's executable) is a launcher: it starts the real editor in the background, then exits. Click waits on that process and reads its exit as the end of the editing session. The same happens on any platform with any editor whose command returns before its window closes.

#### Answer

Setup your editor to make its launcher block until the window is closed, so Click keeps waiting on it.

You can set the `EDITOR` in your environment with its appropriate flags:

| Editor | Flags |
|---|---|
| Visual Studio Code | `EDITOR="code --wait"` |
| Sublime Text | `EDITOR="subl -w"` |

For an editor with no such flag, a workaround is to point `EDITOR` at a small wrapper script that opens the editor and blocks until it exits.

### Tab completion during interactive prompts

A command asks for a file path while it runs:

```python
import click


@click.command()
def convert():
    source = click.prompt("File to convert", type=click.Path(exists=True))
    click.echo(f"Converting {source}")
```

Pressing {kbd}`Tab` while typing the answer inserts a tab character instead of completing the path:

```console
$ convert
File to convert: Doc<TAB>
Error: Path 'Doc\t' does not exist.
```

This is not a bug in Click. Tab completion of the command line belongs to the shell: the shell asks the program for candidates through Click's completion mode, before any command code runs. A prompt works the other way around. The program already runs and reads the line itself, so Click never sees the {kbd}`Tab` key.

{func}`~click.prompt` reads that line with the built-in {func}`input`, and Click passes the whole prompt text to it as-is. This is where Python's {mod}`readline` module takes over, but nothing binds {kbd}`Tab` to completion by default.

#### Answer

Bind {kbd}`Tab` in `readline` and the prompt completes paths with no other change:

```python
import readline

if "libedit" in (readline.__doc__ or ""):
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")
```

See the {mod}`readline` documentation for the binding syntax, for the two libraries it can be built on, and for writing a completer of your own. The module is Unix-only, so the import fails on Windows.

Readline completes file names. It knows nothing about the parameter, so it cannot complete other values, such as the choices of a {class}`~click.Choice` parameter. Click embeds no line editor of its own: for completion of such values at a prompt, use one of the [interactive input libraries](contrib.md#interactive-input-libraries).

When the value does not have to be asked while the command runs, another option is to take it out of the prompt and put it on the command line, as an argument or an option:

```python
@click.command()
@click.argument("source", type=click.Path(exists=True))
def convert(source):
    click.echo(f"Converting {source}")
```

The shell completes paths there natively and Click's completion mode takes part in it (as described in [Shell Completion](shell-completion.md)).

(custom-completions-show-the-full-value)=
### Custom completions show the full value

`Path` and `File` parameters complete differently from a parameter with a custom completer. Take a command with one of each:

```python
def complete_dirs(ctx, param, incomplete):
    return [
        CompletionItem(incomplete + name)
        for name in ("Documents", "Downloads", "Pictures")
    ]


@click.command()
@click.option("--src", type=click.Path())
@click.option("--dest", shell_complete=complete_dirs)
def copy(src, dest):
    click.echo(f"Copy from {src} to {dest}")
```

Completing `--src` shows only the last component of each candidate, and omits the leading path:

```console
$ copy --src /home/user/<TAB><TAB>
Documents  Downloads  Pictures
```

Completing `--dest` shows each value in full, exactly as the completer returned it:

```console
$ copy --dest /home/user/<TAB><TAB>
/home/user/Documents  /home/user/Downloads  /home/user/Pictures
```

This is not a bug in Click. The two parameters are completed by different sides.

`Path.shell_complete` and `File.shell_complete` never enumerate the directory: each returns a single item that is the incomplete value itself, tagged `file` (or `dir` for a `Path` restricted to directories). Then the shell takes over to propose completions, and each shell does so in its own way.

A custom completer sends no such marker. Its `CompletionItem` carries the value, a `type` marker, and an optional `help` string. The value a completer returns is both what the shell displays and what it inserts into the command line.

#### Answer

To change how suggestions are displayed, work on the shell side:

- Check whether your shell's completion system has an option that changes how candidates are displayed.
- Write a `ShellComplete` subclass and register it with `add_completion_class`, as described in [Adding Support for a Shell](shell-completion.md#adding-support-for-a-shell).
- Or return the shortened form directly from your completer, but make the parameter accept and interpret that shortened form into the full value.

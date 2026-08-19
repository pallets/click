# Frequently Asked Questions

```{contents}
:depth: 2
:local: true
```

## General

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

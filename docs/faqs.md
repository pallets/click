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

(edit-wait)=
### The `edit` utility returns immediately

Let's say our default editor is Visual Studio Code. A Click CLI calling `edit()` is supposed to open a new VSCode window on a temporary file then wait for us to edit that file before returning back the CLI execution.

But some editors returns immediately and the file is deleted before you had a chance to edit it. With `require_save=True` (the default), the function also returns `None` instead of the edited content.

This is not a bug in Click. In that particular case, the `code` command (VSCode's executable) is a launcher: it starts the real editor in the background, then exits. Click waits on that process and reads its exit as the end of the editing session. The same happens on any platform with any editor whose command returns before its window closes.

#### Answer

Setup your editor to make its launcher block until the window is closed, so Click keeps waiting on it.

You can set the `EDITOR` in your environment with its appropriate flags:

| Editor | Flags |
|---|---|
| Visual Studio Code | `EDITOR="code --wait"` |
| Sublime Text | `EDITOR="subl -w"` |

For an editor with no such flag, a workaround is to point `EDITOR` at a small wrapper script that opens the editor and blocks until it exits.

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

### Shell Completion Display

When completing a path, my shell only shows the filename part instead of the
full path. Can Click do the same thing for custom completion values?

#### Answer

Click can mark file and path completion results specially. The shell's
completion system then decides how those paths are shown. Some shells shorten
path suggestions to the basename, while others may show them differently.

For custom completion values, Click sends the full completion value to the
shell. Display behavior such as showing only a basename is handled by the shell,
not by Click in a general way.

If you want different display behavior for a specific shell, write a custom
shell completer for that shell.

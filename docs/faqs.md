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

When completing file system paths, my shell can show only the matching file names while inserting the full path. Can
Click do the same for custom completions, such as showing only part of a comma-separated value?

#### Answer

Not in a shell-independent way. For file and path completions, Click returns a special completion item type that tells
the generated completion script to let the shell handle matching and display. The shell's own completion system then
decides whether to show a shorter path segment while inserting the full value.

For custom value completions, Click sends the completion value to the generated shell script. Different shells support
different completion metadata, so Click cannot generally tell the shell to display one string while inserting another.

Use {doc}`shell-completion` to customize which values Click returns with a `shell_complete` callback or a custom
`ParamType.shell_complete` method. If an application needs shell-specific display behavior, implement a custom shell
completion integration for that shell.

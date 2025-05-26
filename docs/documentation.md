# Help Pages

Click makes it very easy to document your command line tools. For most things Click automatically generates help pages
for you. By design the text is customizable, but the layout is not.

## Help Texts

Commands and options accept help arguments. For commands, the docstring of the function is automatically used if
provided.

Simple example:

```python
@click.command()
@click.argument('name')
@click.option('--count', default=1, help='number of greetings')
def hello(name: str, count: int):
    """This script prints hello and a name one or more times."""
    for x in range(count):
        if name:
            click.echo(f"Hello {name}!")
        else:
            click.echo("Hello!")
```

```console
$ hello --help
Usage: hello [OPTIONS] NAME

  This script prints hello and a name one or more times.

Options:
  --count INTEGER  number of greetings
  --help           Show this message and exit.
```

## Command Short Help

For subcommands, a short help snippet is generated. By default, it's the first sentence of the docstring. If too long,
then it will ellipsize what cannot be fit on a single line with `...`. The short help snippet can also be overridden
with `short_help`:

```python
@click.group()
def cli():
    """A simple command line tool."""

@cli.command('init', short_help='init the repo')
def init():
    """Initializes the repository."""
```

```console
$ cli --help
Usage: cli [OPTIONS] COMMAND [ARGS]...

  A simple command line tool.

Options:
  --help  Show this message and exit.

Commands:
  init  init the repo
```

## Command Epilog Help

The help epilog is printed at the end of the help and is useful for showing example command usages or referencing
additional help resources.

```python
@click.command(
    epilog='See https://example.com for more details',
    )
def init():
    """Initializes the repository."""

```

```console
$ init --help
Usage: init [OPTIONS]

  Initializes the repository.

Options:
  --help  Show this message and exit.

  See https://example.com for more details
```

(documenting-arguments)=

## Documenting Arguments

{func}`click.click.argument` does not take a `help` parameter. This follows the Unix Command Line Tools convention of using
arguments only for necessary things and documenting them in the command help text by name. This should then be done via
the docstring.

A brief example:

```python
@click.command()
@click.argument('filename')
def touch(filename):
    """Print FILENAME."""
    click.echo(filename)
```

```console
$ touch --help
Usage: touch [OPTIONS] FILENAME

  Print FILENAME.

Options:
  --help  Show this message and exit.
```

Or more explicitly:

```python
@click.command()
@click.argument('filename')
def touch(filename):
    """Print FILENAME.

    FILENAME is the name of the file to check.
    """
    click.echo(filename)
```

```console
$ touch --help
Usage: touch [OPTIONS] FILENAME

  Print FILENAME.

  FILENAME is the name of the file to check.

Options:
  --help  Show this message and exit.
```

## Showing Defaults

To control the appearance of defaults pass `show_default`.

```python
@click.command()
@click.option('--n', default=1, show_default=False, help='number of dots')
def dots(n):
    click.echo('.' * n)
```


```console
$ dots --help
Usage: dots [OPTIONS]

Options:
  --n INTEGER  number of dots
  --help       Show this message and exit.
```

For single option boolean flags, the default remains hidden if the default value is False even if show default is true.

```python
@click.command()
@click.option('--n', default=1, show_default=True)
@click.option("--gr", is_flag=True, show_default=True, default=False, help="Greet the world.")
@click.option("--br", is_flag=True, show_default=True, default=True, help="Add a thematic break")
def dots(n, gr, br):
    if gr:
        click.echo('Hello world!')
    click.echo('.' * n)
    if br:
        click.echo('-' * n)
```

```console
$ dots --help
Usage: dots [OPTIONS]

Options:
  --n INTEGER  [default: 1]
  --gr         Greet the world.
  --br         Add a thematic break  [default: True]
  --help       Show this message and exit.
```

## Click's Wrapping Behavior

Click's default wrapping ignores single new lines and rewraps the text based on the width of the terminal, to a maximum
of 80 characters. In the example notice how the second grouping of three lines is rewrapped into a single paragraph.

```python
@click.command()
def cli():
    """
    This is a very long paragraph and as you
    can see wrapped very early in the source text
    but will be rewrapped to the terminal width in
    the final output.

    This is
    a paragraph
    that is compacted.
    """
```

```console
$ cli --help
Usage: cli [OPTIONS]

  This is a very long paragraph and as you can see wrapped very early in the
  source text but will be rewrapped to the terminal width in the final output.

  This is a paragraph that is compacted.

Options:
  --help  Show this message and exit.
```

## Escaping Click's Wrapping

Sometimes Click's wrapping can be a problem, such as when showing code examples where newlines are significant. This
behavior can be escaped on a per-paragraph basis by adding a line with only `\b` . The `\b` is removed from the rendered
help text.

Example:

```python
@click.command()
def cli():
    """First paragraph.

    \b
    This is
    a paragraph
    without rewrapping.

    And this is a paragraph
    that will be rewrapped again.
        And this is a paragraph
    that will be rewrapped again.
    """
```

```console
$ cli --help
Usage: cli [OPTIONS]

  First paragraph.

  This is
  a paragraph
  without rewrapping.

  And this is a paragraph that will be rewrapped again.

Options:
  --help  Show this message and exit.
```

To change the rendering maximum width, pass `max_content_width` when calling the command.

```python
cli(max_content_width=120)
```

(doc-meta-variables)=

## Truncating Help Texts

Click gets {func}`click.Command` help text from the docstring. If you do not want to include part of the docstring, add the
`\f` escape marker to have Click truncate the help text after the marker.

Example:

```python
@click.command()
def cli():
    """First paragraph.
    \f

    Words to not be included.
    """
```

```console
$ cli --help
Usage: cli [OPTIONS]

  First paragraph.

Options:
  --help  Show this message and exit.
```

## Placeholder / Meta Variable

The default placeholder variable
([meta variable](https://en.wikipedia.org/wiki/Metasyntactic_variable#IETF_Requests_for_Comments)) in the help pages is
the parameter name in uppercase with underscores. This can be changed for Commands and Parameters with the
`options_metavar` and `metavar` kwargs.

```python
# This controls entry on the usage line.
@click.command(options_metavar='[[options]]')
@click.option('--count', default=1, help='number of greetings',
              metavar='<int>')
@click.argument('name', metavar='<name>')
def hello(name: str, count: int) -> None:
    """This script prints 'hello <name>' a total of <count> times."""
    for x in range(count):
        click.echo(f"Hello {name}!")
```

Example:

```console
$ hello --help
Usage: hello [[options]] <name>

  This script prints 'hello <name>' a total of <count> times.

Options:
  --count <int>  number of greetings
  --help         Show this message and exit.
```

## Help Parameter Customization

Help parameters are automatically added by Click for any command. The default is `--help` but can be override by the
context setting {func}`click.Context.help_option_names`. Click also performs automatic conflict resolution on the default
help parameter so if a command itself implements a parameter named `help` then the default help will not be run.

This example changes the default parameters to `-h` and `--help` instead of just `--help`:

```python
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
def cli():
    pass
```

```console
$ cli -h
Usage: cli [OPTIONS]

Options:
  -h, --help  Show this message and exit.
```

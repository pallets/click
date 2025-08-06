# Help Pages

```{currentmodule} click
```

Click makes it very easy to document your command line tools. For most things Click automatically generates help pages for you. By design the text is customizable, but the layout is not.

## Help Texts

Commands and options accept help arguments. For commands, the docstring of the function is automatically used if provided.

Simple example:

```{eval-rst}
.. click:example::

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

.. click:run::
    invoke(hello, args=['--help'])
```

## Command Short Help

For subcommands, a short help snippet is generated. By default, it's the first sentence of the docstring. If too long, then it will ellipsize what cannot be fit on a single line with `...`. The short help snippet can also be overridden with `short_help`:

```{eval-rst}
.. click:example::

    import click

    @click.group()
    def cli():
        """A simple command line tool."""

    @cli.command('init', short_help='init the repo')
    def init():
        """Initializes the repository."""

.. click:run::
    invoke(cli, args=['--help'])
```

## Command Epilog Help

The help epilog is printed at the end of the help and is useful for showing example command usages or referencing additional help resources.

```{eval-rst}
.. click:example::

    import click

    @click.command(
        epilog='See https://example.com for more details',
        )
    def init():
        """Initializes the repository."""

.. click:run::
    invoke(init, args=['--help'])
```

(documenting-arguments)=

## Documenting Arguments

{class}`click.argument` does not take a `help` parameter. This follows the Unix Command Line Tools convention of using arguments only for necessary things and documenting them in the command help text
by name. This should then be done via the docstring.

A brief example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

.. click:run::
    invoke(touch, args=['--help'])
```

Or more explicitly:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME.

        FILENAME is the name of the file to check.
        """
        click.echo(filename)

.. click:run::
    invoke(touch, args=['--help'])
```

## Showing Defaults

To control the appearance of defaults pass `show_default`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1, show_default=False, help='number of dots')
    def dots(n):
        click.echo('.' * n)

.. click:run::
    invoke(dots, args=['--help'])
```

For single option boolean flags, the default remains hidden if the default value is False, even if show default is set to true.

```{eval-rst}
.. click:example::

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

.. click:run::
   invoke(dots, args=['--help'])
```

## Click's Wrapping Behavior

Click's default wrapping ignores single new lines and rewraps the text based on the width of the terminal, to a maximum of 80 characters. In the example notice how the second grouping of three lines is rewrapped into a single paragraph.

```{eval-rst}
.. click:example::

    import click

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

.. click:run::
    invoke(cli, args=['--help'])
```

## Escaping Click's Wrapping

Sometimes Click's wrapping can be a problem, such as when showing code examples where new lines are significant. This behavior can be escaped on a per-paragraph basis by adding a line with only `\b` . The `\b` is removed from the rendered help text.

Example:

```{eval-rst}
.. click:example::

    import click

    @click.command()
    def cli():
        """First paragraph.

        \b
        This is
        a paragraph
        without rewrapping.

        And this is a paragraph
        that will be rewrapped again.
        """

.. click:run::
    invoke(cli, args=['--help'])
```

To change the rendering maximum width, pass `max_content_width` when calling the command.

```bash
cli(max_content_width=120)
```

## Truncating Help Texts

Click gets {class}`Command` help text from the docstring. If you do not want to include part of the docstring, add the `\f` escape marker to have Click truncate the help text after the marker.

Example:

```{eval-rst}
.. click:example::

    import click

    @click.command()
    def cli():
        """First paragraph.
        \f

        Words to not be included.
        """

.. click:run::
    invoke(cli, args=['--help'])
```

(doc-meta-variables)=

## Placeholder / Meta Variable

The default placeholder variable ([meta variable](https://en.wikipedia.org/wiki/Metasyntactic_variable#IETF_Requests_for_Comments)) in the help pages is the parameter name in uppercase with underscores. This can be changed for Commands and Parameters with the `options_metavar` and `metavar` kwargs.

```{eval-rst}
.. click:example::

    # This controls entry on the usage line.
    @click.command(options_metavar='[[options]]')
    @click.option('--count', default=1, help='number of greetings',
                  metavar='<int>')
    @click.argument('name', metavar='<name>')
    def hello(name: str, count: int) -> None:
        """This script prints 'hello <name>' a total of <count> times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

# Example usage:

.. click:run::
    invoke(hello, args=['--help'])

```

## Help Parameter Customization

Help parameters are automatically added by Click for any command. The default is `--help` but can be overridden by the context setting {attr}`~Context.help_option_names`. Click also performs automatic conflict resolution on the default help parameter, so if a command itself implements a parameter named `help` then the default help will not be run.

This example changes the default parameters to `-h` and `--help`
instead of just `--help`:

```{eval-rst}
.. click:example::

    import click

    CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

    @click.command(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

.. click:run::
    invoke(cli, ['-h'])
```

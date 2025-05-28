(parameters)=

# Parameters

```{eval-rst}
.. currentmodule:: click
```

Click supports only two principle types of parameters for scripts (by design): options and arguments.

## Options

- Are optional.
- Recommended to use for everything except subcommands, urls, or files.
- Can take a fixed number of arguments. The default is 1. They may be specified multiple times using {ref}`multiple-options`.
- Are fully documented by the help page.
- Have automatic prompting for missing input.
- Can act as flags (boolean or otherwise).
- Can be pulled from environment variables.

## Arguments

- Are optional with in reason, but not entirely so.
- Recommended to use for subcommands, urls, or files.
- Can take an arbitrary number of arguments.
- Are not fully documented by the help page since they may be too specific to be automatically documented. For more see {ref}`documenting-arguments`.
- Can be pulled from environment variables but only explicitly named ones. For more see {ref}`environment-variables`.

On each principle type you can specify {ref}`parameter-types`. Specifying these types helps Click add details to your help pages and help with the handling of those types.

(parameter-names)=

## Parameter Names

Parameters (options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

In the example, the argument's name is `filename`. The name must match the python arg name. To provide a different name for use in help text, see {ref}`doc-meta-variables`.
The option's names are `-t` and `--times`. More names are available for options and are covered in {ref}`options`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    @click.option('-t', '--times', type=int)
    def multi_echo(filename, times):
        """Print value filename multiple times."""
        for x in range(times):
            click.echo(filename)

.. click:run::

    invoke(multi_echo, ['--times=3', 'index.txt'], prog_name='multi_echo')
```

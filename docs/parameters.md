(parameters)=

# Parameters

```{currentmodule} click
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

- Are optional within reason, but not entirely so.
- Recommended to use for subcommands, urls, or files.
- Can take an arbitrary number of arguments.
- Are not fully documented by the help page since they may be too specific to be automatically documented. For more see {ref}`documenting-arguments`.
- Can be pulled from environment variables but only explicitly named ones. For more see {ref}`environment-variables`.

On each principle type you can specify {ref}`parameter-types`. Specifying these types helps Click add details to your help pages and help with the handling of those types.

(parameter-names)=

## Parameter Names

Three distinct strings designate a parameter, and each one has its own audience:

- `decls` are the declarations you pass to the decorator. Click parses them to derive every other string in this section.
- `spec` is what the user reads in `--help` and types on the command line. Read it from {attr}`Parameter.spec`, or from {meth}`Parameter.get_help_spec` for the longer form the help page lays out in its left column.
- `name` is what Click uses internally to identify the parameter. It is used as a Python argument and is passed to the decorated function. Read it from {attr}`Parameter.name`.

Click also keeps the parsed declarations on the parameter. {attr}`Parameter.opts` holds every spelling an option answers to, and {attr}`Parameter.secondary_opts` the ones that set a boolean flag to false.

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('recipe')
    @click.option('-g', '--gluten-free/--no-gluten-free', default=False)
    def bake(recipe, gluten_free):
        """Bake the RECIPE, with or without gluten."""
        note = 'no gluten' if gluten_free else 'with gluten'
        click.echo(f'{recipe}: {note}')

.. click:run::

    invoke(bake, ['--gluten-free', 'brioche'], prog_name='bake')


.. click:run::

    invoke(bake, ['--help'], prog_name='bake')
```

The example holds one argument and one option. The table lists all five strings for each of them:

| | `@click.argument('recipe')` | `@click.option('-g', '--gluten-free/--no-gluten-free')` |
|---|---|---|
| `decls` | `('recipe',)` | `('-g', '--gluten-free/--no-gluten-free')` |
| `spec` | `RECIPE` | `--gluten-free` |
| `name` | `recipe` | `gluten_free` |
| `opts` | `['recipe']` | `['-g', '--gluten-free']` |
| `secondary_opts` | `[]` | `['--no-gluten-free']` |

Click derives an option's `name` from the declaration with the longest prefix, so it picks `--gluten-free` over `-g`. It then lowercases that declaration and replaces its dashes with underscores, which gives `gluten_free`. The name must match the Python argument name of the decorated function. More declarations are available for options and are covered in {ref}`options`.

An argument has a single declaration. It becomes the only entry in `opts`, and `name` is that declaration lowercased, with dashes replaced by underscores. The `spec` is the name in upper case. `secondary_opts` stays empty, since the parser binds an argument by name and never matches a spelling. To choose the spec an argument shows in help text, see {ref}`doc-meta-variables`.

The help page above shows each `spec` where the user reads it: `RECIPE` in the usage line, and `-g, --gluten-free / --no-gluten-free` in the left column of the options list, which is the longer form {meth}`Parameter.get_help_spec` returns.

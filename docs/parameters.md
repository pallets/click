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

Click derives an option's `name` from the declaration with the longest prefix, so it picks `--gluten-free` over `-g`. It then lowercases that declaration and replaces its dashes with underscores, which gives `gluten_free`. The name must match the Python argument name of the decorated function. More declarations are available for options and are covered in {ref}`option names <option-names>`.

An argument has a single declaration. It becomes the only entry in `opts`, and `name` is that declaration lowercased, with dashes replaced by underscores. The `spec` is the name in upper case. `secondary_opts` stays empty, since the parser binds an argument by name and never matches a spelling. To choose the spec an argument shows in help text, see {ref}`doc-meta-variables`.

The help page above shows each `spec` where the user reads it: `RECIPE` in the usage line, and `-g, --gluten-free / --no-gluten-free` in the left column of the options list, which is the longer form {meth}`Parameter.get_help_spec` returns.

(name-transform)=

Both kinds derive that name the same way. An option drops its prefix first, and
only the leading one or two dashes are ever a prefix. From there every `-`
becomes a `_`, wherever it sits, and the result is lower cased.
It must then be a name a callback can declare, so that it can receive the value
as a keyword argument: an identifier, and not a reserved keyword. {exc}`TypeError`
is raised when it is neither.

```{eval-rst}
.. list-table:: Examples
    :widths: 20 20 15
    :header-rows: 1

    * - Argument Declaration
      - Option Declaration
      - Inferred Name
    * - ``"foo-bar"``
      - ``"--foo-bar"``
      - foo_bar
    * - ``"Foo-Bar"``
      - ``"--Foo-Bar"``
      - foo_bar
    * - ``"Foo_Bar"``
      - ``"--Foo_Bar"``
      - foo_bar
    * - ``"x"``
      - ``"-x"``
      - x
    * - ``"CamelCase"``
      - ``"--CamelCase"``
      - camelcase
    * - ``"café"``
      - ``"--café"``
      - café
    * - ``"ΟΔΟΣ"``
      - ``"--ΟΔΟΣ"``
      - οδος
    * - ``"\N{KELVIN SIGN}"``
      - ``"--\N{KELVIN SIGN}"``
      - k
    * - ``"foo-٣"``
      - ``"--foo-٣"``
      - foo_٣
    * - ``"a-----b"``
      - ``"--a-----b"``
      - a_____b
    * - ``"a--"``
      - ``"--a--"``
      - a__
    * - ``"-a----b--"``
      - ``"---a----b--"``
      - _a____b__
    * - ``"--"``
      - ``"----"``
      - __
    * - ``"match"``
      - ``"--match"``
      - match
    * - ``"type"``
      - ``"--type"``
      - type
    * - ``"True"``
      - ``"--True"``
      - true
    * - ``"None"``
      - ``"--None"``
      - none
    * - ``"0-file"``
      - ``"--0-file"``
      - :exc:`TypeError`
    * - ``"٣foo"``
      - ``"--٣foo"``
      - :exc:`TypeError`
    * - ``"foo.bar"``
      - ``"--foo.bar"``
      - :exc:`TypeError`
    * - ``"foo\N{NON-BREAKING HYPHEN}bar"``
      - ``"--foo\N{NON-BREAKING HYPHEN}bar"``
      - :exc:`TypeError`
    * - ``"a\N{ZERO WIDTH SPACE}b"``
      - ``"--a\N{ZERO WIDTH SPACE}b"``
      - :exc:`TypeError`
    * - ``""``
      - ``"--"``
      - :exc:`TypeError`
    * - ``"from"``
      - ``"--from"``
      - :exc:`TypeError`
    * - ``"From"``
      - ``"--From"``
      - :exc:`TypeError`
```

The transform is many-to-one and not reversible: the three spellings of
`foo-bar` above all name one parameter. Which declaration is transformed in the
first place is the only thing that differs between the two kinds, covered in
{ref}`option names <option-names>` and {ref}`argument names <argument-names>`.

(keyword-names)=

```{caution}
A [reserved keyword](https://docs.python.org/3/reference/lexical_analysis.html#keywords)
satisfies {meth}`str.isidentifier`, so a rule of its own refuses it: no callback
can declare a parameter called `from`, so `click.option("--from")` raises
{exc}`TypeError`.

Pass an explicit name instead: `click.option("--from", "source")`. An argument
takes one declaration and has no explicit-name channel, so rename the
declaration there and pass `metavar` to keep its old display:
`click.argument("source", metavar="FROM")`.
```

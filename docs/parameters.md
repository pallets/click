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

Parameters (options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

In the example, the argument's name is `filename`. The name must match the python arg name. To provide a different name for use in help text, see {ref}`doc-meta-variables`.
The option's names are `-t` and `--times`. More names are available for options and are covered in {ref}`option names <option-names>`.

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

(name-transform)=

Both kinds derive that name the same way. An option drops its prefix first, and
only the leading one or two dashes are ever a prefix. From there every `-`
becomes a `_`, wherever it sits, and the result is lower cased.
It must then satisfy {meth}`str.isidentifier`, so that the callback can receive
it as a keyword argument, and {exc}`TypeError` is raised when it does not.

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
```

The transform is many-to-one and not reversible: the three spellings of
`foo-bar` above all name one parameter. Which declaration is transformed in the
first place is the only thing that differs between the two kinds, covered in
{ref}`option names <option-names>` and {ref}`argument names <argument-names>`.

(keyword-names)=

```{caution}
A [reserved keyword](https://docs.python.org/3/reference/lexical_analysis.html#keywords)
satisfies {meth}`str.isidentifier`, so Click accepts one: `click.option("--from")`
names its parameter `from`. No callback can declare that, so the command has to
accept `**kwargs`, and Python then stops checking the callback signature at all.

Pass an explicit name instead: `click.option("--from", "source")`. An argument
takes one declaration and has no explicit-name channel, so rename the
declaration there.
```

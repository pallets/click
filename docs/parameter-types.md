(parameter-types)=

# Parameter Types

```{currentmodule} click
```

When the parameter type is set using `type`, Click will leverage the type to make your life easier, for example adding
data to your help pages. Most examples are done with options, but types are available to options and arguments.

```{contents}
---
depth: 2
local: true
---
```

## Built-in Types Examples

(choice-opts)=

### Choice

Sometimes, you want to have a parameter be a choice of a list of values. In that case you can use {class}`Choice` type.
It can be instantiated with a list of valid values. The originally passed choice will be returned, not the str passed on
the command line. Token normalization functions and `case_sensitive=False` can cause the two to be different but still
match. {meth}`Choice.normalize_choice` for more info.


Example:

```{eval-rst}
.. click:example::

    import enum

    class HashType(enum.Enum):
        MD5 = enum.auto()
        SHA1 = enum.auto()

    @click.command()
    @click.option('--hash-type',
                  type=click.Choice(HashType, case_sensitive=False))
    def digest(hash_type: HashType):
        click.echo(hash_type)

What it looks like:

.. click:run::

    invoke(digest, args=['--hash-type=MD5'])
    println()
    invoke(digest, args=['--hash-type=md5'])
    println()
    invoke(digest, args=['--hash-type=foo'])
    println()
    invoke(digest, args=['--help'])
```

Any iterable may be passed to {class}`Choice`. If an `Enum` is passed, the names of the enum members will be used as
valid choices.

Choices work with options that have `multiple=True`. If a `default` value is given with `multiple=True`, it should be a
list or tuple of valid choices.

Choices should be unique after normalization, see {meth}`Choice.normalize_choice` for more info.

```{versionchanged} 7.1
The resulting value from an option will always be one of the originally passed choices
regardless of `case_sensitive`.
```

```{versionchanged} 8.4.0
{class}`Choice` is now generic. Parameterize it with the choice value type
({class}`!Choice[HashType]` for an enum, {class}`!Choice[str]` for plain
strings) to enable type-checked consumers.
```

(ranges)=

### Int and Float Ranges

The {class}`IntRange` type extends the {data}`INT` type to ensure the value is contained in the given range. The
{class}`FloatRange` type does the same for {data}`FLOAT`.

If `min` or `max` is omitted, that side is *unbounded*. Any value in that direction is accepted. By default, both bounds
are *closed*, which means the boundary value is included in the accepted range. `min_open` and `max_open` can be used to
exclude that boundary from the range.

If `clamp` mode is enabled, a value that is outside the range is set to the boundary instead of failing. For example,
the range `0, 5` would return `5` for the value `10`, or `0` for the value `-1`. When using {class}`FloatRange`, `clamp`
can only be enabled if both bounds are *closed* (the default).

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("--count", type=click.IntRange(0, 20, clamp=True))
    @click.option("--digit", type=click.IntRange(0, 9))
    def repeat(count, digit):
        click.echo(str(digit) * count)

.. click:run::

    invoke(repeat, args=['--count=100', '--digit=5'])
    invoke(repeat, args=['--count=6', '--digit=12'])
```

## Built-in Types Listing

The supported parameter {ref}`click-api-types` are

- `str` / {data}`click.STRING`: The default parameter type which indicates unicode strings.

- `int` / {data}`click.INT`: A parameter that only accepts integers.

- `float` / {data}`click.FLOAT`: A parameter that only accepts floating point values.

- `bool` / {data}`click.BOOL`: A parameter that accepts boolean values. This is automatically used for boolean flags.
  The string values "1", "true", "t", "yes", "y", and "on" convert to `True`. "0", "false", "f", "no", "n", and "off"
  convert to `False`.

- {data}`click.UUID`: A parameter that accepts UUID values. This is not automatically guessed but represented as
  {class}`uuid.UUID`.

```{eval-rst}
*   .. autoclass:: Choice
       :noindex:
```

```{eval-rst}
*   .. autoclass:: DateTime
       :noindex:
```

```{eval-rst}
*   .. autoclass:: File
       :noindex:
```

```{eval-rst}
*   .. autoclass:: FloatRange
       :noindex:
```

```{eval-rst}
*   .. autoclass:: IntRange
       :noindex:
```

```{eval-rst}
*   .. autoclass:: Path
       :noindex:
```

(type-inference)=

## How Click Infers a Type

When `type` is not given, Click infers it from `default`. Only the defaults listed below
are recognized. Every other default gives {data}`STRING`.

| `default`                                        | Inferred type                                   |
| ------------------------------------------------ | ----------------------------------------------- |
| not given, or `None`                             | {data}`STRING`                                  |
| `"git"`                                          | {data}`STRING`                                  |
| `5`                                              | {data}`INT`                                     |
| `1.5`                                            | {data}`FLOAT`                                   |
| `True`                                           | {data}`BOOL`                                    |
| `[]` or `()`                                     | {data}`STRING`                                  |
| `[1, 2]` or `(1, 2)`                             | {data}`INT`                                     |
| `[1.5, 2.5]`                                     | {data}`FLOAT`                                   |
| `[1, "git"]`                                     | {data}`INT`                                     |
| `[(1, "git")]`                                   | {class}`Tuple` of ({data}`INT`, {data}`STRING`) |
| `{1, 2}` or `frozenset({1, 2})`                  | {data}`STRING`                                  |
| `{"a": 1}`                                       | {data}`STRING`                                  |
| {class}`uuid.UUID` or {class}`datetime.datetime` | {data}`STRING`                                  |
| `b"git"`, or any other object                    | {data}`STRING`                                  |

A `list` or `tuple` gives the type of its **first item only**, so `[1, "git"]` gives
{data}`INT` and the second item is converted with it. A first item that is itself a
`list` or `tuple` gives a {class}`Tuple`, which also sets `nargs`.

A `set`, a `frozenset`, a `dict`, and a type Click ships but does not guess, such as
{class}`uuid.UUID`, all land in the last group. Their default is converted with
{data}`STRING`, so the command receives the `str()` form of the value.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--count', default=5)
    @click.option('--tag', default={'git'})
    def show(count, tag):
        click.echo(f"count is {type(count).__name__}, tag is {type(tag).__name__}")

.. click:run::

    invoke(show, args=[])
```

When `type` is given a callable Click does not recognize, that callable is called on the
string coming from the command line, and a `ValueError` it raises is reported as a bad
parameter. A container is rarely useful there, because calling it on a string splits the
string: `set` turns `"git"` into `{"g", "i", "t"}`. Pass a {class}`ParamType` instead,
as described in [](#how-to-implement-custom-types).

## How to Implement Custom Types

To implement a custom type, you need to subclass the {class}`ParamType` class. For simple cases, passing a Python
function that fails with a `ValueError` is also supported, though discouraged. Override the {meth}`~ParamType.convert`
method to convert the value from a string to the correct type.

{class}`ParamType` is generic in the converted value type: parameterize it with
the type returned by `convert` so that consumers (and type checkers) can rely
on the narrowed return type.

The following code implements an integer type that accepts hex and octal numbers in addition to normal integers, and
converts them into regular integers.

```python
import click


class BasedIntParamType(click.ParamType[int]):
    name = "integer"

    def convert(self, value, param, ctx) -> int:
        if isinstance(value, int):
            return value

        try:
            if value[:2].lower() == "0x":
                return int(value[2:], 16)
            elif value[:1] == "0":
                return int(value, 8)
            return int(value, 10)
        except ValueError:
            self.fail(f"{value!r} is not a valid integer", param, ctx)


BASED_INT = BasedIntParamType()
```

The {attr}`~ParamType.name` attribute is optional and is used for documentation. Call {meth}`~ParamType.fail` if
conversion fails. The `param` and `ctx` arguments may be `None` in some cases such as prompts.

Values from user input or the command line will be strings, but default values and Python arguments may already be the
correct type. The custom type should check at the top if the value is already valid and pass it through to support those
cases.

```{versionchanged} 8.4.0
{class}`ParamType` is now a generic abstract base class. Parameterize it with
the converted value type ({class}`!ParamType[int]` for an integer-returning
type) so that {meth}`~ParamType.convert` and downstream consumers carry the
narrowed type.
```

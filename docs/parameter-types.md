(parameter-types)=

# Parameter Types

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

Sometimes, you want to have a parameter be a choice of a list of values. In that case you can use {func}`click.Choice` type.
It can be instantiated with a list of valid values. The originally passed choice will be returned, not the str passed on
the command line. Token normalization functions and `case_sensitive=False` can cause the two to be different but still
match. {meth}`Choice.normalize_choice` for more info.

Example:

```python
import enum

class HashType(enum.Enum):
    MD5 = enum.auto()
    SHA1 = enum.auto()

@click.command()
@click.option('--hash-type',
              type=click.Choice(HashType, case_sensitive=False))
def digest(hash_type: HashType):
    click.echo(hash_type)
```

What it looks like:

```console
$ digest --hash-type=MD5
HashType.MD5

$ digest --hash-type=md5
HashType.MD5

$ digest --hash-type=foo
Usage: digest [OPTIONS]
Try 'digest --help' for help.

Error: Invalid value for '--hash-type': 'foo' is not one of 'md5', 'sha1'.

$ digest --help
Usage: digest [OPTIONS]

Options:
  --hash-type [md5|sha1]
  --help                  Show this message and exit.
```

Any iterable may be passed to {func}`click.Choice`. If an `Enum` is passed, the names of the enum members will be used as
valid choices.

Choices work with options that have `multiple=True`. If a `default` value is given with `multiple=True`, it should be a
list or tuple of valid choices.

Choices should be unique after normalization, see {meth}`Choice.normalize_choice` for more info.

:::{versionchanged} 7.1
The resulting value from an option will always be one of the originally passed choices
regardless of `case_sensitive`.
:::

(ranges)=

### Int and Float Ranges

The {func}`click.IntRange` type extends the {data}`INT` type to ensure the value is contained in the given range. The
{func}`click.FloatRange` type does the same for {data}`FLOAT`.

If `min` or `max` is omitted, that side is *unbounded*. Any value in that direction is accepted. By default, both bounds
are *closed*, which means the boundary value is included in the accepted range. `min_open` and `max_open` can be used to
exclude that boundary from the range.

If `clamp` mode is enabled, a value that is outside the range is set to the boundary instead of failing. For example,
the range `0, 5` would return `5` for the value `10`, or `0` for the value `-1`. When using {func}`click.FloatRange`, `clamp`
can only be enabled if both bounds are *closed* (the default).

```python
@click.command()
@click.option("--count", type=click.IntRange(0, 20, clamp=True))
@click.option("--digit", type=click.IntRange(0, 9))
def repeat(count, digit):
    click.echo(str(digit) * count)
```

```console
$ repeat --count=100 --digit=5
55555555555555555555

$ repeat --count=6 --digit=12
Usage: repeat [OPTIONS]
Try 'repeat --help' for help.

Error: Invalid value for '--digit': 12 is not in the range 0<=x<=9.
```

## Built-in Types Listing

The supported parameter {ref}`click-api-types` are:

- `str` / {data}`click.STRING`: The default parameter type which indicates unicode strings.
- `int` / {data}`click.INT`: A parameter that only accepts integers.
- `float` / {data}`click.FLOAT`: A parameter that only accepts floating point values.
- `bool` / {data}`click.BOOL`: A parameter that accepts boolean values. This is automatically used for boolean flags.
  The string values "1", "true", "t", "yes", "y", and "on" convert to `True`. "0", "false", "f", "no", "n", and "off"
  convert to `False`.
- {data}`click.UUID`: A parameter that accepts UUID values. This is not automatically guessed but represented as
  {func}`click.uuid.UUID`.
- {data}`click.types.Choice`
- {data}`click.types.DateTime`
- {data}`click.types.File`
- {data}`click.types.FloatRange`
- {data}`click.types.IntRange`
- {data}`click.types.Path`

## How to Implement Custom Types

To implement a custom type, you need to subclass the {func}`click.ParamType` class. For simple cases, passing a Python
function that fails with a `ValueError` is also supported, though discouraged. Override the {meth}`~ParamType.convert`
method to convert the value from a string to the correct type.

The following code implements an integer type that accepts hex and octal numbers in addition to normal integers, and
converts them into regular integers.

```python
import click

class BasedIntParamType(click.ParamType):
    name = "integer"

    def convert(self, value, param, ctx):
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

The {func}`click.ParamType.name` attribute is optional and is used for documentation. Call {meth}`~ParamType.fail` if
conversion fails. The `param` and `ctx` arguments may be `None` in some cases such as prompts.

Values from user input or the command line will be strings, but default values and Python arguments may already be the
correct type. The custom type should check at the top if the value is already valid and pass it through to support those
cases.

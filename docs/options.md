(options)=

# Options

```{eval-rst}
.. currentmodule:: click
```

Adding options to commands can be accomplished with the {func}`option`
decorator. At runtime the decorator invokes the {class}`Option` class. Options in Click are distinct from {ref}`positional arguments <arguments>`.

Useful and often used kwargs are:

- `default`: Passes a default.
- `help`: Sets help message.
- `nargs`: Sets the number of arguments.
- `required`: Makes option required.
- `type`: Sets {ref}`parameter type <parameter-types>`

```{contents}
:depth: 2
:local: true
```

## Option Decorator

Click expects you to pass at least two positional arguments to the option decorator. They are option name and function argument name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo', 'string_to_echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)


.. click:run::

    invoke(echo, args=['--help'])
```

However, if you don't pass in the function argument name, then Click will try to infer it. A simple way to name your option is by taking the function argument, adding two dashes to the front and converting underscores to dashes. In this case, Click will infer the function argument name correctly so you can add only the option name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--string-to-echo', 'Hi!'])
```

More formally, Click will try to infer the function argument name by:

1. If a positional argument name does not have a prefix, it is chosen.
2. If a positional argument name starts with with two dashes, the first one given is chosen.
3. The first positional argument prefixed with one dash is chosen otherwise.

The chosen positional argument is converted to lower case, up to two dashes are removed from the beginning, and other dashes are converted to underscores to get the function argument name.

```{eval-rst}
.. list-table:: Examples
    :widths: 15 10
    :header-rows: 1

    * - Decorator Arguments
      - Function Name
    * - ``"-f", "--foo-bar"``
      - foo_bar
    * - ``"-x"``
      - x
    * - ``"-f", "--filename", "dest"``
      - dest
    * - ``"--CamelCase"``
      - camelcase
    * - ``"-f", "-fb"``
      - f
    * - ``"--f", "--foo-bar"``
      - f
    * - ``"---f"``
      - _f
```

## Basic Example

A simple {class}`click.Option` takes one argument. This will assume the argument is not required. If the decorated function takes an positional argument then None is passed it. This will also assume the type is `str`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--text')
    def print_this(text):
        click.echo(text)


.. click:run::

    invoke(print_this, args=['--text=this'])

    invoke(print_this, args=[])


.. click:run::

    invoke(print_this, args=['--help'])

```

## Setting a Default

Instead of setting the `type`, you may set a default and Click will try to infer the type.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

.. click:run::

    invoke(dots, args=['--help'])
```

## Multi Value Options

To make an option take multiple values, pass in `nargs`. Note you may pass in any positive integer, but not -1. The values are passed to the underlying function as a tuple.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        a, b = pos
        click.echo(f"{a} / {b}")

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])

```

(tuple-type)=

## Multi Value Options as Tuples

```{versionadded} 4.0
```

As you can see that by using `nargs` set to a specific number each item in
the resulting tuple is of the same type. This might not be what you want.
Commonly you might want to use different types for different indexes in
the tuple. For this you can directly specify a tuple as type:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', type=(str, int))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")


And on the command line:

.. click:run::

    invoke(putitem, args=['--item', 'peter', '1338'])
```

By using a tuple literal as type, `nargs` gets automatically set to the
length of the tuple and the {class}`click.Tuple` type is automatically
used. The above example is thus equivalent to this:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', nargs=2, type=click.Tuple([str, int]))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")
```

(multiple-options)=

## Multiple Options

The multiple options format allows options to take an arbitrary number of arguments (which is called variadic). The arguments are passed to the underlying function as a tuple. If set, the default must be a list or tuple. Setting a string as a default will be interpreted as list of characters.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo(message)
        for m in message:
            click.echo(m)

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar', '-m', 'here'])
```

## Counting

To count the occurrence of an option pass in `count=True`. If the option is not passed in, then the count is 0. Counting is commonly used for verbosity.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo(f"Verbosity: {verbose}")

.. click:run::

    invoke(log, args=[])
    invoke(log, args=['-vvv'])
```

(option-boolean-flag)=

## Boolean

Boolean options (boolean flags) take the value True or False. The simplest case sets the default value to `False` if the flag is not passed, and `True` if it is.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)


.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])

```

To implement this more explicitly, pass in on-option `/` off-option. Click will automatically set `is_flag=True`. Click always wants you to provide an enable
and disable flag so that you can change the default later.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])
    invoke(info, args=['--no-shout'])
```

If a forward slash(`/`) is contained in your option name already, you can split the parameters using `;`. In Windows `/` is commonly used as the prefix character.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")
```

```{versionchanged} 6.0
```

If you want to define an alias for the second option only, then you will need to use leading whitespace to disambiguate the format string.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', ' /-N', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info, args=['--help'])
```

## Flag Value

To have an flag pass a value to the underlying function set `flag_value`. This automatically sets `is_flag=True`. To mark the flag as default, set `default=True`. Setting flag values can be used to create patterns like this:

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper', default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(sys.platform, transformation)())

.. click:run::

    invoke(info, args=['--help'])
    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])
    invoke(info)
```

````{note}
The `default` value is given to the underlying function as-is. So if you set `default=None`, the value passed to the function is the `None` Python value. Same for any other type.

But there is a special case for flags. If a flag has a `flag_value`, then setting `default=True` is interpreted as *the flag should be activated by default*. So instead of the underlying function receiving the `True` Python value, it will receive the `flag_value`.

Which means, in example above, this option:

```python
@click.option('--upper', 'transformation', flag_value='upper', default=True)
```

is equivalent to:

```python
@click.option('--upper', 'transformation', flag_value='upper', default='upper')
```

Because the two are equivalent, it is recommended to always use the second form, and set `default` to the actual value you want to pass. And not use the special `True` case. This makes the code more explicit and predictable.
````

## Values from Environment Variables

To pass in a value in from a specific environment variable use `envvar`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})
```

If a list is passed to `envvar`, the first environment variable found is picked.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar=['ALT_USERNAME', 'USERNAME'])
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'ALT_USERNAME': 'Bill', 'USERNAME': 'john'})

```

Variable names are:
 - [Case-insensitive on Windows but not on other platforms](https://github.com/python/cpython/blob/aa9eb5f757ceff461e6e996f12c89e5d9b583b01/Lib/os.py#L777-L789).
 - Not stripped of whitespaces and should match the exact name provided to the `envvar` argument.

For flag options, there is two concepts to consider: the activation of the flag driven by the environment variable, and the value of the flag if it is activated.

The environment variable need to be interpreted, because values read from them are always strings. We need to transform these strings into boolean values that will determine if the flag is activated or not.

Here are the rules used to parse environment variable values for flag options:
   - `true`, `1`, `yes`, `on`, `t`, `y` are interpreted as activating the flag
   - `false`, `0`, `no`, `off`, `f`, `n` are interpreted as deactivating the flag
   - The presence of the environment variable without value is interpreted as deactivating the flag
   - Empty strings are interpreted as deactivating the flag
   - Values are case-insensitive, so the `True`, `TRUE`, `tRuE` strings are all activating the flag
   - Values are stripped of leading and trailing whitespaces before being interpreted, so the `" True "` string is transformed to `"true"` and so activates the flag
   - If the flag option has a `flag_value` argument, passing that value in the environment variable will activate the flag, in addition to all the cases described above
   - Any other value is interpreted as deactivating the flag

```{caution}
For boolean flags with a pair of values, the only recognized environment variable is the one provided to the `envvar` argument.

So an option defined as `--flag\--no-flag`, with a `envvar="FLAG"` parameter, there is no magical `NO_FLAG=<anything>` variable that is recognized. Only the `FLAG=<anything>` environment variable is recognized.
```

Once the status of the flag has been determine to be activated or not, the `flag_value` is used as the value of the flag if it is activated. If the flag is not activated, the value of the flag is set to `None` by default.

## Multiple Options from Environment Values

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex. The way
Click solves this is by leaving it up to the type to customize this
behavior. For both `multiple` and `nargs` with values other than
`1`, Click will invoke the {meth}`ParamType.split_envvar_value` method to
perform the splitting.

The default implementation for all types is to split on whitespace. The
exceptions to this rule are the {class}`File` and {class}`Path` types
which both split according to the operating system's path splitting rules.
On Unix systems like Linux and OS X, the splitting happens on
every colon (`:`), and for Windows, splitting on every semicolon (`;`).

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('paths', '--path', envvar='PATHS', multiple=True,
                  type=click.Path())
    def perform(paths):
        for path in paths:
            click.echo(path)

    if __name__ == '__main__':
        perform()

.. click:run::

    import os
    invoke(perform, env={"PATHS": f"./foo/bar{os.path.pathsep}./test"})
```

## Other Prefix Characters

Click can deal with prefix characters besides `-` for options. Click can use
`/`, `+` as well as others. Note that alternative prefix characters are generally used very sparingly if at all within POSIX.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo(f"writable={w}")

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])
```

There are special considerations for using `/` as prefix character, see {ref}`option-boolean-flag` for more.

(optional-value)=

## Optional Value

Providing the value to an option can be made optional, in which case
providing only the option's flag without a value will either show a
prompt or use its `flag_value`.

Setting `is_flag=False, flag_value=value` tells Click that the option
can still be passed a value, but if only the flag is given, the
value will be `flag_value`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

.. click:run::

    invoke(hello, args=[])
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"])
```

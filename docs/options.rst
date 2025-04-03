.. _options:

Options
=========

.. currentmodule:: click

Adding options to commands can be accomplished with the :func:`option`
decorator. At runtime the decorator invokes the :class:`Option` class. Options in Click are distinct from :ref:`positional arguments <arguments>`.

Useful and often used kwargs are:

*   ``default``: Passes a default.
*   ``help``: Sets help message.
*   ``nargs``: Sets the number of arguments.
*   ``required``: Makes option required.
*   ``type``: Sets :ref:`parameter type <parameter-types>`

.. contents::
   :depth: 2
   :local:

Option Decorator
-----------------
Click expects you to pass at least two positional arguments to the option decorator. They are option name and function argument name.

.. click:example::

    @click.command()
    @click.option('--string-to-echo', 'string_to_echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--help'])

However, if you don't pass in the function argument name, then Click will try to infer it. A simple way to name your option is by taking the function argument, adding two dashes to the front and converting underscores to dashes. In this case, Click will infer the function argument name correctly so you can add only the option name.

.. click:example::

    @click.command()
    @click.option('--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--string-to-echo', 'Hi!'])

More formally, Click will try to infer the function argument name by:

1.  If a positional argument name does not have a prefix, it is chosen.
2.  If a positional argument name starts with with two dashes, the first one given is chosen.
3.  The first positional argument prefixed with one dash is chosen otherwise.

The chosen positional argument is converted to lower case, up to two dashes are removed from the beginning, and other dashes are converted to underscores to get the function argument name.

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

Basic Example
---------------
A simple :class:`click.Option` takes one argument. This will assume the argument is not required. If the decorated function takes an positional argument then None is passed it. This will also assume the type is ``str``.

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


Setting a Default
---------------------------
Instead of setting the ``type``, you may set a default and Click will try to infer the type.

.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

.. click:run::

    invoke(dots, args=['--help'])

Multi Value Options
-------------------

To make an option take multiple values, pass in ``nargs``. Note only a fixed number of arguments is supported. The values are passed to the underlying function as a tuple.

.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        a, b = pos
        click.echo(f"{a} / {b}")

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])


.. _tuple-type:

Multi Value Options as Tuples
-----------------------------

.. versionadded:: 4.0

As you can see that by using `nargs` set to a specific number each item in
the resulting tuple is of the same type.  This might not be what you want.
Commonly you might want to use different types for different indexes in
the tuple.  For this you can directly specify a tuple as type:

.. click:example::

    @click.command()
    @click.option('--item', type=(str, int))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")

And on the command line:

.. click:run::

    invoke(putitem, args=['--item', 'peter', '1338'])

By using a tuple literal as type, `nargs` gets automatically set to the
length of the tuple and the :class:`click.Tuple` type is automatically
used.  The above example is thus equivalent to this:

.. click:example::

    @click.command()
    @click.option('--item', nargs=2, type=click.Tuple([str, int]))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")

.. _multiple-options:

Multiple Options
-----------------

The multiple options format allows you to call the underlying function multiple times with one command line entry. If set, the default must be a list or tuple. Setting a string as a default will be interpreted as list of characters.

.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo('\n'.join(message))

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar', '-m', 'here'])

Counting
--------
To count the occurrence of an option pass in ``count=True``. If the option is not passed in, then the count is 0. Counting is commonly used for verbosity.

.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo(f"Verbosity: {verbose}")

.. click:run::

    invoke(log, args=[])
    invoke(log, args=['-vvv'])

.. _option-boolean-flag:

Boolean
------------------------

Boolean options (boolean flags) take the value True or False. The simplest case sets the default value to ``False`` if the flag is not passed, and ``True`` if it is.

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


To implement this more explicitly, pass in on-option ``/`` off-option. Click will automatically set ``is_flag=True``. Click always wants you to provide an enable
and disable flag so that you can change the default later.

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

If a forward slash(``/``) is contained in your option name already, you can split the parameters using ``;``. In Windows ``/`` is commonly used as the prefix character.

.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")

.. versionchanged:: 6.0

If you want to define an alias for the second option only, then you will need to use leading whitespace to disambiguate the format string.

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

Flag Value
---------------
To have an flag pass a value to the underlying function set ``flag_value``. This automatically sets ``is_flag=True``. To set a default flag, set  ``default=True``. Setting flag values can be used to create patterns like this:

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

Values from Environment Variables
---------------------------------
To pass in a value in from a specific environment variable use ``envvar``.

.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})

If a list is passed to ``envvar``, the first environment variable found is picked.

.. click:example::

    @click.command()
    @click.option('--username', envvar=['ALT_USERNAME', 'USERNAME'])
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'ALT_USERNAME': 'Bill', 'USERNAME': 'john'})


Multiple Options from Environment Values
-----------------------------------------

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex.  The way
Click solves this is by leaving it up to the type to customize this
behavior.  For both ``multiple`` and ``nargs`` with values other than
``1``, Click will invoke the :meth:`ParamType.split_envvar_value` method to
perform the splitting.

The default implementation for all types is to split on whitespace.  The
exceptions to this rule are the :class:`File` and :class:`Path` types
which both split according to the operating system's path splitting rules.
On Unix systems like Linux and OS X, the splitting happens on
every colon (``:``), and for Windows, splitting on every semicolon (``;``).

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

Other Prefix Characters
-----------------------

Click can deal with prefix characters besides ``-`` for options.  Click can use
``/``, ``+`` as well as others. Note that alternative prefix characters are generally used very sparingly if at all within POSIX.

.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo(f"writable={w}")

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])

There are special considerations for using ``/`` as prefix character, see :ref:`option-boolean-flag` for more.

.. _optional-value:

Optional Value
--------------

Providing the value to an option can be made optional, in which case
providing only the option's flag without a value will either show a
prompt or use its ``flag_value``.

Setting ``is_flag=False, flag_value=value`` tells Click that the option
can still be passed a value, but only if the flag is given the
``flag_value``.

.. click:example::

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

.. click:run::

    invoke(hello, args=[])
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"])

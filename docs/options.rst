.. _options:

Options
=========

.. currentmodule:: click

Adding options to commands can be accomplished with the :func:`option`
decorator.  Options in Click are distinct from :ref:`positional arguments <arguments>`.

Useful and often used kwargs are:

*   ``default``: Passes a default.
*   ``help``: Sets help message.
*   ``nargs``: Sets the number of arguments.
*   ``required``: Makes option required.
*   ``type``: Sets :ref:`parameter-types`

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
To have an flag pass a value to the underlying function set ``is_flag=True`` and set ``flag_value`` to the value desired. This can be used to create patterns like this:

.. click:example::

    import sys

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper')
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(sys.platform, transformation)())

.. click:run::

    invoke(info, args=['--help'])
    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])

Feature Switches
---------------------------

In addition to boolean flags, there are also feature switches.  These are
implemented by setting multiple options to the same parameter name and
defining a flag value.  Note that by providing the ``flag_value`` parameter,
Click will implicitly set ``is_flag=True``.

To set a default flag, assign a value of `True` to the flag that should be
the default.

.. click:example::

    import sys

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper',
                  default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(sys.platform, transformation)())

.. click:run::

    invoke(info, args=['--upper'])
    invoke(info, args=['--help'])
    invoke(info)


.. _option-prompting:

Prompting
---------

In some cases, you want parameters that can be provided from the command line,
but if not provided, ask for user input instead.  This can be implemented with
Click by defining a prompt string.

Example:

.. click:example::

    @click.command()
    @click.option('--name', prompt=True)
    def hello(name):
        click.echo(f"Hello {name}!")

And what it looks like:

.. click:run::

    invoke(hello, args=['--name=John'])
    invoke(hello, input=['John'])

If you are not happy with the default prompt string, you can ask for
a different one:

.. click:example::

    @click.command()
    @click.option('--name', prompt='Your name please')
    def hello(name):
        click.echo(f"Hello {name}!")

What it looks like:

.. click:run::

    invoke(hello, input=['John'])

It is advised that prompt not be used in conjunction with the multiple
flag set to True. Instead, prompt in the function interactively.

By default, the user will be prompted for an input if one was not passed
through the command line. To turn this behavior off, see
:ref:`optional-value`.

Dynamic Defaults for Prompts
----------------------------

The ``auto_envvar_prefix`` and ``default_map`` options for the context
allow the program to read option values from the environment or a
configuration file.  However, this overrides the prompting mechanism, so
that the user does not get the option to change the value interactively.

If you want to let the user configure the default value, but still be
prompted if the option isn't specified on the command line, you can do so
by supplying a callable as the default value. For example, to get a default
from the environment:

.. code-block:: python

    import os

    @click.command()
    @click.option(
        "--username", prompt=True,
        default=lambda: os.environ.get("USER", "")
    )
    def hello(username):
        click.echo(f"Hello, {username}!")

To describe what the default value will be, set it in ``show_default``.

.. click:example::

    import os

    @click.command()
    @click.option(
        "--username", prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default="current user"
    )
    def hello(username):
        click.echo(f"Hello, {username}!")

.. click:run::

   invoke(hello, args=["--help"])


Callbacks and Eager Options
---------------------------

Sometimes, you want a parameter to completely change the execution flow.
For instance, this is the case when you want to have a ``--version``
parameter that prints out the version and then exits the application.

Note: an actual implementation of a ``--version`` parameter that is
reusable is available in Click as :func:`click.version_option`.  The code
here is merely an example of how to implement such a flag.

In such cases, you need two concepts: eager parameters and a callback.  An
eager parameter is a parameter that is handled before others, and a
callback is what executes after the parameter is handled.  The eagerness
is necessary so that an earlier required parameter does not produce an
error message.  For instance, if ``--version`` was not eager and a
parameter ``--foo`` was required and defined before, you would need to
specify it for ``--version`` to work.  For more information, see
:ref:`callback-evaluation-order`.

A callback is a function that is invoked with three parameters: the
current :class:`Context`, the current :class:`Parameter`, and the value.
The context provides some useful features such as quitting the
application and gives access to other already processed parameters.

Here's an example for a ``--version`` flag:

.. click:example::

    def print_version(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        click.echo('Version 1.0')
        ctx.exit()

    @click.command()
    @click.option('--version', is_flag=True, callback=print_version,
                  expose_value=False, is_eager=True)
    def hello():
        click.echo('Hello World!')

The `expose_value` parameter prevents the pretty pointless ``version``
parameter from being passed to the callback.  If that was not specified, a
boolean would be passed to the `hello` script.  The `resilient_parsing`
flag is applied to the context if Click wants to parse the command line
without any destructive behavior that would change the execution flow.  In
this case, because we would exit the program, we instead do nothing.

What it looks like:

.. click:run::

    invoke(hello)
    invoke(hello, args=['--version'])

Values from Environment Variables
---------------------------------

A very useful feature of Click is the ability to accept parameters from
environment variables in addition to regular parameters.  This allows
tools to be automated much easier.  For instance, you might want to pass
a configuration file with a ``--config`` parameter but also support exporting
a ``TOOL_CONFIG=hello.cfg`` key-value pair for a nicer development
experience.

This is supported by Click in two ways.  One is to automatically build
environment variables which is supported for options only.  To enable this
feature, the ``auto_envvar_prefix`` parameter needs to be passed to the
script that is invoked.  Each command and parameter is then added as an
uppercase underscore-separated variable.  If you have a subcommand
called ``run`` taking an option called ``reload`` and the prefix is
``WEB``, then the variable is ``WEB_RUN_RELOAD``.

Example usage:

.. click:example::

    @click.command()
    @click.option('--username')
    def greet(username):
        click.echo(f'Hello {username}!')

    if __name__ == '__main__':
        greet(auto_envvar_prefix='GREETER')

And from the command line:

.. click:run::

    invoke(greet, env={'GREETER_USERNAME': 'john'},
           auto_envvar_prefix='GREETER')

When using ``auto_envvar_prefix`` with command groups, the command name
needs to be included in the environment variable, between the prefix and
the parameter name, *i.e.* ``PREFIX_COMMAND_VARIABLE``. If you have a
subcommand called ``run-server`` taking an option called ``host`` and
the prefix is ``WEB``, then the variable is ``WEB_RUN_SERVER_HOST``.

Example:

.. click:example::

   @click.group()
   @click.option('--debug/--no-debug')
   def cli(debug):
       click.echo(f"Debug mode is {'on' if debug else 'off'}")

   @cli.command()
   @click.option('--username')
   def greet(username):
       click.echo(f"Hello {username}!")

   if __name__ == '__main__':
       cli(auto_envvar_prefix='GREETER')

.. click:run::

   invoke(cli, args=['greet',],
          env={'GREETER_GREET_USERNAME': 'John', 'GREETER_DEBUG': 'false'},
          auto_envvar_prefix='GREETER')


The second option is to manually pull values in from specific environment
variables by defining the name of the environment variable on the option.

Example usage:

.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
       click.echo(f"Hello {username}!")

    if __name__ == '__main__':
        greet()

And from the command line:

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})

In that case it can also be a list of different environment variables
where the first one is picked.

Multiple Values from Environment Values
---------------------------------------

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex.  The way
Click solves this is by leaving it up to the type to customize this
behavior.  For both ``multiple`` and ``nargs`` with values other than
``1``, Click will invoke the :meth:`ParamType.split_envvar_value` method to
perform the splitting.

The default implementation for all types is to split on whitespace.  The
exceptions to this rule are the :class:`File` and :class:`Path` types
which both split according to the operating system's path splitting rules.
On Unix systems like Linux and OS X, the splitting happens for those on
every colon (``:``), and for Windows, on every semicolon (``;``).

Example usage:

.. click:example::

    @click.command()
    @click.option('paths', '--path', envvar='PATHS', multiple=True,
                  type=click.Path())
    def perform(paths):
        for path in paths:
            click.echo(path)

    if __name__ == '__main__':
        perform()

And from the command line:

.. click:run::

    import os
    invoke(perform, env={"PATHS": f"./foo/bar{os.path.pathsep}./test"})

Other Prefix Characters
-----------------------

Click can deal with alternative prefix characters other than ``-`` for
options.  This is for instance useful if you want to handle slashes as
parameters ``/`` or something similar.  Note that this is strongly
discouraged in general because Click wants developers to stay close to
POSIX semantics.  However in certain situations this can be useful:

.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo(f"writable={w}")

    if __name__ == '__main__':
        chmod()

And from the command line:

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])

Note that if you are using ``/`` as prefix character and you want to use a
boolean flag you need to separate it with ``;`` instead of ``/``:

.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")

    if __name__ == '__main__':
        log()

Callbacks for Validation
------------------------

.. versionchanged:: 2.0

If you want to apply custom validation logic, you can do this in the
parameter callbacks. These callbacks can both modify values as well as
raise errors if the validation does not work. The callback runs after
type conversion. It is called for all sources, including prompts.

In Click 1.0, you can only raise the :exc:`UsageError` but starting with
Click 2.0, you can also raise the :exc:`BadParameter` error, which has the
added advantage that it will automatically format the error message to
also contain the parameter name.

.. click:example::

    def validate_rolls(ctx, param, value):
        if isinstance(value, tuple):
            return value

        try:
            rolls, _, dice = value.partition("d")
            return int(dice), int(rolls)
        except ValueError:
            raise click.BadParameter("format must be 'NdM'")

    @click.command()
    @click.option(
        "--rolls", type=click.UNPROCESSED, callback=validate_rolls,
        default="1d6", prompt=True,
    )
    def roll(rolls):
        sides, times = rolls
        click.echo(f"Rolling a {sides}-sided dice {times} time(s)")

.. click:run::

    invoke(roll, args=["--rolls=42"])
    println()
    invoke(roll, args=["--rolls=2d12"])
    println()
    invoke(roll, input=["42", "2d12"])


.. _optional-value:

Optional Value
--------------

Providing the value to an option can be made optional, in which case
providing only the option's flag without a value will either show a
prompt or use its ``flag_value``.

Setting ``is_flag=False, flag_value=value`` tells Click that the option
can still be passed a value, but if only the flag is given the
``flag_value`` is used.

.. click:example::

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

.. click:run::

    invoke(hello, args=[])
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"])

If the option has ``prompt`` enabled, then setting
``prompt_required=False`` tells Click to only show the prompt if the
option's flag is given, instead of if the option is not provided at all.

.. click:example::

    @click.command()
    @click.option('--name', prompt=True, prompt_required=False, default="Default")
    def hello(name):
        click.echo(f"Hello {name}!")

.. click:run::

    invoke(hello)
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"], input="Prompt")

If ``required=True``, then the option will still prompt if it is not
given, but it will also prompt if only the flag is given.

.. _options:

Options
=======

.. currentmodule:: click

Adding options to commands can be accomplished by the :func:`option`
decorator.  Since options can come in various different versions, there
are a ton of parameters to configure their behavior. Options in click are
distinct from :ref:`positional arguments <arguments>`.

Name Your Options
-----------------

Options have a name that will be used as the Python argument name when
calling the decorated function. This can be inferred from the option
names or given explicitly. Names are given as position arguments to the
decorator.

A name is chosen in the following order

1.  If a name is not prefixed, it is used as the Python argument name
    and not treated as an option name on the command line.
2.  If there is at least one name prefixed with two dashes, the first
    one given is used as the name.
3.  The first name prefixed with one dash is used otherwise.

To get the Python argument name, the chosen name is converted to lower
case, up to two dashes are removed as the prefix, and other dashes are
converted to underscores.

.. code-block:: python

    @click.command()
    @click.option('-s', '--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. code-block:: python

    @click.command()
    @click.option('-s', '--string-to-echo', 'string')
    def echo(string):
        click.echo(string)

-   ``"-f", "--foo-bar"``, the name is ``foo_bar``
-   ``"-x"``, the name is ``x``
-   ``"-f", "--filename", "dest"``, the name is  ``dest``
-   ``"--CamelCase"``, the name is ``camelcase``
-   ``"-f", "-fb"``, the name is ``f``
-   ``"--f", "--foo-bar"``, the name is ``f``
-   ``"---f"``, the name is ``_f``

Basic Value Options
-------------------

The most basic option is a value option.  These options accept one
argument which is a value.  If no type is provided, the type of the default
value is used.  If no default value is provided, the type is assumed to be
:data:`STRING`.  Unless a name is explicitly specified, the name of the
parameter is the first long option defined; otherwise the first short one is
used. By default, options are not required, however to make an option required,
simply pass in `required=True` as an argument to the decorator.

.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

.. click:example::

    # How to make an option required
    @click.command()
    @click.option('--n', required=True, type=int)
    def dots(n):
        click.echo('.' * n)

.. click:example::

    # How to use a Python reserved word such as `from` as a parameter
    @click.command()
    @click.option('--from', '-f', 'from_')
    @click.option('--to', '-t')
    def reserved_param_name(from_, to):
        click.echo(f"from {from_} to {to}")

And on the command line:

.. click:run::

   invoke(dots, args=['--n=2'])

In this case the option is of type :data:`INT` because the default value
is an integer.

To show the default values when showing command help, use ``show_default=True``

.. click:example::

    @click.command()
    @click.option('--n', default=1, show_default=True)
    def dots(n):
        click.echo('.' * n)

.. click:run::

   invoke(dots, args=['--help'])

For single option boolean flags, the default remains hidden if the default
value is False.

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


Multi Value Options
-------------------

Sometimes, you have options that take more than one argument.  For options,
only a fixed number of arguments is supported.  This can be configured by
the ``nargs`` parameter.  The values are then stored as a tuple.

.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        a, b = pos
        click.echo(f"{a} / {b}")

And on the command line:

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])

.. _tuple-type:

Tuples as Multi Value Options
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
----------------

Similarly to ``nargs``, there is also the case of wanting to support a
parameter being provided multiple times and have all the values recorded --
not just the last one.  For instance, ``git commit -m foo -m bar`` would
record two lines for the commit message: ``foo`` and ``bar``. This can be
accomplished with the ``multiple`` flag:

Example:

.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo('\n'.join(message))

And on the command line:

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar'])

When passing a ``default`` with ``multiple=True``, the default value
must be a list or tuple, otherwise it will be interpreted as a list of
single characters.

.. code-block:: python

    @click.option("--format", multiple=True, default=["json"])


Counting
--------

In some very rare circumstances, it is interesting to use the repetition
of options to count an integer up.  This can be used for verbosity flags,
for instance:

.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo(f"Verbosity: {verbose}")

And on the command line:

.. click:run::

    invoke(log, args=['-vvv'])

Boolean Flags
-------------

Boolean flags are options that can be enabled or disabled.  This can be
accomplished by defining two flags in one go separated by a slash (``/``)
for enabling or disabling the option.  (If a slash is in an option string,
Click automatically knows that it's a boolean flag and will pass
``is_flag=True`` implicitly.)  Click always wants you to provide an enable
and disable flag so that you can change the default later.

Example:

.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

And on the command line:

.. click:run::

    invoke(info, args=['--shout'])
    invoke(info, args=['--no-shout'])
    invoke(info)

If you really don't want an off-switch, you can just define one and
manually inform Click that something is a flag:

.. click:example::

    import sys

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

And on the command line:

.. click:run::

    invoke(info, args=['--shout'])
    invoke(info)

Note that if a slash is contained in your option already (for instance, if
you use Windows-style parameters where ``/`` is the prefix character), you
can alternatively split the parameters through ``;`` instead:

.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")

    if __name__ == '__main__':
        log()

.. versionchanged:: 6.0

If you want to define an alias for the second option only, then you will
need to use leading whitespace to disambiguate the format string:

Example:

.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', ' /-S', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info, args=['--help'])

Feature Switches
----------------

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

And on the command line:

.. click:run::

    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])
    invoke(info)

.. _choice-opts:

Choice Options
--------------

Sometimes, you want to have a parameter be a choice of a list of values.
In that case you can use :class:`Choice` type.  It can be instantiated
with a list of valid values.  The originally passed choice will be returned,
not the str passed on the command line.  Token normalization functions and
``case_sensitive=False`` can cause the two to be different but still match.

Example:

.. click:example::

    @click.command()
    @click.option('--hash-type',
                  type=click.Choice(['MD5', 'SHA1'], case_sensitive=False))
    def digest(hash_type):
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

Only pass the choices as list or tuple. Other iterables (like
generators) may lead to unexpected results.

Choices work with options that have ``multiple=True``. If a ``default``
value is given with ``multiple=True``, it should be a list or tuple of
valid choices.

Choices should be unique after considering the effects of
``case_sensitive`` and any specified token normalization function.

.. versionchanged:: 7.1
    The resulting value from an option will always be one of the
    originally passed choices regardless of ``case_sensitive``.

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


Password Prompts
----------------

Click also supports hidden prompts and asking for confirmation.  This is
useful for password input:

.. click:example::

    import codecs

    @click.command()
    @click.option(
        "--password", prompt=True, hide_input=True,
        confirmation_prompt=True
    )
    def encode(password):
        click.echo(f"encoded: {codecs.encode(password, 'rot13')}")

.. click:run::

    invoke(encode, input=['secret', 'secret'])

Because this combination of parameters is quite common, this can also be
replaced with the :func:`password_option` decorator:

.. code-block:: python

    @click.command()
    @click.password_option()
    def encrypt(password):
        click.echo(f"encoded: to {codecs.encode(password, 'rot13')}")


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


Yes Parameters
--------------

For dangerous operations, it's very useful to be able to ask a user for
confirmation.  This can be done by adding a boolean ``--yes`` flag and
asking for confirmation if the user did not provide it and to fail in a
callback:

.. click:example::

    def abort_if_false(ctx, param, value):
        if not value:
            ctx.abort()

    @click.command()
    @click.option('--yes', is_flag=True, callback=abort_if_false,
                  expose_value=False,
                  prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')

And what it looks like on the command line:

.. click:run::

    invoke(dropdb, input=['n'])
    invoke(dropdb, args=['--yes'])

Because this combination of parameters is quite common, this can also be
replaced with the :func:`confirmation_option` decorator:

.. click:example::

    @click.command()
    @click.confirmation_option(prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')


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

.. _ranges:

Range Options
-------------

The :class:`IntRange` type extends the :data:`INT` type to ensure the
value is contained in the given range. The :class:`FloatRange` type does
the same for :data:`FLOAT`.

If ``min`` or ``max`` is omitted, that side is *unbounded*. Any value in
that direction is accepted. By default, both bounds are *closed*, which
means the boundary value is included in the accepted range. ``min_open``
and ``max_open`` can be used to exclude that boundary from the range.

If ``clamp`` mode is enabled, a value that is outside the range is set
to the boundary instead of failing. For example, the range ``0, 5``
would return ``5`` for the value ``10``, or ``0`` for the value ``-1``.
When using :class:`FloatRange`, ``clamp`` can only be enabled if both
bounds are *closed* (the default).

.. click:example::

    @click.command()
    @click.option("--count", type=click.IntRange(0, 20, clamp=True))
    @click.option("--digit", type=click.IntRange(0, 9))
    def repeat(count, digit):
        click.echo(str(digit) * count)

.. click:run::

    invoke(repeat, args=['--count=100', '--digit=5'])
    invoke(repeat, args=['--count=6', '--digit=12'])


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

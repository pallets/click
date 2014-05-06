Options
=======

.. currentmodule:: click

Adding options to commands can be accomplished by the :func:`option`
decorator.  Since options can come in various different versions there
are a ton of parameters to configure their behavior.

Basic Value Options
-------------------

The most basic option is a value option.  These options accept one
argument which is a value.  If no type is provided the type of the default
value is used.  If no default value is provided the type is assumed to be
:data:`STRING`.  The name of the parameter is by default the first long
option defined, otherwise the first short one.

.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

And on the command line:

.. click:run::

   invoke(dots, args=['--n=2'])

In this case the option is of type :data:`INT` because the default value
is an integer.

Multi Value Options
-------------------

Sometimes you have options that take more than one argument.  For options
only a fixed number of arguments is supported.  This can be configured by
the ``nargs`` parameter.  The values are then stored as a tuple.

.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        click.echo('%s / %s' % pos)

And on the command line:

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])

Multiple Options
----------------

Similar to ``nargs`` there is also the case where sometimes you want to
support a parameter to be provided multiple times to and have all values
recorded and not just the last one.  For instance ``git commit -m foo -m
bar`` would record two lines for the commit message.  ``foo`` and ``bar``.
This can be accomplished with the ``multiple`` flag:

Example:

.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo('\n'.join(message))

And on the command line:

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar'])

Counting
--------

In some very rare circumstances it's interesting to use the repeating of
options to count an integer up.  This for instance can be used for
verbosity flags:

.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo('Verbosity: %s' % verbose)

And on the command line:

.. click:run::

    invoke(log, args=['-vvv'])

Boolean Flags
-------------

Boolean flags are options that can be enabled or disabled.  This can be
accomplished by defining two flags in one go separated by a slash (``/``)
for enabling or disabling the option.  Click always wants you to provide
an enable and disable flag so that you can change the default later.

Example:

.. click:example::

    import os

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = os.uname()[0]
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

And on the command line:

.. click:run::

    invoke(info, args=['--shout'])
    invoke(info, args=['--no-shout'])

If you really don't want an off-switch you can just define one and
manually inform click that something is a flag:

.. click:example::

    import os

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = os.uname()[0]
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

And on the command line:

.. click:run::

    invoke(info, args=['--shout'])

Feature Switches
----------------

In addition to boolean flags there are also feature switches.  These are
implemented by setting multiple options to the same parameter name and by
defining a flag value.  To set a default flag assign a value of `True` to
the flag that should be the default.

.. click:example::

    import os

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper',
                  default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(os.uname()[0], transformation)())

And on the command line:

.. click:run::

    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])
    invoke(info)

.. _choice-opts:

Choice Options
--------------

Sometimes you want to have a parameter be a choice of a list of values.
In that case you can use :class:`Choice` type.  It can be instantiated
with a list of valid values.

Example:

.. click:example::

    @click.command()
    @click.option('--hash-type', type=click.Choice(['md5', 'sha1']))
    def digest(hash_type):
        click.echo(hash_type)

What it looks like:

.. click:run::

    invoke(digest, args=['--hash-type=md5'])
    println()
    invoke(digest, args=['--hash-type=foo'])
    println()
    invoke(digest, args=['--help'])

.. _option-prompting:

Prompting
---------

Sometimes you want parameters that can either be provided from the command
line or if not, you want to ask for user input.  This can be implemented
with click by defining a prompt string.

Example:

.. click:example::

    @click.command()
    @click.option('--name', prompt=True)
    def hello(name):
        click.echo('Hello %s!' % name)

And what it looks like:

.. click:run::

    invoke(hello, args=['--name=John'])
    invoke(hello, input=['John'])

If you are not happy with the default prompt string you can ask for
a different one:

.. click:example::

    @click.command()
    @click.option('--name', prompt='Your name please')
    def hello(name):
        click.echo('Hello %s!' % name)

What it looks like:

.. click:run::

    invoke(hello, input=['John'])

Password Prompts
----------------

Click also supports hidden prompts and asking for confirmation.  This is
useful for password input:

.. click:example::

    @click.command()
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True)
    def encrypt(password):
        click.echo('Encrypting password to %s' % password.encode('rot13'))

What it looks like:

.. click:run::

    invoke(encrypt, input=['secret', 'secret'])

Because this combination of parameters is quite common this can also be
replaced with the :func:`password_option` decorator:

.. click:example::

    @click.command()
    @click.password_option()
    def encrypt(password):
        click.echo('Encrypting password to %s' % password.encode('rot13'))

Callbacks and Eager Options
---------------------------

Sometimes you want a parameter to completely change the execution flow.
This for instance is the case when you want to have a ``--version``
parameter that prints out the version and then exits the application.

In such cases you need two concepts: eager parameters and a callback.  An
eager parameter is a parameter that is handled before others and a
callback is what executes after the parameter is handled.  The eagerness
is necessary so that an earlier required parameter does not produce an
error message.  For instance if ``--version`` was not eager and a
parameter ``--foo`` was required and defined before, you would need to
specify it for ``--version`` to work.

A callback is a function that is invoked with two parameters: the current
:class:`Context` and the value.  The context provides some useful features
such as quitting the application and gives access to other already
processed parameters.

Here an example for a ``--version`` flag:

.. click:example::

    def print_version(ctx, value):
        if not value:
            return
        click.echo('Version 1.0')
        ctx.exit()

    @click.command()
    @click.option('--version', is_flag=True, callback=print_version,
                  expose_value=False, is_eager=True)
    def hello():
        click.echo('Hello World!')

The `expose_value` parameter prevents the now pretty pointless ``version``
parameter to be passed to the callback.  If that was not specified a
boolean would be passed to the `hello` script.

What it looks like:

.. click:run::

    invoke(hello)
    invoke(hello, args=['--version'])

Yes Parameters
--------------

For dangerous operations it's very useful to be able to ask a user for
confirmation.  This can be done by adding a boolean ``--yes`` flag and
asking for confirmation if the user did not provide it and to fail in a
callback:

.. click:example::

    def abort_if_false(ctx, value):
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

Because this combination of parameters is quite common this can also be
replaced with the :func:`confirmation_option` decorator:

.. click:example::

    @click.command()
    @click.confirmation_option(help='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')

Values from Environment Variables
---------------------------------

A very useful feature of click is the ability to accept parameters from
environment variables in addition to regular parameters.  This allows
tools to be automated much easier.  For instance you might want to pass
the config file as ``--config`` parameter but also support exporting a
``TOOL_CONFIG=hello.cfg`` key / value pair for a nicer development
experience.

This is supported by click in two ways.  One is to automatically build
environment variables which is supported for options only.  To enable this
feature the ``auto_envvar_prefix`` parameter needs to be passed to the
script that is invoked.  Each command and parameter is then added as
underscore-separated variable in uppercase.  So if you have a subcommand
called ``foo`` taking an option called ``bar`` and the prefix is
``MY_TOOL`` then the variable is ``MY_TOOL_FOO_BAR``.

Example usage:

.. click:example::

    @click.command()
    @click.option('--username')
    def greet(username):
        click.echo('Hello %s!' % username)

    if __name__ == '__main__':
        greet(auto_envvar_prefix='GREETER')

And from the command line:

.. click:run::

    invoke(greet, env={'GREETER_USERNAME': 'john'},
           auto_envvar_prefix='GREETER')

The second option is to manually pull values in from specific environment
variables by defining the name of the environment variable on the option.

Example usage:

.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
        click.echo('Hello %s!' % username)

    if __name__ == '__main__':
        greet()

And from the command line:

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})

In that case it can also be a list of different environment variables
where the first one is picked.

Other Prefix Characters
-----------------------

Click can deal with alternative prefix characters, other than ``-`` for
options.  This is for instance useful if you want to handle slashes as
parameters ``/`` or something similar.  Note that this is strongly
discouraged in general because click wants developers to stay close to
POSIX semantics.  However in certain situations this can be useful:

.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo('writable=%s' % w)

    if __name__ == '__main__':
        chmod()

And from the command line:

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])

.. _ranges:

Range Options
-------------

A special mention should go to the :class:`IntRange` type which works very
similar to the :data:`INT` type but restricts the value to fall into a
specific range (inclusive on both edges).  It has two modes:

-   the default mode (non clamping mode) where a value that falls outside
    of the range will cause an error.
-   an optional clamping mode where a value that falls outside of the
    range will be clamped.  This means that a range of ``0-5`` would
    return ``5`` for the value ``10`` or ``0`` for the value ``-1`` (for
    example).

Example:

.. click:example::

    @click.command()
    @click.option('--count', type=click.IntRange(0, 20, clamp=True))
    @click.option('--digit', type=click.IntRange(0, 10))
    def repeat(count, digit):
        click.echo(str(digit) * count)

    if __name__ == '__main__':
        repeat()

And from the command line:

.. click:run::

    invoke(repeat, args=['--count=1000', '--digit=5'])
    invoke(repeat, args=['--count=1000', '--digit=12'])

If you pass ``None`` for any of the edges it means that the range is open
at that side.

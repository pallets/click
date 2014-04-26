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
:data:`STRING`.

Example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        print('.' * n)

And on the command line::

    $ python dots.py --n=2
    ..

In this case the option is of type :data:`INT` because the default value
is an integer.

The name of the parameter is the longest.

Multi Value Options
-------------------

Sometimes you have options that take more than one argument.  For options
only a fixed number of arguments is supported.  This can be configured by
the ``nargs`` parameter.  The values are then stored as a tuple.

Example::


    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        print('%s / %s' % pos)

And on the command line::

    $ python findme.py --pos 2.0 3.0
    2.0 / 3.0

Multiple Options
----------------

Similar to ``nargs`` there is also the case where sometimes you want to
support a parameter to be provided multiple times to and have all values
recorded and not just the last one.  For instance ``git commit -m foo -m
bar`` would record two lines for the commit message.  ``foo`` and ``bar``.
This can be accomplished with the ``multiple`` flag:

Example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        print('\n'.join(message))

And on the command line::

    $ python commit.py -m foo -m bar
    foo
    bar

Counting
--------

If you have used ``optparse`` or ``argparse`` before you might be missing
support for counting.  This is a very rarely useful feature, usually only
useful for implementing verbosity flags.  It can however be emulated by
using the multiple flag and taking the length of the end result::

    @click.command()
    @click.option('-v', '--verbose', is_flag=True, multiple=True)
    def log(verbose):
        verbosity = len(verbose)
        print('Verbosity: %s' % verbosity)

And on the command line::

    $ python log.py -vvv
    Verbosity: 3

Boolean Flags
-------------

Boolean flags are options that can be enabled or disabled.  This can be
accomplished by defining two flags in one go separated by a slash (``/``)
for enabling or disabling the option.  Click always wants you to provide
an enable and disable flag so that you can change the default later.

Example::

    import os

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = os.uname()[0]
        if shout:
            rv = rv.upper() + '!!!!111'
        print(rv)

And on the command line::

    $ python info.py --shout
    DARWIN!!!!111
    $ python info.py --no-shout
    Darwin

If you really don't want an off-switch you can just define one and
manually inform click that something is a flag::

    import os

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = os.uname()[0]
        if shout:
            rv = rv.upper() + '!!!!111'
        print(rv)

And on the command line::

    $ python info.py --shout
    DARWIN!!!!111

Feature Switches
----------------

In addition to boolean flags there are also feature switches.  These are
implemented by setting multiple options to the same parameter name and by
defining a flag value.  To set a default flag assign a value of `True` to
the flag that should be the default.

Example::

    import os

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper',
                  default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        print(getattr(os.uname()[0], transformation)())

And on the command line::

    $ python info.py --upper
    DARWIN
    $ python info.py --lower
    darwin
    $ python info.py
    DARWIN

.. _choice-opts:

Choice Options
--------------

Sometimes you want to have a parameter be a choice of a list of values.
In that case you can use :class:`Choice` type.  It can be instanciated
with a list of valid values.

Example::

    @click.command()
    @click.option('--hash-type', type=click.Choice(['md5', 'sha1']))
    def digest(hash_type):
        print(hash_type)

What it looks like::

    $ python digest.py --hash-type=md5
    md5

    $ python digest.py --hash-type=foo
    Usage: digest.py [OPTIONS]

    Error: Invalid value for hash_type: invalid choice: foo. (choose from md5, sha1)

    $ python digest.py --help
    Usage: digest.py [OPTIONS]

    Options:
      --hash-type=[md5|sha1]
      --help                Show this message and exit.

.. _option-prompting:

Prompting
---------

Sometimes you want parameters that can either be provided from the command
line or if not, you want to ask for user input.  This can be implemented
with click by defining a prompt string.

Example::

    import os

    @click.command()
    @click.option('--name', prompt=True)
    def hello(name):
        print('Hello %s!' % name)

And what it looks like::

    $ python hello.py --name=John
    Hello John!
    $ python hello.py
    Name: John
    Hello John!

If you are not happy with the default prompt string you can ask for
a different one::

    import os

    @click.command()
    @click.option('--name', prompt='Your name please')
    def hello(name):
        print('Hello %s!' % name)

What it looks like::

    $ python hello.py
    Your name please: John
    Hello John!

Password Prompts
----------------

Click also supports hidden prompts and asking for confirmation.  This is
useful for password input::

    @click.command()
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True)
    def encrypt(password):
        print('Encrypting password to %s' % password.encode('rot13'))

What it looks like::

    $ python encrypt.py
    Password:
    Repeat for confirmation:
    Encrypting password to frpher

Because this combination of parameters is quite common this can also be
replaced with the :func:`password_option` decorator::

    @click.command()
    @click.password_option()
    def encrypt(password):
        print('Encrypting password to %s' % password.encode('rot13'))

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

Here an example for a ``--version`` flag::

    def print_version(ctx, value):
        if not value:
            return
        print('Version 1.0')
        ctx.exit()

    @click.command()
    @click.option('--version', is_flag=True, callback=print_version,
                  expose_value=False, is_eager=True)
    def hello():
        print('Hello World!')

The `expose_value` parameter prevents the now pretty pointless ``version``
parameter to be passed to the callback.  If that was not specified a
boolean would be passed to the `hello` script.

What it looks like::

    $ python hello.py 
    Hello World!
    $ python hello.py --version
    Version 1.0

Yes Parameters
--------------

For dangerous operations it's very useful to be able to ask a user for
confirmation.  This can be done by adding a boolean ``--yes`` flag and
asking for confirmation if the user did not provide it and to fail in a
callback::

    def abort_if_false(ctx, value):
        if not value:
            ctx.abort()

    @click.command()
    @click.option('--yes', is_flag=True, callback=abort_if_false,
                  expose_value=False,
                  prompt='Are you sure you want to drop the db?')
    def dropdb():
        print('Dropped all tables!')

And what it looks like on the command line::

    $ python dropdb.py
    Are you sure you want to drop the db? [yN]: n 
    Aborted!
    $ python dropdb.py --yes
    Dropped all tables!

Because this combination of parameters is quite common this can also be
replaced with the :func:`confirmation_option` decorator::

    @click.command()
    @click.confirmation_option('Are you sure you want to drop the db?')
    def dropdb():
        print('Dropped all tables!')

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

Example usage::

    @click.command()
    @click.option('--username')
    def greet(username):
        print('Hello %s!' % username)

    if __name__ == '__main__':
        greet(auto_envvar_prefix='GREETER')

And from the command line::

    $ export GREETER_USERNAME=john
    $ python greet.py
    Hello john!

The second option is to manually pull values in from specific environment
variables by defining the name of the environment variable on the option.

Example usage::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
        print('Hello %s!' % username)

    if __name__ == '__main__':
        greet()

And from the command line::

    $ export USERNAME=john
    $ python greet.py
    Hello john!

In that case it can also be a list of different environment variables
where the first one is picked.

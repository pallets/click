Basic Commands, Groups, Context
================================

.. currentmodule:: click

Commands and Groups are the building blocks for Click applications. :class:`Command` wraps a function to make it into a cli command. :class:`Group` wraps Commands and Groups to make them into applications. :class:`Context` is how groups and commands communicate.

.. contents::
   :depth: 2
   :local:

Commands
--------------------

Basic Command Example
^^^^^^^^^^^^^^^^^^^^^^^
A simple command decorator takes no arguments.

.. click:example::
    @click.command()
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Renaming Commands
^^^^^^^^^^^^^^^^^^^
By default the command is the function name with underscores replaced by dashes. To change this pass the  desired name into the first positional argument.

.. click:example::
    @click.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Deprecating Commands
^^^^^^^^^^^^^^^^^^^^^^
To mark a command as deprecated pass in ``deprecated=True``

.. click:example::
    @click.command('say-hello', deprecated=True)
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Groups
------------

Basic Group Example
^^^^^^^^^^^^^^^^^^^^^
A group wraps one or more commands. After being wrapped, the commands are nested under that group. You can see that on the help pages and in the execution. By default, invoking the group with no command shows the help page.

.. click:example::
    @click.group()
    def greeting():
        click.echo('Starting greeting ...')

    @greeting.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

At the top level:

.. click:run::

    invoke(greeting)

At the command level:

.. click:run::

    invoke(greeting, args=['say-hello'])
    invoke(greeting, args=['say-hello', '--help'])

As you can see from the above example, the function wrapped by the group decorator executes unless it is interrupted (for example by calling the help).

Renaming Groups
^^^^^^^^^^^^^^^^^
To have a name other than the decorated function name as the group name, pass it in as the first positional argument.

.. click:example::
    @click.group('greet-someone')
    def greeting():
        click.echo('Starting greeting ...')

    @greeting.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::

    invoke(greeting, args=['say-hello'])

Group Invocation Without Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, if a group is passed without a command, the group is not invoked and a command automatically passes ``--help``. To change this, pass ``invoke_without_command=True`` to the group. The context object also includes information about whether or not the group invocation would go to a command nested under it.

.. click:example::

    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo('I was invoked without subcommand')
        else:
            click.echo(f"I am about to invoke {ctx.invoked_subcommand}")

    @cli.command()
    def sync():
        click.echo('The subcommand')

.. click:run::

    invoke(cli, prog_name='tool', args=[])
    invoke(cli, prog_name='tool', args=['sync'])



Group Separation
^^^^^^^^^^^^^^^^^^^
Command :ref:`parameters` attached to a command belong only to that command.

.. click:example::
    @click.group()
    def greeting():
        pass

    @greeting.command()
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

    @greeting.command()
    @click.option('--count', default=1)
    def goodbye(count):
        for x in range(count):
            click.echo("Goodbye!")

.. click:run::

    invoke(greeting, args=['hello', '--count', '2'])
    invoke(greeting, args=['goodbye', '--count', '2'])
    invoke(greeting)

Additionally parameters for a given group belong only to that group and not to the commands under it. What this means is that options and arguments for a specific command have to be specified *after* the command name itself, but *before* any other command names.

This behavior is observable with the ``--help`` option. Suppose we have a group called ``tool`` containing a command called ``sub``.

- ``tool --help`` returns the help for the whole program (listing subcommands).
- ``tool sub --help`` returns the help for the ``sub`` subcommand.
- But ``tool --help sub`` treats ``--help`` as an argument for the main program. Click then invokes the callback for ``--help``, which prints the help and aborts the program before click can process the subcommand.

Arbitrary Nesting
^^^^^^^^^^^^^^^^^^^
:class:`Commands <Command>` are attached to a :class:`Group`. Multiple groups can be attached to another group. Groups containing multiple groups can be attached to a group, and so on. To invoke a command nested under multiple groups, all the groups under which it is nested must be invoked.

.. click:example::

    @click.group()
    def cli():
        pass

    # Not @click so that the group is registered now.
    @cli.group()
    def session():
        click.echo('Starting session')

    @session.command()
    def initdb():
        click.echo('Initialized the database')

    @session.command()
    def dropdb():
        click.echo('Dropped the database')

.. click:run::

    invoke(cli, args=['session', 'initdb'])

Lazily Attaching Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Most examples so far have attached the commands to a group immediately, but commands may be registered later. This could be used to split commands into multiple Python modules. Regardless of how they are attached, the commands are invoked identically.

.. click:example::

    @click.group()
    def cli():
        pass

    @cli.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(dropdb)

.. click:run::

    invoke(cli, args=['initdb'])
    invoke(cli, args=['dropdb'])

Context Object
-------------------
The :class:`Context` object is how commands and groups communicate.

Auto Envvar Prefix
^^^^^^^^^^^^^^^^^^^^
Automatically built environment variables are supported for options only. To enable this feature, the ``auto_envvar_prefix`` parameter needs to be passed to the script that is invoked.  Each command and parameter is then added as an uppercase underscore-separated variable.  If you have a subcommand
called ``run`` taking an option called ``reload`` and the prefix is ``WEB``, then the variable is ``WEB_RUN_RELOAD``.

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

Global Context Access
---------------------

.. versionadded:: 5.0

Starting with Click 5.0 it is possible to access the current context from
anywhere within the same thread through the use of the
:func:`get_current_context` function which returns it.  This is primarily
useful for accessing the context bound object as well as some flags that
are stored on it to customize the runtime behavior.  For instance the
:func:`echo` function does this to infer the default value of the `color`
flag.

Example usage::

    def get_current_command_name():
        return click.get_current_context().info_name

It should be noted that this only works within the current thread.  If you
spawn additional threads then those threads will not have the ability to
refer to the current context.  If you want to give another thread the
ability to refer to this context you need to use the context within the
thread as a context manager::

    def spawn_thread(ctx, func):
        def wrapper():
            with ctx:
                func()
        t = threading.Thread(target=wrapper)
        t.start()
        return t

Now the thread function can access the context like the main thread would
do.  However if you do use this for threading you need to be very careful
as the vast majority of the context is not thread safe!  You are only
allowed to read from the context, but not to perform any modifications on
it.


Detecting the Source of a Parameter
-----------------------------------

In some situations it's helpful to understand whether or not an option
or parameter came from the command line, the environment, the default
value, or :attr:`Context.default_map`. The
:meth:`Context.get_parameter_source` method can be used to find this
out. It will return a member of the :class:`~click.core.ParameterSource`
enum.

.. click:example::

    @click.command()
    @click.argument('port', nargs=1, default=8080, envvar="PORT")
    @click.pass_context
    def cli(ctx, port):
        source = ctx.get_parameter_source("port")
        click.echo(f"Port came from {source.name}")

.. click:run::

    invoke(cli, prog_name='cli', args=['8080'])
    println()
    invoke(cli, prog_name='cli', args=[], env={"PORT": "8080"})
    println()
    invoke(cli, prog_name='cli', args=[])
    println()

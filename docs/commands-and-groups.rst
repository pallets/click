Basic Commands, Groups, Context
================================

.. currentmodule:: click

Commands and Groups are the building blocks for Click applications. :class:`Command` wraps a function to make it into a cli command. :class:`Group` wraps Commands and Groups to make them into applications. :class:`Context` is how groups and commands communicate.

.. contents::
   :depth: 1
   :local:

Basic Command Example
----------------------
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
------------------
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
---------------------
To mark a command as deprecated pass in ``deprecated=True``

.. click:example::
    @click.command('say-hello', deprecated=True)
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Basic Group Example
---------------------
A group wraps command(s). After being wrapped, the commands are nested under that group. You can see that on the help pages and in the execution. By default, invoking the group with no command shows the help page.

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
-----------------
To have a name other than the decorated function name as the group name, pass it in as the first positional argument.

.. click:example::
    @click.group('greet_someone')
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
--------------------------------

By default, a group is not invoked unless a subcommand is passed. In fact, not
providing a command automatically passes ``--help`` by default. This behavior
can be changed by passing ``invoke_without_command=True`` to a group. In that
case, the callback is always invoked instead of showing the help page. The
context object also includes information about whether or not the invocation
would go to a subcommand.

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
--------------------------
Within a group, command :ref:`parameters` attached to a command belong only to that command.

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
- But ``tool.py --help sub`` treats ``--help`` as an argument for the main program. Click then invokes the callback for ``--help``, which prints the help and aborts the program before click can process the subcommand.

Arbitrary Nesting
------------------
Commands are attached to a group. Multiple groups can be attached to another group. Groups containing multiple groups can be attached to a group, and so on.
To invoke a command nest under multiple groups, all the above groups must added.

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
--------------------------
Most examples so far have attached the the commands and group immediately, but commands may be registered later. This could be used to split command into multiple Python modules.

.. click:example::

    @click.group()
    def cli():
        pass

    @click.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(initdb)
    cli.add_command(dropdb)

Context Object
-------------------
The :class:`Context` object ...

Commands and Groups
===================

.. currentmodule:: click

The most important feature of click is the concept of arbitrarily nesting
command line utilities.  This is implemented through the :class:`Command`
and :class:`Group` (actually :class:`MultiCommand`).

Callback Invocation
-------------------

For a regular command the callback is executed whenever the command runs.
So if the script is the only command it will always fire (unless a
parameter callback prevents it.  This for instance happens if someone
passes ``--help`` to the script).

For groups and multi commands the situation looks different.  In that case
the callback fires whenever a subcommand fires (unless this behavior is
changed).  What this means in practice is that an outer command runs
when an inner command runs:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    def cli(debug):
        click.utils.echo('Debug mode is %s' % ('on' if debug else 'off'))

    @cli.command()
    def sync():
        click.utils.echo('Synching')

Here is what this looks like:

.. click:run::

    invoke(cli, prog_name='tool.py')
    println()
    invoke(cli, prog_name='tool.py', args=['--debug', 'sync'])

Nested Handling and Contexts
----------------------------

As you can see from the earlier example the basic command group accepts a
debug argument which is passed to its callback, but not to the sync
command itself.  The sync command only accepts its own arguments.

This allows tools to act completely independent of each other.  But how
does one command talk to a nested one?  The answer to this is the
:class:`Context`.

Each time a command is invoked a new context is created and linked with the
parent context.  Normally you can't see these contexts, but they are
there.  Contexts are passed to parameter callbacks together with the
value automatically.  Commands can also ask for the context to be passed
by marking themselves with the :func:`pass_context` decorator.  In that
case the context is passed as first argument.

The context can also carry a program specified object that can be
used for the program's purposes.  What this means is that you can build a
script like this:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    @click.pass_context
    def cli(ctx, debug):
        ctx.obj['DEBUG'] = debug

    @cli.command()
    @click.pass_context
    def sync(ctx):
        click.utils.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))

    if __name__ == '__main__':
        cli(obj={})

If the object is provided each context will pass the object onwards to
its children, but at any level a context's object can be overridden.  To
reach to a parent ``context.parent`` can be used.

In addition to that instead of passing an object down nothing stops the
application from modifying global state.  For instance you could just flip
a global ``DEBUG`` variable and be done with it.

Decorating Commands
-------------------

As you have seen in the earlier example a decorator can change how a
command is invoked.  What actually happens behind the scenes is that
callbacks are always invoked through the :meth:`Context.invoke` method
which automatically invokes a command correctly (by either passing the
context or not).

This is very useful when you want to write custom decorators.  For
instance a common pattern would be to configure an object representing
state and then storing it on the context and then to use a custom
decorator to find the most recent object of this sort and pass it as first
argument.

For instance the :func:`pass_obj` decorator can be implemented like this:

.. click:example::

    from functools import update_wrapper

    def pass_obj(f):
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            return ctx.invoke(f, ctx.obj, *args, **kwargs)
        return update_wrapper(new_func, f)

The :meth:`Context.invoke` command will automatically invoke the function
in the correct way.  So the function will either be called with ``f(ctx,
obj)`` or ``f(obj)`` depending on if it itself is decorated with
:func:`with_context`.

This is a very powerful context that can be used to build very complex
nested applications.  See :ref:`complex-guide` for more information.


Group Invocation Without Command
--------------------------------

By default a group or multi command is not invoked unless a subcommand is
passed.  In fact, not providing a command automatically passes ``--help``
by default.  This behavior can be changed by passing
``invoke_without_command=True`` to a group.  In that case the callback is
always invoked instead of showing the help page.  The context object also
includes information about if the invocation would go to a subcommand or
not.

Example:

.. click:example::

    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.utils.echo('I was invoked without subcommand')
        else:
            click.utils.echo('I am about to invoke %s' % ctx.invoked_subcommand)

    @cli.command()
    def sync():
        click.utils.echo('The subcommand')

And how it works in practice::

    $ python tool.py 
    I was invoked without subcommand
    $ python tool.py sync
    I am about to invoke sync
    The subcommand

.. _custom-multi-commands:

Custom Multi Commands
---------------------

In addition to using :func:`click.group` you can also build your own
custom multi commands.  This is useful when you want to support commands
being loaded lazily from plugins.

A custom multi command just needs to implement a list and load method:

.. click:example::

    import click
    import os

    plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

    class MyCLI(click.MultiCommand):

        def list_commands(self, ctx):
            rv = []
            for filename in os.listdir(plugin_folder):
                if filename.endswith('.py'):
                    rv.append(filename[:-3])
            rv.sort()
            return rv

        def get_command(self, name):
            ns = {}
            fn = os.path.join(plugin_folder, name + '.py')
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
            return ns['cli']

    cli = MyCLI(help='This tool\'s subcommands are loaded from a '
                'plugin folder dynamically.')

    if __name__ == '__main__':
        cli()

These custom classes can also be used with decorators:

.. click:example::

    @click.command(cls=MyCLI)
    def cli():
        pass

Merging Multi Commands
----------------------

In addition to implementing custom multi commands it can also be
interesting to merge multiple together into one script.  While this is
generally not as recommended as nesting one below the other the merging
approach can be useful in some circumstances for a nicer shell experience.

A default implementation for such a merging system is the
:class:`CommandCollection` class.  It accepts a list of other multi
commands and makes the commands available on the same class.  It accepts a
list of other multi commands and makes the commands available on the same
level.

Example usage:

.. click:example::

    import click

    @click.group()
    def cli1():
        pass

    @cli1.command()
    def cmd1():
        """Command on cli1"""

    @click.group()
    def cli2():
        pass

    @cli1.command()
    def cmd2():
        """Command on cli2"""

    cli = click.CommandCollection(sources=[cli1, cli2])

    if __name__ == '__main__':
        cli()

And what it looks like:

.. click:run::

    invoke(cli, prog_name='cli', args=['--help'])

In case a command exists on more than one source, the first source wins.

Commands and Groups
===================

.. currentmodule:: click

The most important feature of Click is the concept of arbitrarily nesting
command line utilities.  This is implemented through the :class:`Command`
and :class:`Group` (actually :class:`MultiCommand`).

Callback Invocation
-------------------

For a regular command, the callback is executed whenever the command runs.
If the script is the only command, it will always fire (unless a parameter
callback prevents it.  This for instance happens if someone passes
``--help`` to the script).

For groups and multi commands, the situation looks different.  In this case,
the callback fires whenever a subcommand fires (unless this behavior is
changed).  What this means in practice is that an outer command runs
when an inner command runs:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    def cli(debug):
        click.echo('Debug mode is %s' % ('on' if debug else 'off'))

    @cli.command()
    def sync():
        click.echo('Syncing')

Here is what this looks like:

.. click:run::

    invoke(cli, prog_name='tool.py')
    println()
    invoke(cli, prog_name='tool.py', args=['--debug', 'sync'])

Passing Parameters
------------------

Click strictly separates parameters between commands and subcommands. What this
means is that options and arguments for a specific command have to be specified
*after* the command name itself, but *before* any other command names.

This behavior is already observable with the predefined ``--help`` option.
Suppose we have a program called ``tool.py``, containing a subcommand called
``sub``.

- ``tool.py --help`` will return the help for the whole program (listing
  subcommands).

- ``tool.py sub --help`` will return the help for the ``sub`` subcommand.

- But ``tool.py --help sub`` will treat ``--help`` as an argument for the main
  program. Click then invokes the callback for ``--help``, which prints the
  help and aborts the program before click can process the subcommand.

Nested Handling and Contexts
----------------------------

As you can see from the earlier example, the basic command group accepts a
debug argument which is passed to its callback, but not to the sync
command itself.  The sync command only accepts its own arguments.

This allows tools to act completely independent of each other, but how
does one command talk to a nested one?  The answer to this is the
:class:`Context`.

Each time a command is invoked, a new context is created and linked with the
parent context.  Normally, you can't see these contexts, but they are
there.  Contexts are passed to parameter callbacks together with the
value automatically.  Commands can also ask for the context to be passed
by marking themselves with the :func:`pass_context` decorator.  In that
case, the context is passed as first argument.

The context can also carry a program specified object that can be
used for the program's purposes.  What this means is that you can build a
script like this:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    @click.pass_context
    def cli(ctx, debug):
        # ensure that ctx.obj exists and is a dict (in case `cli()` is called
        # by means other than the `if` block below
        ctx.ensure_object(dict)

        ctx.obj['DEBUG'] = debug

    @cli.command()
    @click.pass_context
    def sync(ctx):
        click.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))

    if __name__ == '__main__':
        cli(obj={})

If the object is provided, each context will pass the object onwards to
its children, but at any level a context's object can be overridden.  To
reach to a parent, ``context.parent`` can be used.

In addition to that, instead of passing an object down, nothing stops the
application from modifying global state.  For instance, you could just flip
a global ``DEBUG`` variable and be done with it.

Decorating Commands
-------------------

As you have seen in the earlier example, a decorator can change how a
command is invoked.  What actually happens behind the scenes is that
callbacks are always invoked through the :meth:`Context.invoke` method
which automatically invokes a command correctly (by either passing the
context or not).

This is very useful when you want to write custom decorators.  For
instance, a common pattern would be to configure an object representing
state and then storing it on the context and then to use a custom
decorator to find the most recent object of this sort and pass it as first
argument.

For instance, the :func:`pass_obj` decorator can be implemented like this:

.. click:example::

    from functools import update_wrapper

    def pass_obj(f):
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            return ctx.invoke(f, ctx.obj, *args, **kwargs)
        return update_wrapper(new_func, f)

The :meth:`Context.invoke` command will automatically invoke the function
in the correct way, so the function will either be called with ``f(ctx,
obj)`` or ``f(obj)`` depending on whether or not it itself is decorated with
:func:`pass_context`.

This is a very powerful concept that can be used to build very complex
nested applications; see :ref:`complex-guide` for more information.


Group Invocation Without Command
--------------------------------

By default, a group or multi command is not invoked unless a subcommand is
passed.  In fact, not providing a command automatically passes ``--help``
by default.  This behavior can be changed by passing
``invoke_without_command=True`` to a group.  In that case, the callback is
always invoked instead of showing the help page.  The context object also
includes information about whether or not the invocation would go to a
subcommand.

Example:

.. click:example::

    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo('I was invoked without subcommand')
        else:
            click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

    @cli.command()
    def sync():
        click.echo('The subcommand')

And how it works in practice:

.. click:run::

    invoke(cli, prog_name='tool', args=[])
    invoke(cli, prog_name='tool', args=['sync'])

.. _custom-multi-commands:

Custom Multi Commands
---------------------

In addition to using :func:`click.group`, you can also build your own
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

        def get_command(self, ctx, name):
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

In addition to implementing custom multi commands, it can also be
interesting to merge multiple together into one script.  While this is
generally not as recommended as it nests one below the other, the merging
approach can be useful in some circumstances for a nicer shell experience.

The default implementation for such a merging system is the
:class:`CommandCollection` class.  It accepts a list of other multi
commands and makes the commands available on the same level.

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

    @cli2.command()
    def cmd2():
        """Command on cli2"""

    cli = click.CommandCollection(sources=[cli1, cli2])

    if __name__ == '__main__':
        cli()

And what it looks like:

.. click:run::

    invoke(cli, prog_name='cli', args=['--help'])

In case a command exists in more than one source, the first source wins.


.. _multi-command-chaining:

Multi Command Chaining
----------------------

.. versionadded:: 3.0

Sometimes it is useful to be allowed to invoke more than one subcommand in
one go.  For instance if you have installed a setuptools package before
you might be familiar with the ``setup.py sdist bdist_wheel upload``
command chain which invokes ``dist`` before ``bdist_wheel`` before
``upload``.  Starting with Click 3.0 this is very simple to implement.
All you have to do is to pass ``chain=True`` to your multicommand:

.. click:example::

    @click.group(chain=True)
    def cli():
        pass


    @cli.command('sdist')
    def sdist():
        click.echo('sdist called')


    @cli.command('bdist_wheel')
    def bdist_wheel():
        click.echo('bdist_wheel called')

Now you can invoke it like this:

.. click:run::

    invoke(cli, prog_name='setup.py', args=['sdist', 'bdist_wheel'])

When using multi command chaining you can only have one command (the last)
use ``nargs=-1`` on an argument.  It is also not possible to nest multi
commands below chained multicommands.  Other than that there are no
restrictions on how they work.  They can accept options and arguments as
normal.

Another note: the :attr:`Context.invoked_subcommand` attribute is a bit
useless for multi commands as it will give ``'*'`` as value if more than
one command is invoked.  This is necessary because the handling of
subcommands happens one after another so the exact subcommands that will
be handled are not yet available when the callback fires.

.. note::

    It is currently not possible for chain commands to be nested.  This
    will be fixed in future versions of Click.


Multi Command Pipelines
-----------------------

.. versionadded:: 3.0

A very common usecase of multi command chaining is to have one command
process the result of the previous command.  There are various ways in
which this can be facilitated.  The most obvious way is to store a value
on the context object and process it from function to function.  This
works by decorating a function with :func:`pass_context` after which the
context object is provided and a subcommand can store its data there.

Another way to accomplish this is to setup pipelines by returning
processing functions.  Think of it like this: when a subcommand gets
invoked it processes all of its parameters and comes up with a plan of
how to do its processing.  At that point it then returns a processing
function and returns.

Where do the returned functions go?  The chained multicommand can register
a callback with :meth:`MultiCommand.resultcallback` that goes over all
these functions and then invoke them.

To make this a bit more concrete consider this example:

.. click:example::

    @click.group(chain=True, invoke_without_command=True)
    @click.option('-i', '--input', type=click.File('r'))
    def cli(input):
        pass

    @cli.resultcallback()
    def process_pipeline(processors, input):
        iterator = (x.rstrip('\r\n') for x in input)
        for processor in processors:
            iterator = processor(iterator)
        for item in iterator:
            click.echo(item)

    @cli.command('uppercase')
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()
        return processor

    @cli.command('lowercase')
    def make_lowercase():
        def processor(iterator):
            for line in iterator:
                yield line.lower()
        return processor

    @cli.command('strip')
    def make_strip():
        def processor(iterator):
            for line in iterator:
                yield line.strip()
        return processor

That's a lot in one go, so let's go through it step by step.

1.  The first thing is to make a :func:`group` that is chainable.  In
    addition to that we also instruct Click to invoke even if no
    subcommand is defined.  If this would not be done, then invoking an
    empty pipeline would produce the help page instead of running the
    result callbacks.
2.  The next thing we do is to register a result callback on our group.
    This callback will be invoked with an argument which is the list of
    all return values of all subcommands and then the same keyword
    parameters as our group itself.  This means we can access the input
    file easily there without having to use the context object.
3.  In this result callback we create an iterator of all the lines in the
    input file and then pass this iterator through all the returned
    callbacks from all subcommands and finally we print all lines to
    stdout.

After that point we can register as many subcommands as we want and each
subcommand can return a processor function to modify the stream of lines.

One important thing of note is that Click shuts down the context after
each callback has been run.  This means that for instance file types
cannot be accessed in the `processor` functions as the files will already
be closed there.  This limitation is unlikely to change because it would
make resource handling much more complicated.  For such it's recommended
to not use the file type and manually open the file through
:func:`open_file`.

For a more complex example that also improves upon handling of the
pipelines have a look at the `imagepipe multi command chaining demo
<https://github.com/pallets/click/tree/master/examples/imagepipe>`__ in
the Click repository.  It implements a pipeline based image editing tool
that has a nice internal structure for the pipelines.


Overriding Defaults
-------------------

By default, the default value for a parameter is pulled from the
``default`` flag that is provided when it's defined, but that's not the
only place defaults can be loaded from.  The other place is the
:attr:`Context.default_map` (a dictionary) on the context.  This allows
defaults to be loaded from a configuration file to override the regular
defaults.

This is useful if you plug in some commands from another package but
you're not satisfied with the defaults.

The default map can be nested arbitrarily for each subcommand and
provided when the script is invoked.  Alternatively, it can also be
overridden at any point by commands.  For instance, a top-level command could
load the defaults from a configuration file.

Example usage:

.. click:example::

    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--port', default=8000)
    def runserver(port):
        click.echo('Serving on http://127.0.0.1:%d/' % port)

    if __name__ == '__main__':
        cli(default_map={
            'runserver': {
                'port': 5000
            }
        })

And in action:

.. click:run::

    invoke(cli, prog_name='cli', args=['runserver'], default_map={
        'runserver': {
            'port': 5000
        }
    })

Context Defaults
----------------

.. versionadded:: 2.0

Starting with Click 2.0 you can override defaults for contexts not just
when calling your script, but also in the decorator that declares a
command.  For instance given the previous example which defines a custom
``default_map`` this can also be accomplished in the decorator now.

This example does the same as the previous example:

.. click:example::

    import click

    CONTEXT_SETTINGS = dict(
        default_map={'runserver': {'port': 5000}}
    )

    @click.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    @click.option('--port', default=8000)
    def runserver(port):
        click.echo('Serving on http://127.0.0.1:%d/' % port)

    if __name__ == '__main__':
        cli()

And again the example in action:

.. click:run::

    invoke(cli, prog_name='cli', args=['runserver'])


Command Return Values
---------------------

.. versionadded:: 3.0

One of the new introductions in Click 3.0 is the full support for return
values from command callbacks.  This enables a whole range of features
that were previously hard to implement.

In essence any command callback can now return a value.  This return value
is bubbled to certain receivers.  One usecase for this has already been
show in the example of :ref:`multi-command-chaining` where it has been
demonstrated that chained multi commands can have callbacks that process
all return values.

When working with command return values in Click, this is what you need to
know:

-   The return value of a command callback is generally returned from the
    :meth:`BaseCommand.invoke` method.  The exception to this rule has to
    do with :class:`Group`\s:

    *   In a group the return value is generally the return value of the
        subcommand invoked.  The only exception to this rule is that the
        return value is the return value of the group callback if it's
        invoked without arguments and `invoke_without_command` is enabled.
    *   If a group is set up for chaining then the return value is a list
        of all subcommands' results.
    *   Return values of groups can be processed through a
        :attr:`MultiCommand.result_callback`.  This is invoked with the
        list of all return values in chain mode, or the single return
        value in case of non chained commands.

-   The return value is bubbled through from the :meth:`Context.invoke`
    and :meth:`Context.forward` methods.  This is useful in situations
    where you internally want to call into another command.

-   Click does not have any hard requirements for the return values and
    does not use them itself.  This allows return values to be used for
    custom decorators or workflows (like in the multi command chaining
    example).

-   When a Click script is invoked as command line application (through
    :meth:`BaseCommand.main`) the return value is ignored unless the
    `standalone_mode` is disabled in which case it's bubbled through.

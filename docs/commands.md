Advanced Groups and Context
=============================

.. currentmodule:: click

In addition to the capabilities covered in the previous section, Groups have more advanced capabilities that leverage the Context.

.. contents::
   :depth: 1
   :local:

Callback Invocation
-------------------

For a regular command, the callback is executed whenever the command runs.
If the script is the only command, it will always fire (unless a parameter
callback prevents it.  This for instance happens if someone passes
``--help`` to the script).

For groups, the situation looks different. In this case, the callback fires
whenever a subcommand fires.  What this means in practice is that an outer
command runs when an inner command runs:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    def cli(debug):
        click.echo(f"Debug mode is {'on' if debug else 'off'}")

    @cli.command()  # @cli, not @click!
    def sync():
        click.echo('Syncing')

Here is what this looks like:

.. click:run::

    invoke(cli, prog_name='tool.py')
    println()
    invoke(cli, prog_name='tool.py', args=['--debug', 'sync'])

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
        # by means other than the `if` block below)
        ctx.ensure_object(dict)

        ctx.obj['DEBUG'] = debug

    @cli.command()
    @click.pass_context
    def sync(ctx):
        click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")

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

.. _command-chaining:

Command Chaining
----------------

It is useful to invoke more than one subcommand in one call. For example,
``my-app validate build upload`` would invoke ``validate``, then ``build``, then
``upload``. To implement this, pass ``chain=True`` when creating a group.

.. click:example::

    @click.group(chain=True)
    def cli():
        pass

    @cli.command('validate')
    def validate():
        click.echo('validate')

    @cli.command('build')
    def build():
        click.echo('build')

You can invoke it like this:

.. click:run::

    invoke(cli, prog_name='my-app', args=['validate', 'build'])

When using chaining, there are a few restrictions:

-   Only the last command may use ``nargs=-1`` on an argument, otherwise the
    parser will not be able to find further commands.
-   It is not possible to nest groups below a chain group.
-   On the command line, options must be specified before arguments for each
    command in the chain.
-   The :attr:`Context.invoked_subcommand` attribute will be ``'*'`` because the
    parser doesn't know the full list of commands that will run yet.

.. _command-pipelines:

Command Pipelines
------------------

When using chaining, a common pattern is to have each command process the
result of the previous command.

A straightforward way to do this is to use :func:`make_pass_decorator` to pass
a context object to each command, and store and read the data on that object.

.. click:example::

    pass_ns = click.make_pass_decorator(dict, ensure=True)

    @click.group(chain=True)
    @click.argument("name")
    @pass_ns
    def cli(ns, name):
        ns["name"] = name

    @cli.command
    @pass_ns
    def lower(ns):
        ns["name"] = ns["name"].lower()

    @cli.command
    @pass_ns
    def show(ns):
        click.echo(ns["name"])

.. click:run::

    invoke(cli, prog_name="process", args=["Click", "show", "lower", "show"])

Another way to do this is to collect data returned by each command, then process
it at the end of the chain. Use the group's :meth:`~Group.result_callback`
decorator to register a function that is called after the chain is finished. It
is passed the list of return values as well as any parameters registered on the
group.

A command can return anything, including a function. Here's an example of that,
where each subcommand creates a function that processes the input, then the
result callback calls each function. The command takes a file, processes each
line, then outputs it. If no subcommands are given, it outputs the contents
of the file unchanged.

.. code-block:: python

    @click.group(chain=True, invoke_without_command=True)
    @click.argument("fin", type=click.File("r"))
    def cli(fin):
        pass

    @cli.result_callback()
    def process_pipeline(processors, fin):
        iterator = (x.rstrip("\r\n") for x in input)

        for processor in processors:
            iterator = processor(iterator)

        for item in iterator:
            click.echo(item)

    @cli.command("upper")
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()
        return processor

    @cli.command("lower")
    def make_lowercase():
        def processor(iterator):
            for line in iterator:
                yield line.lower()
        return processor

    @cli.command("strip")
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

For a more complex example that also improves upon handling of the pipelines,
see the `imagepipe example`_ in the Click repository. It implements a
pipeline based image editing tool that has a nice internal structure.

.. _imagepipe example: https://github.com/pallets/click/tree/main/examples/imagepipe


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

The default map can be nested arbitrarily for each subcommand:

.. code-block:: python

    default_map = {
        "debug": True,  # default for a top level option
        "runserver": {"port": 5000}  # default for a subcommand
    }

The default map can be provided when the script is invoked, or
overridden at any point by commands. For instance, a top-level command
could load the defaults from a configuration file.

Example usage:

.. click:example::

    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--port', default=8000)
    def runserver(port):
        click.echo(f"Serving on http://127.0.0.1:{port}/")

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
        click.echo(f"Serving on http://127.0.0.1:{port}/")

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
show in the example of :ref:`command-chaining` where it has been
demonstrated that chained groups can have callbacks that process
all return values.

When working with command return values in Click, this is what you need to
know:

-   The return value of a command callback is generally returned from the
    :meth:`Command.invoke` method.  The exception to this rule has to
    do with :class:`Group`\s:

    *   In a group the return value is generally the return value of the
        subcommand invoked.  The only exception to this rule is that the
        return value is the return value of the group callback if it's
        invoked without arguments and `invoke_without_command` is enabled.
    *   If a group is set up for chaining then the return value is a list
        of all subcommands' results.
    *   Return values of groups can be processed through a
        :attr:`Group.result_callback`.  This is invoked with the
        list of all return values in chain mode, or the single return
        value in case of non chained commands.

-   The return value is bubbled through from the :meth:`Context.invoke`
    and :meth:`Context.forward` methods.  This is useful in situations
    where you internally want to call into another command.

-   Click does not have any hard requirements for the return values and
    does not use them itself.  This allows return values to be used for
    custom decorators or workflows (like in the command chaining
    example).

-   When a Click script is invoked as command line application (through
    :meth:`Command.main`) the return value is ignored unless the
    `standalone_mode` is disabled in which case it's bubbled through.

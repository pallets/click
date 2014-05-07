Advanced Patterns
=================

.. currentmodule:: click

In addition to common functionality that is implemented in the library
itself, there are countless of patterns that can be implemented by extending
click.  This page should give some inspiration of what can be
accomplished.

.. _aliases:

Command Aliases
---------------

Many tools support aliases for commands.  For instance you can configure
``git`` to accept ``git ci`` as alias for ``git commit``.  Other tools
also support auto discovery for aliases by automatically shortening them.

Click does not support this out of the box but it's very easy to customize
the :class:`Group` or any other :class:`MultiCommand` to provide this
functionality.

As explained in :ref:`custom-multi-commands` a multi command can provide
two methods: :meth:`~MultiCommand.list_commands` and
:meth:`~MultiCommand.get_command`.  In this particular case you only need
to override the latter as you generally don't want to enumerate the
aliases on the help page to avoid confusion.

This following example implements a subclass of :class:`Group` that
accepts a prefix for a command.  So if there is a command called
``push`` it would accept ``pus`` as alias if it's unique:

.. click:example::

    class AliasedGroup(click.Group):

        def get_command(self, ctx, cmd_name):
            rv = click.Group.get_command(self, ctx, cmd_name)
            if rv is not None:
                return rv
            matches = [x for x in self.list_commands(ctx)
                       if x.startswith(cmd_name)]
            if not matches:
                return None
            elif len(matches) == 1:
                return click.Group.get_command(self, ctx, matches[0])
            ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

And it can be used like this then:

.. click:example::

    @click.command(cls=AliasedGroup)
    def cli():
        pass

    @cli.command()
    def push():
        pass

    @cli.command()
    def pop():
        pass

Invoking Other Commands
-----------------------

Sometimes it might be interesting to invoke one command from another
command.  This is generally a pattern that is discouraged with click but
possible nonetheless.  For this you can use the :func:`Context.invoke`
or :func:`Context.forward` methods.

They work similar but the difference is that :func:`Context.invoke` merely
invokes another command with the arguments you provide as a caller,
whereas :func:`Context.forward` fills in the arguments from the current
command.  Both accept the command as first argument and everything else is
passed onwards as you would expect.

Example:

.. click:example::

    cli = click.Group()

    @cli.command()
    @click.option('--count', default=1)
    def test(count):
        click.echo('Count: %d' % count)

    @cli.command()
    @click.option('--count', default=1)
    @click.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

And what it looks like:

.. click:run::

    invoke(cli, prog_name='cli', args=['dist'])

Showing Long Texts
------------------

In some situations you might want to show long texts on the terminal and
let a user scroll through it.  This can be achieved by using the
:func:`echo_via_pager` function which works similar to the :func:`echo`
function but always writes to stdout and, if possible, through a pager.

Example:

.. click:example::

    @click.command()
    def less():
        click.echo_via_pager('\n'.join('Line %d' % idx
                                       for idx in range(200)))


.. _callback-evaluation-order:

Callback Evaluation Order
-------------------------

Click works a bit different than some other command line parsers in that
it attempts to reconsiliate the order of arguments as defined by the
programmer with the order of arguments as defined by the user before
invoking any callbacks.

This is an important concept to understand when implementing complex
patterns ported from optparse or other systems to click.  A parameter
callback invocation in optparse happens as part of the parsing step
whereas a callback invocation in click happens after the parsing.

The main difference is that in optparse callbacks are invoked with the raw
value as it happens whereas a callback in click is invoked after the value
as fully converted.

Generally the order of invocation is driven by the order in which the user
provides the arguments to the script.  So if there is an option called
``--foo`` and an option called ``--bar`` and the user calls it as ``--bar
--foo`` then the callback for ``bar`` will fire before the one of ``foo``.

There are two exceptions to this rule which are important to know:

Eagerness:
    An option can be set to be "eager".  All eager parameters are
    evaluated before all non-eager parameters, but again in the order as
    they were provided on the command line by the user.

    This is important for parameters that execute and exit like ``--help``
    and ``--version``.  Both are eager parameters but whatever paramter
    comes first on the command line will win and exit the program.

Repeated parameters:
    If an option or argument is split up on the command line into multiple
    places because it's repeated (for instance ``--exclude foo --include
    baz --exclude bar``) the callback will fire based on the position of
    the first option.  So in this case the callback will fire for
    ``exclude`` and it will be passed both options (``foo`` and
    ``bar``), then the callback for ``include`` will fire with ``baz``
    only.

    Note that even if an parameter does not allow multiple versions click
    will still accept the position of the first, but it will ignore every
    value with the exception of the first.  The reason for this is to
    allow composability through shell aliases that set defaults.

Missing parameters:
    If an parameter is not defined on the command line the callback will
    still fire.  This is different from how it works in optparse where
    not defined values do not fire the callback.  Missing parameters fire
    their callbacks at the very end which makes it possible for them to
    default to values from a parameter that came before.

Most of the time you don't need to be concerned about any of this stuff,
but it's important to know how it works for some advanced cases.

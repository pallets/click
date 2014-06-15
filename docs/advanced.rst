Advanced Patterns
=================

.. currentmodule:: click

In addition to common functionality that is implemented in the library
itself, there are countless patterns that can be implemented by extending
Click.  This page should give some insight into what can be accomplished.

.. _aliases:

Command Aliases
---------------

Many tools support aliases for commands.  For instance, you can configure
``git`` to accept ``git ci`` as alias for ``git commit``.  Other tools
also support auto-discovery for aliases by automatically shortening them.

Click does not support this out of the box, but it's very easy to customize
the :class:`Group` or any other :class:`MultiCommand` to provide this
functionality.

As explained in :ref:`custom-multi-commands`, a multi command can provide
two methods: :meth:`~MultiCommand.list_commands` and
:meth:`~MultiCommand.get_command`.  In this particular case, you only need
to override the latter as you generally don't want to enumerate the
aliases on the help page in order to avoid confusion.

This following example implements a subclass of :class:`Group` that
accepts a prefix for a command.  If there were a command called ``push``,
it would accept ``pus`` as an alias (so long as it was unique):

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

And it can then be used like this:

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

Token Normalization
-------------------

.. versionadded:: 2.0

Starting with Click 2.0, it's possible to provide a function that is used
for normalizing tokens.  Tokens are option names, choice values, or command
values.  This can be used to implement case insensitive options, for
instance.

In order to use this feature, the context needs to be passed a function that
performs the normalization of the token.  For instance, you could have a
function that converts the token to lowercase:

.. click:example::

    CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())

    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option('--name', default='Pete')
    def cli(name):
        click.echo('Name: %s' % name)

And how it works on the command line:

.. click:run::

    invoke(cli, prog_name='cli', args=['--NAME=Pete'])

Invoking Other Commands
-----------------------

Sometimes, it might be interesting to invoke one command from another
command.  This is a pattern that is generally discouraged with Click, but
possible nonetheless.  For this, you can use the :func:`Context.invoke`
or :func:`Context.forward` methods.

They work similarly, but the difference is that :func:`Context.invoke` merely
invokes another command with the arguments you provide as a caller,
whereas :func:`Context.forward` fills in the arguments from the current
command.  Both accept the command as the first argument and everything else
is passed onwards as you would expect.

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


.. _callback-evaluation-order:

Callback Evaluation Order
-------------------------

Click works a bit differently than some other command line parsers in that
it attempts to reconcile the order of arguments as defined by the
programmer with the order of arguments as defined by the user before
invoking any callbacks.

This is an important concept to understand when porting complex
patterns to Click from optparse or other systems.  A parameter
callback invocation in optparse happens as part of the parsing step,
whereas a callback invocation in Click happens after the parsing.

The main difference is that in optparse, callbacks are invoked with the raw
value as it happens, whereas a callback in Click is invoked after the
value has been fully converted.

Generally, the order of invocation is driven by the order in which the user
provides the arguments to the script; if there is an option called ``--foo``
and an option called ``--bar`` and the user calls it as ``--bar
--foo``, then the callback for ``bar`` will fire before the one for ``foo``.

There are two exceptions to this rule which are important to know:

Eagerness:
    An option can be set to be "eager".  All eager parameters are
    evaluated before all non-eager parameters, but again in the order as
    they were provided on the command line by the user.

    This is important for parameters that execute and exit like ``--help``
    and ``--version``.  Both are eager parameters, but whatever parameter
    comes first on the command line will win and exit the program.

Repeated parameters:
    If an option or argument is split up on the command line into multiple
    places because it is repeated -- for instance, ``--exclude foo --include
    baz --exclude bar`` -- the callback will fire based on the position of
    the first option.  In this case, the callback will fire for
    ``exclude`` and it will be passed both options (``foo`` and
    ``bar``), then the callback for ``include`` will fire with ``baz``
    only.

    Note that even if a parameter does not allow multiple versions, Click
    will still accept the position of the first, but it will ignore every
    value except the first.  The reason for this is to allow composability
    through shell aliases that set defaults.

Missing parameters:
    If a parameter is not defined on the command line, the callback will
    still fire.  This is different from how it works in optparse where
    undefined values do not fire the callback.  Missing parameters fire
    their callbacks at the very end which makes it possible for them to
    default to values from a parameter that came before.

Most of the time you do not need to be concerned about any of this,
but it is important to know how it works for some advanced cases.

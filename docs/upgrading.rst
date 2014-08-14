Upgrading To Newer Releases
===========================

Click attempts the highest level of backwards compatibility but sometimes
this is not entirely possible.  In case we need to break backwards
compatibility this document gives you information about how to upgrade or
handle backwards compatibility properly.

.. _upgrade-to-3.2:

Upgrading to 3.2
----------------

Click 3.2 contains a fix for the :meth:`Context.invoke` function when used
with other commands.  The original intention of this function was to
invoke the other command as as if it came from the command line when it
was passed a context object instead of a function.  This use was only
documented in a single place in the documentation before and there was no
proper explanation for the method in the API documentation.

The core issue is that before 3.2 this call worked against intentions::

    ctx.invoke(other_command, 'arg1', 'arg2')

This was never intended to work as it does not allow Click to operate on
the parameters.  Given that this pattern was never documented and ill
intended the decision was made to change this behavior in a bugfix release
before it spreads by accident and developers depend on it.

The correct invocation for the above command is the following::

    ctx.invoke(other_command, name_of_arg1='arg1', name_of_arg2='arg2')

This also allowed us to fix the issue that defaults were not handled
properly by this function.

.. _upgrade-to-2.0:

Upgrading to 2.0
----------------

Click 2.0 has one breaking change which is the signature for parameter
callbacks.  Before 2.0, the callback was invoked with ``(ctx, value)``
whereas now it's ``(ctx, param, value)``.  This change was necessary as it
otherwise made reusing callbacks too complicated.

To ease the transition Click will still accept old callbacks.  Starting
with Click 3.0 it will start to issue a warning to stderr to encourage you
to upgrade.

In case you want to support both Click 1.0 and Click 2.0, you can make a
simple decorator that adjusts the signatures::

    import click
    from functools import update_wrapper

    def compatcallback(f):
        # Click 1.0 does not have a version string stored, so we need to
        # use getattr here to be safe.
        if getattr(click, '__version__', '0.0') >= '2.0':
            return f
        return update_wrapper(lambda ctx, value: f(ctx, None, value), f)

With that helper you can then write something like this::

    @compatcallback
    def callback(ctx, param, value):
        return value.upper()

Note that because Click 1.0 did not pass a parameter, the `param` argument
here would be `None`, so a compatibility callback could not use that
argument.

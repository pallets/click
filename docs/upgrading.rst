Upgrading To Newer Releases
===========================

Click attempts the highest level of backwards compatibility but sometimes
this is not entirely possible.  In case we need to break backwards
compatibility this document gives you information about how to upgrade or
handle backwards compatibility properly.

.. _upgrade-to-2.0:

Upgrading to 2.0
----------------

Click 2.0 has one breaking change which is the signature for parameter
callbacks.  Before 2.0 the callback was invoked with ``(ctx, value)``
wheras now it's ``(ctx, param, value)``.  This change was necessary as it
otherwise made reusing callbacks too complicated.

To ease the transition Click will still accept old callbacks but it will
issue a warning to stderr to encourage you to upgrade.

In case you want to support both Click 1.0 and Click 2.0 you can make a
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

Note that because Click 1.0 did not pass a parameter the `param` argument
here would be `None` so a compatibility callback could not use that
argument.

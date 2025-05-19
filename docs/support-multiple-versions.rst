Supporting Multiple Versions
============================

Supporting multiple versions of ``click`` in a single codebase is usually
straightforward. Most features of ``click`` are stable across releases, and don't
require special handling.

However, feature releases may deprecate and change APIs. Some features require special
handling to function correctly across a range of versions.

click 8.1.x and 8.2.x
---------------------

This section will help you support click version 8.1 and 8.2 simultaneously.


``ParamType`` methods require ``ctx``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In 8.2, several methods of ``ParamType`` now accept a ``ctx: click.Context`` argument.
By way of example, this section covers ``ParamType.get_metavar``.

To handle this while supporting 8.1, you can define a decorator:

.. code-block:: python

    import functools
    import typing as t

    C = t.TypeVar("C", bound=t.Callable[..., t.Any])

    def shim_get_metavar(f: C) -> C:
        @functools.wraps(f)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            if "ctx" not in kwargs:
                kwargs["ctx"] = click.get_current_context(silent=True)
            return f(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

And then use the decorator on your ``ParamType`` to write a compatible ``get_metavar``
method.
For example:

.. code-block:: python

    import click

    class CommaDelimitedString(click.ParamType):
        @shim_get_metavar
        def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str:
            return "TEXT,TEXT,..."


.. note::

    This methodology, creating a wrapper which does feature detection based on ``"ctx"``
    being in ``kwargs``, works for several other methods, e.g.
    ``ParamType.get_missing_message``.

Parameters
==========

.. currentmodule:: click

Click supports two types of parameters for scripts: options and arguments.
There is generally some confusion among authors of command line scripts of
when to use which, so here is a quick overview of the differences.  As its
name indicates, an option is optional.  While arguments can be optional
within reason, they are much more restricted in how optional they can be.

To help you decide between options and arguments, the recommendation is
to use arguments exclusively for things like going to subcommands or input
filenames / URLs, and have everything else be an option instead.

Differences
-----------

Arguments can do less than options.  The following features are only
available for options:

*   automatic prompting for missing input
*   act as flags (boolean or otherwise)
*   option values can be pulled from environment variables, arguments can not
*   options are fully documented in the help page, arguments are not
    (:ref:`this is intentional <documenting-arguments>` as arguments
    might be too specific to be automatically documented)

On the other hand arguments, unlike options, can accept an arbitrary number
of arguments.  Options can strictly ever only accept a fixed number of
arguments (defaults to 1), or they may be specified multiple times using
:ref:`multiple-options`.

Parameter Types
---------------

Parameters can be of different types.  Types can be implemented with
different behavior and some are supported out of the box:

``str`` / :data:`click.STRING`:
    The default parameter type which indicates unicode strings.

``int`` / :data:`click.INT`:
    A parameter that only accepts integers.

``float`` / :data:`click.FLOAT`:
    A parameter that only accepts floating point values.

``bool`` / :data:`click.BOOL`:
    A parameter that accepts boolean values. This is automatically used
    for boolean flags. The string values "1", "true", "t", "yes", "y",
    and "on" convert to ``True``. "0", "false", "f", "no", "n", and
    "off" convert to ``False``.

:data:`click.UUID`:
    A parameter that accepts UUID values.  This is not automatically
    guessed but represented as :class:`uuid.UUID`.

.. autoclass:: File
   :noindex:

.. autoclass:: Path
   :noindex:

.. autoclass:: Choice
   :noindex:

.. autoclass:: IntRange
   :noindex:

.. autoclass:: FloatRange
  :noindex:

.. autoclass:: DateTime
   :noindex:

Custom parameter types can be implemented by subclassing
:class:`click.ParamType`.  For simple cases, passing a Python function that
fails with a `ValueError` is also supported, though discouraged.

.. _parameter_names:

Parameter Names
---------------

Parameters (both options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

Arguments take only one positional name. To provide a different name for
use in help text, see :ref:`doc-meta-variables`.

Options can have many names that may be prefixed with one or two dashes.
Names with one dash are parsed as short options, names with two are
parsed as long options. If a name is not prefixed, it is used as the
Python argument name and not parsed as an option name. Otherwise, the
first name with a two dash prefix is used, or the first with a one dash
prefix if there are none with two. The prefix is removed and dashes are
converted to underscores to get the Python argument name.


Implementing Custom Types
-------------------------

To implement a custom type, you need to subclass the :class:`ParamType`
class. Override the :meth:`~ParamType.convert` method to convert the
value from a string to the correct type.

The following code implements an integer type that accepts hex and octal
numbers in addition to normal integers, and converts them into regular
integers.

.. code-block:: python

    import click

    class BasedIntParamType(click.ParamType):
        name = "integer"

        def convert(self, value, param, ctx):
            if isinstance(value, int):
                return value

            try:
                if value[:2].lower() == "0x":
                    return int(value[2:], 16)
                elif value[:1] == "0":
                    return int(value, 8)
                return int(value, 10)
            except ValueError:
                self.fail(f"{value!r} is not a valid integer", param, ctx)

    BASED_INT = BasedIntParamType()

The :attr:`~ParamType.name` attribute is optional and is used for
documentation. Call :meth:`~ParamType.fail` if conversion fails. The
``param`` and ``ctx`` arguments may be ``None`` in some cases such as
prompts.

Values from user input or the command line will be strings, but default
values and Python arguments may already be the correct type. The custom
type should check at the top if the value is already valid and pass it
through to support those cases.

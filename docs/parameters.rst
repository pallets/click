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
    (this is intentional as arguments might be too specific to be
    automatically documented)

On the other hand arguments, unlike options, can accept an arbitrary number
of arguments.  Options can strictly ever only accept a fixed number of
arguments (defaults to 1).

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
    A parameter that accepts boolean values.  This is automatically used
    for boolean flags.  If used with string values ``1``, ``yes``, ``y``
    and ``true`` convert to `True` and ``0``, ``no``, ``n`` and ``false``
    convert to `False`.

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

Custom parameter types can be implemented by subclassing
:class:`click.ParamType`.  For simple cases, passing a Python function that
fails with a `ValueError` is also supported, though discouraged.

Parameter Names
---------------

Parameters (both options and arguments) accept a number of positional
arguments which are the parameter declarations.  Each string with a
single dash is added as short argument; each string starting with a double
dash as long one.  If a string is added without any dashes, it becomes the
internal parameter name which is also used as variable name.

If a parameter is not given a name without dashes, a name is generated
automatically by taking the longest argument and converting all dashes to
underscores.  For an option with ``('-f', '--foo-bar')``, the parameter
name is `foo_bar`.  For an option with ``('-x',)``, the parameter is `x`.
For an option with ``('-f', '--filename', 'dest')``, the parameter is
called `dest`.

Implementing Custom Types
-------------------------

To implement a custom type, you need to subclass the :class:`ParamType`
class.  Types can be invoked with or without context and parameter object,
which is why they need to be able to deal with this.

The following code implements an integer type that accepts hex and octal
numbers in addition to normal integers, and converts them into regular
integers::

    import click

    class BasedIntParamType(click.ParamType):
        name = 'integer'

        def convert(self, value, param, ctx):
            try:
                if value[:2].lower() == '0x':
                    return int(value[2:], 16)
                elif value[:1] == '0':
                    return int(value, 8)
                return int(value, 10)
            except ValueError:
                self.fail('%s is not a valid integer' % value, param, ctx)

    BASED_INT = BasedIntParamType()

As you can see, a subclass needs to implement the :meth:`ParamType.convert`
method and optionally provide the :attr:`ParamType.name` attribute.  The
latter can be used for documentation purposes.

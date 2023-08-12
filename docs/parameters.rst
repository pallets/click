Parameters
==========

.. currentmodule:: click

Click supports only two types  of parameters for scripts (by design): options and arguments.

Options
----------------

*   are optional.
*   Recommended to use for everything except subcommands, urls, or files.
*   Can take a fixed number of arguments. The default is 1. They may be specified multiple times using :ref:`multiple-options`.
*   Are fully documented by the help page.
*   Have automatic prompting for missing input.
*   Can act as flags (boolean or otherwise).
*   Can be pulled from environment variables.

Arguments
----------------

*   are optional with in reason, but not entirely so.
*   Recommended to use for subcommands, urls, or files.
*   Can take an arbitrary number of arguments.
*   Are not fully documented by the help page since they may be too specific to be automatically documented. How to document args is covered in :ref:`documenting args section <documenting-arguments>`.
*   Can be pulled from environment variables but only explicitly named ones. See :ref:`environment-variables` for further explanation.

.. _parameter_names:

Parameter Names
---------------

Parameters (both options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

.. click:example::

    @click.command()
    @click.argument('filename')
    @click.option('-t', '--times', type=int)
    def multi_echo(filename, times):
        """Print value of SRC environment variable."""
        for x in range(times):
            click.echo(filename)

In the above example the argument's name is ``filename``. The name must match the python arg name. To provide a different name for use in help text, see :ref:`doc-meta-variables`.
The option's names are ``-t`` and ``--times``. More names are available for options and are covered in :ref:`options`.

And what it looks like when run:

.. click:run::

    invoke(multi_echo, ['--times=3', 'index.txt'], prog_name='multi_echo')

Parameter Types
---------------

The supported parameter types are:

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

How to Implement Custom Types
-------------------------------

To implement a custom type, you need to subclass the :class:`ParamType` class. For simple cases, passing a Python function that fails with a `ValueError` is also supported, though discouraged. Override the :meth:`~ParamType.convert` method to convert the value from a string to the correct type.

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

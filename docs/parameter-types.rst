.. _parameter-types:

Parameter Types
==================

.. currentmodule:: click

Specifying the parameter type with the ``type`` kwarg allows Click add data to your help pages and helps with the handling of the types. Most examples are done with argument, but types are available to options and arguments.

.. contents::
    :depth: 2
    :local:

Built-in Types Examples
------------------------

.. _choice-opts:

Choice
^^^^^^^^^^^^^^^^^^^^^^

Sometimes, you want to have a parameter be a choice of a list of values.
In that case you can use :class:`Choice` type.  It can be instantiated
with a list of valid values.  The originally passed choice will be returned,
not the str passed on the command line.  Token normalization functions and
``case_sensitive=False`` can cause the two to be different but still match.

Example:

.. click:example::

    @click.command()
    @click.option('--hash-type',
                  type=click.Choice(['MD5', 'SHA1'], case_sensitive=False))
    def digest(hash_type):
        click.echo(hash_type)

What it looks like:

.. click:run::

    invoke(digest, args=['--hash-type=MD5'])
    println()
    invoke(digest, args=['--hash-type=md5'])
    println()
    invoke(digest, args=['--hash-type=foo'])
    println()
    invoke(digest, args=['--help'])

Only pass the choices as list or tuple. Other iterables (like
generators) may lead to unexpected results.

Choices work with options that have ``multiple=True``. If a ``default``
value is given with ``multiple=True``, it should be a list or tuple of
valid choices.

Choices should be unique after considering the effects of
``case_sensitive`` and any specified token normalization function.

.. versionchanged:: 7.1
    The resulting value from an option will always be one of the
    originally passed choices regardless of ``case_sensitive``.

Built-in Types Listing
-----------------------
The supported parameter types are:

*   ``str`` / :data:`click.STRING`: The default parameter type which indicates unicode strings.

*   ``int`` / :data:`click.INT`: A parameter that only accepts integers.

*   ``float`` / :data:`click.FLOAT`: A parameter that only accepts floating point values.

*   ``bool`` / :data:`click.BOOL`: A parameter that accepts boolean values. This is automatically used
    for boolean flags. The string values "1", "true", "t", "yes", "y",
    and "on" convert to ``True``. "0", "false", "f", "no", "n", and
    "off" convert to ``False``.

*   :data:`click.UUID`:
    A parameter that accepts UUID values.  This is not automatically
    guessed but represented as :class:`uuid.UUID`.

*   .. autoclass:: Choice
       :noindex:

*   .. autoclass:: DateTime
       :noindex:

*   .. autoclass:: File
       :noindex:

*   .. autoclass:: FloatRange
       :noindex:

*   .. autoclass:: IntRange
       :noindex:

*   .. autoclass:: Path
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

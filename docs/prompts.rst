User Input Prompts
==================

.. currentmodule:: click

Click supports prompts in two different places.  The first is automated
prompts when the parameter handling happens, and the second is to ask for
prompts at a later point independently.

This can be accomplished with the :func:`prompt` function, which asks for
valid input according to a type, or the :func:`confirm` function, which asks
for confirmation (yes/no).

Option Prompts
--------------

Option prompts are integrated into the option interface.  See
:ref:`option-prompting` for more information.  Internally, it
automatically calls either :func:`prompt` or :func:`confirm` as necessary.

Input Prompts
-------------

To manually ask for user input, you can use the :func:`prompt` function.
By default, it accepts any Unicode string, but you can ask for any other
type.  For instance, you can ask for a valid integer::

    value = click.prompt('Please enter a valid integer', type=int)

Additionally, the type will be determined automatically if a default value is
provided.  For instance, the following will only accept floats::

    value = click.prompt('Please enter a number', default=42.0)

You can customize how to display and format the prompt via providing
:param:`builder_cls` as an instance of :class:`PromptBuilder`.

Confirmation Prompts
--------------------

To ask if a user wants to continue with an action, the :func:`confirm`
function comes in handy.  By default, it returns the result of the prompt
as a boolean value::

    if click.confirm('Do you want to continue?'):
        click.echo('Well done!')

There is also the option to make the function automatically abort the
execution of the program if it does not return ``True``::

    click.confirm('Do you want to continue?', abort=True)

As in `Input Prompts`_ described above, you can customize how to display
and format the prompt via providing :param:`builder_cls` as an instance
of :class:`PromptBuilder`.

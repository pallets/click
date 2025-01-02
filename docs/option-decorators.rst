Options Shortcut Decorators
===========================

.. currentmodule:: click

For convenience commonly used combinations of options arguments are available as their own decorators.

.. contents::
    :depth: 2
    :local:

Password Option
------------------

Click supports hidden prompts and asking for confirmation.  This is
useful for password input:

.. click:example::

    import codecs

    @click.command()
    @click.option(
        "--password", prompt=True, hide_input=True,
        confirmation_prompt=True
    )
    def encode(password):
        click.echo(f"encoded: {codecs.encode(password, 'rot13')}")

.. click:run::

    invoke(encode, input=['secret', 'secret'])

Because this combination of parameters is quite common, this can also be
replaced with the :func:`password_option` decorator:

.. code-block:: python

    @click.command()
    @click.password_option()
    def encrypt(password):
        click.echo(f"encoded: to {codecs.encode(password, 'rot13')}")

Confirmation Option
--------------------

For dangerous operations, it's very useful to be able to ask a user for
confirmation.  This can be done by adding a boolean ``--yes`` flag and
asking for confirmation if the user did not provide it and to fail in a
callback:

.. click:example::

    def abort_if_false(ctx, param, value):
        if not value:
            ctx.abort()

    @click.command()
    @click.option('--yes', is_flag=True, callback=abort_if_false,
                  expose_value=False,
                  prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')

And what it looks like on the command line:

.. click:run::

    invoke(dropdb, input=['n'])
    invoke(dropdb, args=['--yes'])

Because this combination of parameters is quite common, this can also be
replaced with the :func:`confirmation_option` decorator:

.. click:example::

    @click.command()
    @click.confirmation_option(prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')

API
===

.. module:: click

This part of the documentation lists the full API reference of all public
classes and functions.

Decorators
----------

.. autofunction:: command

.. autofunction:: group

.. autofunction:: argument

.. autofunction:: option

.. autofunction:: password_option

.. autofunction:: confirmation_option

.. autofunction:: version_option

.. autofunction:: help_option

.. autofunction:: pass_context

.. autofunction:: pass_obj

.. autofunction:: make_pass_decorator

Utilities
---------

.. autofunction:: echo

.. autofunction:: echo_via_pager

.. autofunction:: prompt

.. autofunction:: confirm

.. autofunction:: progressbar

.. autofunction:: clear

.. autofunction:: style

.. autofunction:: unstyle

.. autofunction:: secho

.. autofunction:: edit

.. autofunction:: launch

.. autofunction:: getchar

.. autofunction:: pause

.. autofunction:: get_terminal_size

.. autofunction:: get_binary_stream

.. autofunction:: get_text_stream

.. autofunction:: get_app_dir

.. autofunction:: format_filename

Commands
--------

.. autoclass:: BaseCommand
   :members:

.. autoclass:: Command
   :members:

.. autoclass:: MultiCommand
   :members:

.. autoclass:: Group
   :members:

.. autoclass:: CommandCollection
   :members:

Parameters
----------

.. autoclass:: Parameter
   :members:

.. autoclass:: Option

.. autoclass:: Argument

Context
-------

.. autoclass:: Context
   :members:

Types
-----

.. autodata:: STRING

.. autodata:: INT

.. autodata:: FLOAT

.. autodata:: BOOL

.. autodata:: UUID

.. autoclass:: File

.. autoclass:: Path

.. autoclass:: Choice

.. autoclass:: IntRange

.. autoclass:: ParamType
   :members:

Exceptions
----------

.. autoexception:: ClickException

.. autoexception:: Abort

.. autoexception:: UsageError

.. autoexception:: BadParameter

.. autoexception:: FileError

Formatting
----------

.. autoclass:: HelpFormatter
   :members:

.. autofunction:: wrap_text

Parsing
-------

.. autoclass:: OptionParser
   :members:

Testing
-------

.. currentmodule:: click.testing

.. autoclass:: CLIRunner
   :members:

.. autoclass:: Result
   :members:

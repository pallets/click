API
===

.. module:: click

This part of the documentation shows the full API reference of all public
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

Helper Functions
----------------

.. autofunction:: echo

.. autofunction:: echo_via_pager

.. autofunction:: prompt

.. autofunction:: confirm

.. autofunction:: get_terminal_size

Commands
--------

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

.. autoclass:: Choice

.. autoclass:: ParamType

Exceptions
----------

.. autoexception:: Abort

.. autoexception:: UsageError

Formatting
----------

.. autoclass:: HelpFormatter
   :members:

.. autofunction:: wrap_text

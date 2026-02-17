Glossary
========

This glossary defines key terms used throughout Click's documentation.

.. glossary::
   :sorted:

   Argument
       A positional parameter passed to a command without a name prefix.
       Arguments are identified by their position in the command line.
       For example, in ``mycli command file.txt``, ``file.txt`` is an argument.

   Callback
       A function that is invoked when a parameter is processed. Callbacks can be
       attached to options or arguments for custom validation or processing.
       See :doc:`/parameters` for more information.

   Command
       A function decorated with ``@click.command()`` or ``@click.group()`` 
       that can be invoked from the command line. Commands can accept options
       and arguments.

   Command Line Interface (CLI)
       A text-based interface for interacting with a program through commands,
       options, and arguments. Click helps you build CLIs in Python.

   Context
       An object that carries state between commands in a group hierarchy.
       The context is created for each command invocation and can be accessed
       via the ``@click.pass_context`` decorator.

   Flag
       A boolean option that doesn't take a value (e.g., ``--verbose`` or ``-v``).
       Flags are either present (True) or absent (False).

   Group
       A command that contains other commands (subcommands). Created with
       ``@click.group()``. Groups allow organizing commands hierarchically.

   Multi-command
       A command that groups multiple subcommands together. Groups and
       multi-commands are similar concepts in Click.

   Option
       A named parameter passed to a command, typically with a dash prefix
       (e.g., ``--name value`` or ``-n value``). Options can have values
       or be used as flags.

   Parameter
       The general term for both options and arguments that can be passed
       to a command. Parameters are defined using decorators like
       ``@click.option()`` or ``@click.argument()``.

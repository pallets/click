# -*- coding: utf-8 -*-
"""
    click
    ~~~~~

    click is a simple Python module that wraps the stdlib's optparse to make
    writing command line scripts fun.  Unlike other modules it's based around
    a simple API that does not come with too much magic and is composable.

    In case optparse ever goes away from the stdlib it will be shipped by
    this module.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

# Core classes
from .core import Context, Command, MultiCommand, Group, CommandCollection, \
     Parameter, Option, Argument

# Decorators
from .decorators import pass_context, pass_obj, make_pass_decorator, \
     command, group, argument, option, confirmation_option, \
     password_option, version_option, help_option

# Types
from .types import ParamType, File, Choice, STRING, INT, FLOAT, BOOL

# Helper functions
from .helpers import prompt, confirm, get_terminal_size

# Exceptions
from .exceptions import UsageError, Abort


__all__ = [
    # Core classes
    'Context', 'Command', 'MultiCommand', 'Group', 'CommandCollection',
    'Parameter', 'Option', 'Argument',

    # Decorators
    'pass_context', 'pass_obj', 'make_pass_decorator', 'command', 'group',
    'argument', 'option', 'confirmation_option', 'password_option',
    'version_option', 'help_option',

    # Types
    'ParamType', 'File', 'Choice', 'STRING', 'INT', 'FLOAT', 'BOOL',

    # Helper functions
    'prompt', 'confirm', 'get_terminal_size',

    # Exceptions
    'UsageError', 'Abort',
]

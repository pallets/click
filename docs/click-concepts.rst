Click Concepts
================

This section covers concepts about Click's design.

.. contents::
    :depth: 1
    :local:

.. _callback-evaluation-order:

Callback Evaluation Order
-------------------------

Click works a bit differently than some other command line parsers in that
it attempts to reconcile the order of arguments as defined by the
programmer with the order of arguments as defined by the user before
invoking any callbacks.

This is an important concept to understand when porting complex
patterns to Click from optparse or other systems.  A parameter
callback invocation in optparse happens as part of the parsing step,
whereas a callback invocation in Click happens after the parsing.

The main difference is that in optparse, callbacks are invoked with the raw
value as it happens, whereas a callback in Click is invoked after the
value has been fully converted.

Generally, the order of invocation is driven by the order in which the user
provides the arguments to the script; if there is an option called ``--foo``
and an option called ``--bar`` and the user calls it as ``--bar
--foo``, then the callback for ``bar`` will fire before the one for ``foo``.

There are three exceptions to this rule which are important to know:

Eagerness:
    An option can be set to be "eager".  All eager parameters are
    evaluated before all non-eager parameters, but again in the order as
    they were provided on the command line by the user.

    This is important for parameters that execute and exit like ``--help``
    and ``--version``.  Both are eager parameters, but whatever parameter
    comes first on the command line will win and exit the program.

Repeated parameters:
    If an option or argument is split up on the command line into multiple
    places because it is repeated -- for instance, ``--exclude foo --include
    baz --exclude bar`` -- the callback will fire based on the position of
    the first option.  In this case, the callback will fire for
    ``exclude`` and it will be passed both options (``foo`` and
    ``bar``), then the callback for ``include`` will fire with ``baz``
    only.

    Note that even if a parameter does not allow multiple versions, Click
    will still accept the position of the first, but it will ignore every
    value except the last.  The reason for this is to allow composability
    through shell aliases that set defaults.

Missing parameters:
    If a parameter is not defined on the command line, the callback will
    still fire.  This is different from how it works in optparse where
    undefined values do not fire the callback.  Missing parameters fire
    their callbacks at the very end which makes it possible for them to
    default to values from a parameter that came before.

Most of the time you do not need to be concerned about any of this,
but it is important to know how it works for some advanced cases.


.. _glossary:

Glossary
--------

This section defines key terms used throughout Click's documentation to ensure
consistent usage.

.. glossary::

    Option
        A command-line parameter that is optional and typically starts with
        ``--`` (e.g., ``--verbose``). Options can accept values or be boolean
        flags.

    Flag
        A boolean option that enables or disables a feature when present.
        Flags do not require a value; their presence alone determines the
        state (e.g., ``--force``).

    Command Line Application
        A program that is executed from a terminal or shell prompt. Click
        specializes in building these applications, which receive input via
        arguments and options passed on the command line.

    Command Line Utility
        A synonym for command line application, typically referring to smaller,
        single-purpose tools that perform specific tasks (e.g., ``ls``, ``grep``).

    Terminal
        A text-based interface for interacting with a computer. Also known as
        a command-line interface (CLI), console, or shell. The terminal
        receives input from the user and displays output from the application.

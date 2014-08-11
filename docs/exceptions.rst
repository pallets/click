Exception Handling
==================

.. currentmodule:: click

Click internally uses exceptions to signal various error conditions that
the user of the application might have caused.  Primarily this is things
like incorrect usage.

Where are Errors Handled?
-------------------------

Click's main error handling is happening in :meth:`BaseCommand.main`.  In
there it handles all subclasses of :exc:`ClickException` as well as the
standard :exc:`EOFError` and :exc:`KeyboardInterrupt` exceptions.  The
latter are internally translated into a :exc:`Abort`.

The logic applied is the following:

1.  If an :exc:`EOFError` or :exc:`KeyboardInterrupt` happens, reraise it
    as :exc:`Abort`.
2.  If an :exc:`ClickException` is raised, invoke the
    :meth:`ClickException.show` method on it to display it and then exit
    the program with :attr:`ClickException.exit_code`.
3.  If an :exc:`Abort` exception is raised print the string ``Aborted!``
    to standard error and exit the program with exit code ``1``.
4.  if it goes through well, exit the program with exit code ``0``.

What if I don't want that?
--------------------------

Generally you always have the option to invoke the :meth:`invoke` method
yourself.  For instance if you have a :class:`Command` you can invoke it
manually like this::

    ctx = command.make_context('command-name', ['args', 'go', 'here'])
    with ctx:
        result = command.invoke(ctx)

In this case exceptions will not be handled at all and bubbled up as you
would expect.

Starting with Click 3.0 you can also use the :meth:`Command.main` method
but disable the standalone mode which will do two things: disable
exception handling and disable the implicit :meth:`sys.exit` at the end.

So you can do something like this::

    command.main(['command-name', 'args', 'go', 'here'],
                 standalone_mode=False)

Which Exceptions Exist?
-----------------------

Click has two exception bases: :exc:`ClickException` which is raised for
all exceptions that Click wants to signal to the user and :exc:`Abort`
which is used to instruct Click to abort the execution.

A :exc:`ClickException` has a :meth:`~ClickException.show` method which
can render an error message to stderr or the given file object.  If you
want to use the exception yourself for doing something check the API docs
about what else they provide.

The following common subclasses exist:

*   :exc:`UsageError` to inform the user that something went wrong.
*   :exc:`BadParameter` to inform the user that something went wrong with
    a specific parameter.  These are often handled internally in Click and
    augmented with extra information if possible.  For instance if those
    are raised from a callback Click will automatically augment it with
    the parameter name if possible.
*   :exc:`FileError` this is an error that is raised by the
    :exc:`FileType` if Click encounters issues opening the file.

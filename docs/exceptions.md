(exception-handling-exit-codes)=

# Exception Handling and Exit Codes

```{eval-rst}
.. currentmodule:: click
```

Click internally uses exceptions to signal various error conditions that
the user of the application might have caused. Primarily this is things
like incorrect usage.

```{contents}
:depth: 1
:local:
```

## Where are Errors Handled?

Click's main error handling is happening in {meth}`Command.main`. In
there it handles all subclasses of {exc}`ClickException` as well as the
standard {exc}`EOFError` and {exc}`KeyboardInterrupt` exceptions.

The table below lists every way a command can end, and what Click does
for each. The middle column is the default. The last column applies when
{meth}`Command.main` runs with ``standalone_mode=False``, which the next
section describes.

| How the command ends | Standalone mode | ``standalone_mode=False`` |
| --- | --- | --- |
| It returns | Exit with code ``0`` | Return the value of {meth}`Command.invoke` |
| It called {meth}`Context.exit` | Exit with the given code | Return the given code |
| It raised a {exc}`ClickException` | Call {meth}`ClickException.show`, then exit with {attr}`ClickException.exit_code` | Propagate it |
| The user pressed {kbd}`Ctrl+C`, which raises a {exc}`KeyboardInterrupt` | Print a blank line, then ``Aborted!`` to standard error, and exit with code ``1`` | Print a blank line, then raise {exc}`Abort` with the original exception as its ``__cause__`` |
| The user pressed {kbd}`Ctrl+D`, or {kbd}`Ctrl+Z` on Windows, which raises an {exc}`EOFError` | The same as {kbd}`Ctrl+C` | The same as {kbd}`Ctrl+C` |
| It raised an {exc}`Abort` | Print ``Aborted!`` to standard error, and exit with code ``1`` | Propagate it |
| The output pipe closed early, which raises an {exc}`OSError` with ``EPIPE`` | Silence the flush errors, and exit with code ``1`` | The same |
| It raised any other exception | Propagate it | Propagate it |

Click writes the message and exits once that handling is done. An
interrupt arriving during this last step cannot change the exit code the
table gave. It can only cost the message.

## What if I Don't Want That?

Generally you always have the option to invoke the {meth}`Command.invoke`
method yourself. For instance if you have a {class}`Command` you can
invoke it manually like this:

```python
ctx = command.make_context("command-name", ["args", "go", "here"])
with ctx:
    result = command.invoke(ctx)
```

In this case exceptions will not be handled at all and bubbled up as you
would expect.

Starting with Click 3.0 you can also use the {meth}`Command.main` method
but disable the standalone mode which will do two things: disable
exception handling and disable the implicit {func}`sys.exit` at the end.

So you can do something like this:

```python
command.main(
    ["command-name", "args", "go", "here"],
    standalone_mode=False,
)
```

This is also how you replace the ``Aborted!`` message. Standalone mode
turns off every row of the table above, so catch the cases you want to
keep and write your own message for the rest:

```python
try:
    command.main(
        ["command-name", "args", "go", "here"],
        standalone_mode=False,
    )
except click.Abort:
    click.echo("Bye!", err=True)
    raise SystemExit(1)
except click.ClickException as e:
    e.show()
    raise SystemExit(e.exit_code)
```

## Which Exceptions Exist?

Click has two exception bases: {exc}`ClickException` which is raised for
all exceptions that Click wants to signal to the user and {exc}`Abort`
which is used to instruct Click to abort the execution.

A {exc}`ClickException` has a {meth}`ClickException.show` method which
can render an error message to stderr or the given file object. If you
want to use the exception yourself for doing something check the API docs
about what else they provide.

The following common subclasses exist:

- {exc}`UsageError` to inform the user that something went wrong.
- {exc}`BadParameter` to inform the user that something went wrong with
  a specific parameter. These are often handled internally in Click and
  augmented with extra information if possible. For instance if those
  are raised from a callback Click will automatically augment it with
  the parameter name if possible.
- {exc}`FileError` this is an error that is raised by the
  {class}`FileType` if Click encounters issues opening the file.

(help-page-exit-codes)=

## Help Pages and Exit Codes

Triggering the a help page intentionally (by passing in ``--help``)
returns exit code 0. If a help page is displayed due to incorrect user
input, the program returns exit code 2. See {ref}`exit-codes` for more
general information.

For clarity, here is an example.

```{eval-rst}
.. click:example::

    @click.group('printer_group')
    def printer_group():
        pass

    @printer_group.command('printer')
    @click.option('--this')
    def printer(this):
        if this:
            click.echo(this)

.. click:run::
    invoke(printer_group, args=['--help'])

The above invocation returns exit code 0.

.. click:run::
    invoke(printer_group, args=[])
```

The above invocation returns exit code 2 since the user invoked the command incorrectly. However, since this is such a common error when first using a command, Click invokes the help page for the user. To see that `printer-group` is an invalid invocation, turn `no_args_is_help` off.

```{eval-rst}
.. click:example::

    @click.group('printer_group', no_args_is_help=False)
    def printer_group():
        pass

    @printer_group.command('printer')
    @click.option('--this')
    def printer(this):
        if this:
            click.echo(this)

.. click:run::
    invoke(printer_group, args=[])
```

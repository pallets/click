.. currentmodule:: click.shell_completion

Shell Completion
================

Click provides tab completion support for Bash (version 4.4 and up),
Zsh, and Fish. It is possible to add support for other shells too, and
suggestions can be customized at multiple levels.

Shell completion suggests command names, option names, and values for
choice, file, and path parameter types. Options are only listed if at
least a dash has been entered. Hidden commands and options are not
shown.

.. code-block:: text

    $ repo <TAB><TAB>
    clone  commit  copy  delete  setuser
    $ repo clone -<TAB><TAB>
    --deep  --help  --rev  --shallow  -r


Enabling Completion
-------------------

Completion is only available if a script is installed and invoked
through an entry point, not through the ``python`` command. See
:doc:`/setuptools`. Once the executable is installed, calling it with
a special environment variable will put Click in completion mode.

In order for completion to be used, the user needs to register a special
function with their shell. The script is different for every shell, and
Click will output it when called with ``_{PROG_NAME}_COMPLETE`` set to
``source_{shell}``. ``{PROG_NAME}`` is the executable name in uppercase
with dashes replaced by underscores. The built-in shells are ``bash``,
``zsh``, and ``fish``.

Provide your users with the following instructions customized to your
program name. This uses ``foo-bar`` as an example.

.. tabs::

    .. group-tab:: Bash

        Add this to ``~/.bashrc``:

        .. code-block:: bash

            eval "$(_FOO_BAR_COMPLETE=source_bash foo-bar)"

    .. group-tab:: Zsh

        Add this to ``~/.zshrc``:

        .. code-block:: zsh

            eval "$(_FOO_BAR_COMPLETE=source_zsh foo-bar)"

    .. group-tab:: Fish

        Add this to ``~/.config/fish/completions/foo-bar.fish``:

        .. code-block:: fish

            eval (env _FOO_BAR_COMPLETE=source_fish foo-bar)

        This is the same file used for the activation script method
        below. For Fish it's probably always easier to use that method.

Using ``eval`` means that the command is invoked and evaluated every
time a shell is started, which can delay shell responsiveness. To speed
it up, write the generated script to a file, then source that. You can
generate the files ahead of time and distribute them with your program
to save your users a step.

.. tabs::

    .. group-tab:: Bash

        Save the script somewhere.

        .. code-block:: bash

            _FOO_BAR_COMPLETE=source_bash foo-bar > ~/.foo-bar-complete.bash

        Source the file in ``~/.bashrc``.

        .. code-block:: bash

            . ~/.foo-bar-complete.bash

    .. group-tab:: Zsh

        Save the script somewhere.

        .. code-block:: bash

            _FOO_BAR_COMPLETE=source_zsh foo-bar > ~/.foo-bar-complete.zsh

        Source the file in ``~/.zshrc``.

        .. code-block:: bash

            . ~/.foo-bar-complete.zsh

    .. group-tab:: Fish

        Save the script to ``~/.config/fish/completions/foo-bar.fish``:

        .. code-block:: fish

            _FOO_BAR_COMPLETE=source_fish foo-bar > ~/.config/fish/completions/foo-bar.fish

After modifying the shell config, you need to start a new shell in order
for the changes to be loaded.


Custom Type Completion
----------------------

When creating a custom :class:`~click.ParamType`, override its
:meth:`~click.ParamType.shell_complete` method to provide shell
completion for parameters with the type. The method must return a list
of :class:`~CompletionItem` objects. Besides the value, these objects
hold metadata that shell support might use. The built-in implementations
use ``type`` to indicate special handling for paths, and ``help`` for
shells that support showing a help string next to a suggestion.

In this example, the type will suggest environment variables that start
with the incomplete value.

.. code-block:: python

    class EnvVarType(ParamType):
        def shell_complete(self, ctx, param, incomplete):
            return [
                CompletionItem(name)
                for name in os.environ if name.startswith(incomplete)
            ]

    @click.command()
    @click.option("--ev", type=EnvVarType())
    def cli(ev):
        click.echo(os.environ[ev])


Overriding Value Completion
---------------------------

Value completions for a parameter can be customized without a custom
type by providing a ``shell_complete`` function. The function is used
instead of any completion provided by the type. It is passed 3 keyword
arguments:

-   ``ctx`` - The current command context.
-   ``param`` - The current parameter requesting completion.
-   ``incomplete`` - The partial word that is being completed. May
    be an empty string if no characters have been entered yet.

It must return a list of :class:`CompletionItem` objects, or as a
shortcut it can return a list of strings.

In this example, the command will suggest environment variables that
start with the incomplete value.

.. code-block:: python

    def complete_env_vars(ctx, param, incomplete):
        return [k for k in os.environ if k.startswith(incomplete)]

    @click.command()
    @click.argument("name", shell_complete=complete_env_vars)
    def cli(name):
        click.echo(f"Name: {name}")
        click.echo(f"Value: {os.environ[name]}")


Adding Support for a Shell
--------------------------

Support can be added for shells that do not come built in. Be sure to
check PyPI to see if there's already a package that adds support for
your shell. This topic is very technical, you'll want to look at Click's
source to study the built-in implementations.

Shell support is provided by subclasses of :class:`ShellComplete`
registered with :func:`add_completion_class`. When Click is invoked in
completion mode, it calls :meth:`~ShellComplete.source` to output the
completion script, or :meth:`~ShellComplete.complete` to output
completions. The base class provides default implementations that
require implementing some smaller parts.

First, you'll need to figure out how your shell's completion system
works and write a script to integrate it with Click. It must invoke your
program with the environment variable ``_{PROG_NAME}_COMPLETE`` set to
``complete_{shell}`` and pass the complete args and incomplete value.
How it passes those values, and the format of the completion response
from Click is up to you.

In your subclass, set :attr:`~ShellComplete.source_template` to the
completion script. The default implementation will perform ``%``
formatting with the following variables:

-   ``complete_func`` - A safe name for the completion function defined
    in the script.
-   ``complete_var`` - The environment variable name for passing the
    ``complete_{shell}`` value.
-   ``prog_name`` - The name of the executable being completed.

The example code is for a made up shell "My Shell" or "mysh" for short.

.. code-block:: python

    from click.shell_completion import add_completion_class
    from click.shell_completion import ShellComplete

    _mysh_source = """\
    %(complete_func)s {
        response=$(%(complete_var)s=complete_mysh %(prog_name)s)
        # parse response and set completions somehow
    }
    call-on-complete %(prog_name)s %(complete_func)s
    """

    @add_completion_class
    class MyshComplete(ShellComplete):
        name = "mysh"
        source_template = _mysh_source

Next, implement :meth:`~ShellComplete.get_completion_args`. This must
get, parse, and return the complete args and incomplete value from the
completion script. For example, for the Bash implementation the
``COMP_WORDS`` env var contains the command line args as a string, and
the ``COMP_CWORD`` env var contains the index of the incomplete arg. The
method must return a ``(args, incomplete)`` tuple.

.. code-block:: python

    import os
    from click.parser import split_arg_string

    class MyshComplete(ShellComplete):
        ...

        def get_completion_args(self):
            args = split_arg_string(os.environ["COMP_WORDS"])

            if os.environ["COMP_PARTIAL"] == "1":
                incomplete = args.pop()
                return args, incomplete

            return args, ""

Finally, implement :meth:`~ShellComplete.format_completion`. This is
called to format each ``(type, value, help)`` tuples returned by Click
into a string. For example, the Bash implementation returns
``f"{type},{value}`` (it doesn't support help strings), and the Zsh
implementation returns each part separated by a newline, replacing empty
help with a ``_`` placeholder. This format is entirely up to what you
parse with your completion script.

The ``type`` value is usually ``plain``, but it can be another value
that the completion script can switch on. For example, ``file`` or
``dir`` can tell the shell to handle path completion, since the shell is
better at that than Click.

.. code-block:: python

    import os
    from click.parser import split_arg_string

    class MyshComplete(ShellComplete):
        ...

        def format_completion(self, item):
            type, value, _ = item
            return f"{type}\t{value}"

With those three things implemented, the new shell support is ready. In
case those weren't sufficient, there are more parts that can be
overridden, but that probably isn't necessary.

The activation instructions will again depend on how your shell works.
Use the following to generate the completion script, then load it into
the shell somehow.

.. code-block:: text

    _FOO_BAR_COMPLETE=source_mysh foo-bar

Shell Completion
================

.. versionadded:: 2.0

Click can provide tab completion for commands, options, and choice
values. Bash, Zsh, and Fish are supported

Completion is only available if a script is installed and invoked
through an entry point, not through the ``python`` command. See
:ref:`setuptools-integration`.


What it Completes
-----------------

Generally, the shell completion support will complete commands,
options, and any option or argument values where the type is
:class:`click.Choice`. Options are only listed if at least a dash has
been entered.

.. code-block:: text

    $ repo <TAB><TAB>
    clone    commit   copy     delete   setuser
    $ repo clone -<TAB><TAB>
    --deep     --help     --rev      --shallow  -r

Custom completions can be provided for argument and option values by
providing an ``autocompletion`` function that returns a list of strings.
This is useful when the suggestions need to be dynamically generated
completion time. The callback function will be passed 3 keyword
arguments:

-   ``ctx`` - The current command context.
-   ``args`` - The list of arguments passed in.
-   ``incomplete`` - The partial word that is being completed. May
    be an empty string if no characters have been entered yet.

Here is an example of using a callback function to generate dynamic
suggestions:

.. code-block:: python

    import os

    def get_env_vars(ctx, args, incomplete):
        return [k for k in os.environ.keys() if incomplete in k]

    @click.command()
    @click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
    def cmd1(envvar):
        click.echo(f"Environment variable: {envvar}")
        click.echo(f"Value: {os.environ[envvar]}")


Completion help strings
-----------------------

ZSH and fish support showing documentation strings for completions.
These are taken from the help parameters of options and subcommands. For
dynamically generated completions a help string can be provided by
returning a tuple instead of a string. The first element of the tuple is
the completion and the second is the help string to display.

Here is an example of using a callback function to generate dynamic
suggestions with help strings:

.. code-block:: python

    import os

    def get_colors(ctx, args, incomplete):
        colors = [('red', 'a warm color'),
                  ('blue', 'a cool color'),
                  ('green', 'the other starter color')]
        return [c for c in colors if incomplete in c[0]]

    @click.command()
    @click.argument("color", type=click.STRING, autocompletion=get_colors)
    def cmd1(color):
        click.echo(f"Chosen color is {color}")


Activation
----------

In order to activate shell completion, you need to inform your shell
that completion is available for your script. Any Click application
automatically provides support for that. If the program is executed with
a special ``_<PROG_NAME>_COMPLETE`` variable, the completion mechanism
is triggered instead of the normal command. ``<PROG_NAME>`` is the
executable name in uppercase with dashes replaced by underscores.

If your tool is called ``foo-bar``, then the variable is called
``_FOO_BAR_COMPLETE``. By exporting it with the ``source_{shell}``
value it will output the activation script to evaluate.

Here are examples for a ``foo-bar`` script.

For Bash, add this to ``~/.bashrc``:

.. code-block:: text

    eval "$(_FOO_BAR_COMPLETE=source_bash foo-bar)"

For Zsh, add this to ``~/.zshrc``:

.. code-block:: text

    eval "$(_FOO_BAR_COMPLETE=source_zsh foo-bar)"

For Fish, add this to ``~/.config/fish/completions/foo-bar.fish``:

.. code-block:: text

    eval (env _FOO_BAR_COMPLETE=source_fish foo-bar)

Open a new shell to enable completion. Or run the ``eval`` command
directly in your current shell to enable it temporarily.


Activation Script
-----------------

The above ``eval`` examples will invoke your application every time a
shell is started. This may slow down shell startup time significantly.

Alternatively, export the generated completion code as a static script
to be executed. You can ship this file with your builds; tools like Git
do this. At least Zsh will also cache the results of completion files,
but not ``eval`` scripts.

For Bash:

.. code-block:: text

    _FOO_BAR_COMPLETE=source_bash foo-bar > foo-bar-complete.sh

For Zsh:

.. code-block:: text

    _FOO_BAR_COMPLETE=source_zsh foo-bar > foo-bar-complete.sh

For Fish:

.. code-block:: text

    _FOO_BAR_COMPLETE=source_fish foo-bar > foo-bar-complete.fish

In ``.bashrc`` or ``.zshrc``, source the script instead of the ``eval``
command:

.. code-block:: text

    . /path/to/foo-bar-complete.sh

For Fish, add the file to the completions directory:

.. code-block:: text

    _FOO_BAR_COMPLETE=source_fish foo-bar > ~/.config/fish/completions/foo-bar-complete.fish

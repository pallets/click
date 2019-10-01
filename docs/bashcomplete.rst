Bash Complete
=============

.. versionadded:: 2.0

As of Click 2.0, there is built-in support for Bash completion for
any Click script.  There are certain restrictions on when this completion
is available, but for the most part it should just work.

Limitations
-----------

Bash completion is only available if a script has been installed properly,
and not executed through the ``python`` command.  For information about
how to do that, see :ref:`setuptools-integration`.  Click currently
only supports completion for Bash and Zsh.

What it Completes
-----------------

Generally, the Bash completion support will complete subcommands, options
and any option or argument values where the type is click.Choice.
Subcommands and choices are always listed whereas options only if at
least a dash has been provided.  Example::

    $ repo <TAB><TAB>
    clone    commit   copy     delete   setuser
    $ repo clone -<TAB><TAB>
    --deep     --help     --rev      --shallow  -r

Additionally, custom suggestions can be provided for arguments and options with
the ``autocompletion`` parameter.  ``autocompletion`` should be a callback function
that returns a list of strings. This is useful when the suggestions need to be
dynamically generated at bash completion time. The callback function will be
passed 3 keyword arguments:

- ``ctx`` - The current click context.
- ``args`` - The list of arguments passed in.
- ``incomplete`` - The partial word that is being completed, as a string.  May
  be an empty string ``''`` if no characters have been entered yet.

The returned strings should have spaces appended to them in the case that
they cannot be further completed, omitting the space allows the completion
to be invoked multiple times, which can be useful for completing path-like
strings by searching a database or filesystem.

Here is an example of using a callback function to generate dynamic suggestions:

.. click:example::

    import os

    def get_env_vars(ctx, args, incomplete):
        return [k + ' ' for k in os.environ.keys() if incomplete in k]

    @click.command()
    @click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
    def cmd1(envvar):
        click.echo('Environment variable: %s' % envvar)
        click.echo('Value: %s' % os.environ[envvar])


Completion help strings (ZSH only)
----------------------------------

ZSH supports showing documentation strings for completions. These are taken
from the help parameters of options and subcommands. For dynamically generated
completions a help string can be provided by returning a tuple instead of a
string. The first element of the tuple is the completion and the second is the
help string to display.

Here is an example of using a callback function to generate dynamic suggestions with help strings:

.. click:example::

    import os

    def get_colors(ctx, args, incomplete):
        colors = [('red', 'help string for the color red'),
                  ('blue', 'help string for the color blue'),
                  ('green', 'help string for the color green')]
        return [c for c in colors if incomplete in c[0]]

    @click.command()
    @click.argument("color", type=click.STRING, autocompletion=get_colors)
    def cmd1(color):
        click.echo('Chosen color is %s' % color)


Activation
----------

In order to activate Bash completion, you need to inform Bash that
completion is available for your script, and how.  Any Click application
automatically provides support for that.  The general way this works is
through a magic environment variable called ``_<PROG_NAME>_COMPLETE``,
where ``<PROG_NAME>`` is your application executable name in uppercase
with dashes replaced by underscores.

If your tool is called ``foo-bar``, then the magic variable is called
``_FOO_BAR_COMPLETE``.  By exporting it with the ``source`` value it will
spit out the activation script which can be trivially activated.

For instance, to enable Bash completion for your ``foo-bar`` script, this
is what you would need to put into your ``.bashrc``::

    eval "$(_FOO_BAR_COMPLETE=source foo-bar)"

For zsh users add this to your ``.zshrc``::

    eval "$(_FOO_BAR_COMPLETE=source_zsh foo-bar)"

From this point onwards, your script will have autocompletion enabled.

Activation Script
-----------------

The above activation example will always invoke your application on
startup.  This might be slowing down the shell activation time
significantly if you have many applications.  Alternatively, you could also
ship a file with the contents of that, which is what Git and other systems
are doing.

This can be easily accomplished::

    _FOO_BAR_COMPLETE=source foo-bar > foo-bar-complete.sh

For zsh:

    _FOO_BAR_COMPLETE=source_zsh foo-bar > foo-bar-complete.sh

And then you would put this into your .bashrc or .zshrc instead::

    . /path/to/foo-bar-complete.sh

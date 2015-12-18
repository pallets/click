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
how to do that, see :ref:`setuptools-integration`.  Also, Click currently
only supports completion for Bash.

Currently, Bash completion is an internal feature that is not customizable.
This might be relaxed in future versions.

What it Completes
-----------------

By default, the Bash completion support will complete subcommands and
parameters.  Subcommands are always listed whereas parameters only if at
least a dash has been provided.  Example::

    $ repo <TAB><TAB>
    clone    commit   copy     delete   setuser
    $ repo clone -<TAB><TAB>
    --deep     --help     --rev      --shallow  -r
	
Additionally, custom suggestions can be provided for arguments with the
``autocompletion`` parameter.  ``autocompletion`` may be a list of strings, as
in the following example:

.. click:example::

    @click.command()
    @click.argument("name", type=click.STRING, autocompletion=["John", "Simon", "Doe"])
    def cmd1(name):
        click.echo('Name: %s' % name)
    
Alternatively, ``autocompletion`` may be a callback function that returns a list
of strings. This is useful when the suggestions need to be dynamically generated
at bash completion time. The callback function will be passed 4 keyword
arguments:

- ``ctx`` - The current click context.
- ``incomplete`` - The partial word that is being completed, as a string.  May
  be an empty string ``''`` if no characters have been entered yet.
- ``cwords`` - The bash `COMP_WORDS <https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion.html#Programmable-Completion>`_ array, as a list of strings.
- ``cword`` - The bash `COMP_CWORD <https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion.html#Programmable-Completion>`_ variable, as an integer.

Here is an example of using a callback function to generate dynamic suggestions:

.. click:example::

    import os
   
    def get_env_vars(ctx, incomplete, cwords, cword):
        return os.environ.keys()

    @click.command()
    @click.argument("envvar", type=click.STRING, autocompletion=get_env_vars)
    def cmd1(envvar):
        click.echo('Environment variable: %s' % envvar)
        click.echo('Value: %s' % os.environ[envvar])
  

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
spit out the activation script which can be trivally activated.

For instance, to enable Bash completion for your ``foo-bar`` script, this
is what you would need to put into your ``.bashrc``::

    eval "$(_FOO_BAR_COMPLETE=source foo-bar)"

From this point onwards, your script will have Bash completion enabled.

Activation Script
-----------------

The above activation example will always invoke your application on
startup.  This might be slowing down the shell activation time
significantly if you have many applications.  Alternatively, you could also
ship a file with the contents of that, which is what Git and other systems
are doing.

This can be easily accomplished::

    _FOO_BAR_COMPLETE=source foo-bar > foo-bar-complete.sh

And then you would put this into your bashrc instead::

    . /path/to/foo-bar-complete.sh

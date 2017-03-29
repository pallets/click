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
only supports completion for Bash. Zsh support is available through Zsh's
bash completion compatibility mode.

Currently, Bash completion is an internal feature that is not customizable.
This might be relaxed in future versions.

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

Zsh Compatibility
----------------

To enable Bash completion in Zsh, add the following lines to your .zshrc:

    autoload bashcompinit
    bashcompinit

See https://github.com/pallets/click/issues/323 for more information on
this issue.

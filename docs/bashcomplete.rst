Bash Complete
=============

.. versionadded:: 2.0

As of click 2.0, there is built-in support for Bash completion for
any click script.  There are certain restrictions on when this completion
is available, but for the most part it should just work.

Limitations
-----------

Bash completion is only available if a script has been installed properly,
and not executed through the ``python`` command.  For information about
how to do that, see :ref:`setuptools-integration`.  Also, click currently
only supports completion for Bash.

Currently, Bash completion is an internal feature that is not customizable.
This might be relaxed in future versions.

What it Completes
-----------------

Generally, the Bash completion support will complete subcommands and
parameters.  Subcommands are always listed whereas parameters only if at
least a dash has been provided.  Example::

    $ repo <TAB><TAB>
    clone    commit   copy     delete   setuser
    $ repo clone -<TAB><TAB>
    --deep     --help     --rev      --shallow  -r

Activation
----------

In order to activate Bash completion, you need to inform Bash that
completion is available for your script, and how.  Any click application
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

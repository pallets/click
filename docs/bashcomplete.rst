Bash Complete
=============

.. versionadded:: 2.0

Starting with click 2.0 there is built-in support for bash completion for
any Click script.  There are certain restrictions on when this completion
is available but for the most part it should just work.

Limitations
-----------

Bash completion is only available if a script has been installed properly
and not executed through the ``python`` command.  For information about
how to do that see :ref:`setuptools-integration`.  Currently click also
only supports completion for bash.

Currently bash completion is an internal feature that is not customizable.
This might be relaxed in future versions.

What it Completes
-----------------

Generally the bash completion support will complete subcommands and
parameters.  Subcommands are always listed whereas parameters only if at
least a dash has been provided.  Example::

    $ repo <TAB><TAB>
    clone    commit   copy     delete   setuser  
    $ repo clone -<TAB><TAB>
    --deep     --help     --rev      --shallow  -r         

Activation
----------

In order to activate bash completion you need to inform bash that
completion is available for your script and how.  Any click application
automatically provides support for that.  The general way this works is
through a magic environment variable called ``_<PROG_NAME>_COMPLETE``
where ``<PROG_NAME>`` is your application executable name in uppercase
with dashes replaced by underscores.

So if your tool is called ``foo-bar`` then the magic variable is called
``_FOO_BAR_COMPLETE``.  By exporting it with the ``source`` value it will
spit out the activation script which can be trivally be activated.

For instance to enable bash completion for your ``foo-bar`` script, this
is what you would need to put into your ``.bashrc``::

    eval "$(_FOO_BAR_COMPLETE=source foo-bar)"

From this point onwards your script will have bash completion enabled.

Activation Script
-----------------

The above activation example will always invoke your application on
startup.  This might be slowing down the shell activation time
significantly if you have many applications.  Alternatively you could also
ship a file with the contents of that which is what git and other systems
are doing.

This can be easily accomplished::

    _FOO_BAR_COMPLETE=source foo-bar > foo-bar-complete.sh

And then you would put this into your bashrc instead::

    . /path/to/foo-bar-complete.sh

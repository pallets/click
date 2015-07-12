plugins
=======

A sample package that loads CLI plugins from another package.


Contents
--------

* ``printer`` - The core package.
* ``PrinterStyle`` - An external plugin for ``printer``'s CLI that adds colors.
* ``BrokenPlugin`` - An broken external plugin that is supposed to add bold styling.


Workflow
--------

First get into the example directory:

.. code-block:: console

    $ cd examples/plugins

Install the main package:

.. code-block:: console

    $ pip install .

And run the commandline utility to see the usage:

.. code-block:: console

    $ printer
    Usage: printer [OPTIONS] COMMAND [ARGS]...

      Format and print file contents.

      For example:

          $ cat README.rst | printer lower

    Options:
      --help  Show this message and exit.

    Commands:
      lower  Convert to lower case.
      upper  Convert to uppser case.


Try running ``cat README.rst | printer upper`` to convert this file to upper-case.

The ``PrinterStyle`` directory is an external CLI plugin that is compatible with
``printer``.  In this case ``PrinterStyle`` adds styling options to the ``printer``
utility.

Install it:

.. code-block:: console

    $ pip install PrinterStyle/

And get the ``printer`` usage again, now with two additional commands:

.. code-block:: console

    $ printer
    Usage: printer [OPTIONS] COMMAND [ARGS]...

      Format and print file contents.

      For example:

          $ cat README.rst | printer lower

    Options:
      --help  Show this message and exit.

    Commands:
      background  Add a background color.
      bold        Make text bold.
      color       Add color to text.
      lower       Convert to lower case.
      upper       Convert to upper case.


Broken Plugins
--------------

Plugins that trigger an exception on load are flagged in the usage and the full
traceback can be viewed by executing the command.

Install the included broken plugin, which should give us a bold styling option:

.. code-block:: console

    $ pip install BrokenPlugin/

And look at the ``printer`` usage again - notice the icon next to ``bold``:

.. code-block:: console

    $ printer
    Usage: printer [OPTIONS] COMMAND [ARGS]...

      Format and print file contents.

      For example:

          $ cat README.rst | printer lower

    Options:
      --help  Show this message and exit.

    Commands:
      background  Add a background color.
      bold        † Warning: could not load plugin. See `printer bold --help`.
      color       Add color to text.
      lower       Convert to lower case.
      upper       Convert to upper case.

Executing ``printer bold`` reveals the full traceback:

.. code-block:: console

    $ printer bold

    Warning: entry point could not be loaded. Contact its author for help.

    Traceback (most recent call last):
      File "/Users/wursterk/github/click/venv/lib/python3.4/site-packages/pkg_resources/__init__.py", line 2353, in resolve
        return functools.reduce(getattr, self.attrs, module)
    AttributeError: 'module' object has no attribute 'bolddddddddddd'

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "/Users/wursterk/github/click/click/decorators.py", line 145, in decorator
        obj.add_command(entry_point.load())
      File "/Users/wursterk/github/click/venv/lib/python3.4/site-packages/pkg_resources/__init__.py", line 2345, in load
        return self.resolve()
      File "/Users/wursterk/github/click/venv/lib/python3.4/site-packages/pkg_resources/__init__.py", line 2355, in resolve
        raise ImportError(str(exc))
    ImportError: 'module' object has no attribute 'bolddddddddddd'

In this case the error is in the broken plugin's ``setup.py``.

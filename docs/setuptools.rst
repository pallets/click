.. _setuptools-integration:

Setuptools Integration
======================
When writing command line utilities, it's recommended to write them as modules that are distributed with setuptools for cross-platform compatibility.  

#. On windows, setuptools automatically generates executable wrappers for Windows. This is especially useful since Unix shebangs don't work. Unix shebangs are comments at the beginning of the file that give the path to the executable, eg ``#!/usr/bin/env/python``. If the file is set as an executable, then the os will use the shebang to find the executable and run it. On windows you are not able to link a file to a specific Python interpreter so you have to ensure the script in run with the right interpreter. 

#. On linux and osx, setuptools scripts work with virtualenv without the virtualenv having to be activated. This makes it easy to bundle your dependencies as virtualenvs.

In addition, setuptools solves some problem unrelated to platform. 

#.  Under certain conditions, you script can be imported and run twice. For example, your script is imported as ``__main__``, which Python does for the first module it imports, and then another piece of code calls your code. You module has been imported as ``__main__``, so it is imported again with its actual name and run again. 

#.  You can avoid the above issue by protecting the script with: 

    .. code-block::

        if __name__ = '__main__':

    But this trick will run into issues if you start using it as a package.

How to Package a Script
---------------------------------

To bundle your script with setuptools, all you need is the script in a
Python package and a ``setup.py`` file.

Imagine this directory structure:

.. code-block:: text

    yourscript.py
    setup.py

Contents of ``yourscript.py``:

.. click:example::

    import click

    @click.command()
    def cli():
        """Example script."""
        click.echo('Hello World!')

Contents of ``setup.py``:

.. code-block:: python

    from setuptools import setup

    setup(
        name='yourscript',
        version='0.1.0',
        py_modules=['yourscript'],
        install_requires=[
            'Click',
        ],
        entry_points={
            'console_scripts': [
                'yourscript = yourscript:cli',
            ],
        },
    )

The magic is in the ``entry_points`` parameter.  Below
``console_scripts``, each line identifies one console script.  The first
part before the equals sign (``=``) is the name of the script that should
be generated, the second part is the import path followed by a colon
(``:``) with the Click command.

That's it.

Running a Script
------------------

To test the script, you can make a new virtualenv and then install your
package:

.. code-block:: console

    $ python3 -m venv .venv
    $ . .venv/bin/activate
    $ pip install --editable .

Afterwards, your command should be available:

.. click:run::

    invoke(cli, prog_name='yourscript')

How to package a package
--------------------------

If your script is growing and you want to switch over to your script being
contained in a Python package the changes necessary are minimal.  Let's
assume your directory structure changed to this:

.. code-block:: text

    project/
        yourpackage/
            __init__.py
            main.py
            utils.py
            scripts/
                __init__.py
                yourscript.py
        setup.py

In this case instead of using ``py_modules`` in your ``setup.py`` file you
can use ``packages`` and the automatic package finding support of
setuptools.  In addition to that it's also recommended to include other
package data.

These would be the modified contents of ``setup.py``:

.. code-block:: python

    from setuptools import setup, find_packages

    setup(
        name='yourpackage',
        version='0.1.0',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            'Click',
        ],
        entry_points={
            'console_scripts': [
                'yourscript = yourpackage.scripts.yourscript:cli',
            ],
        },
    )

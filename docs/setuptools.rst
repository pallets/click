.. _setuptools-integration:

Usage with Setuptools
=====================

When writing command line utilities, it's recommended to write them as
modules that are distributed with setuptools instead of using UNIX
shebangs.  There are many reasons for this.

The first one is that setuptools automatically generates executable
wrappers for Windows so your command line utilities work on Windows too.

The second reason is that setuptools scripts work with virtualenv on UNIX
without the virtualenv having to be activated.  This is a very useful
concept which allows you to bundle your scripts with all requirements into
a virtualenv.

Introduction
------------

To bundle your script with setuptools, all you need is the script in a Python
package and a ``setup.py`` file.

Imagine this directory structure::

    yourpackage/
        cli.py
    setup.py

Contents of ``cli.py``:

.. click:example::

    import click

    @click.command()
    def cli():
        """Example script."""
        click.echo('Hello World!')

Contents of ``setup.py``::

    from setuptools import setup, find_packages

    setup(
        name='yourpackage',
        version='0.1',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            'Click',
        ],
        entry_points='''
            [console_scripts]
            yourscript=yourpackage.cli:cli
        ''',
    )

The magic is in the ``entry_points`` parameter.  Below ``console_scripts``,
each line identifies one console script.  The first part before the equals
sign (``=``) is the name of the script that should be generated, the second
part is the import path followed by a colon (``:``) with the click
command.

That's it.

Testing The Script
------------------

To test the script you can make a new virtualenv and then install your
package::

    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install --editable .

Afterwards your command should be available:

.. click:run::

    invoke(cli, prog_name='yourscript', prog_prefix='')

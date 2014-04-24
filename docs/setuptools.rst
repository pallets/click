Usage with Setuptools
=====================

When writing command line utilities it's recommended to write them as
modules that are distributed with setuptools instead of using UNIX
shebangs.  There are a bunch of reasons for this.

The first one is that setuptools automatically generates executable
wrappers for Windows so your command line utilies work on Windows too.

The second reason is that setuptools scripts work with virtualenv on UNIX
without the virtualenv having to be activated.  This is a very useful
concept which allows you to bundle your scripts with all requirements into
a virtualenv.

Introduction
------------

All you need to do to bundle your scripts with setuptools is your script
in a python package and a ``setup.py`` file.

Imagine this layout::

    yourpackage/
        cli.py
    setup.py

Contents of ``cli.py``::

    import click

    @click.command()
    def cli():
        """Example script."""
        print('Hello World!')

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

The magic is in the ``entry_points`` parameter.  Below ``console_scripts``
each line identifies one console script.  The first part before the equals
sign (``=``) is the name of the script that should be generate, the second
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

Afterwards your command should be available::

    $ yourscript
    Hello World!

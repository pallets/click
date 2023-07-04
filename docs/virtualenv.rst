.. _virtualenv-heading:

Virtualenv
========================= 

Why use virtualenv?
------------------------- 

You should use `Virtualenv <https://virtualenv.pypa.io/en/latest/>`_ because: 

*   It allows you to install multiple versions of the same dependency.

*   If you have an operating system version of python, it prevents you from changing its dependencies and potentially messing up your os.

How to use virtualenv 
-----------------------------

Create your project folder, then a virtualenv within it::

    $ mkdir myproject
    $ cd myproject
    $ python3 -m venv .venv

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . .venv/bin/activate
    (venv) $

On Windows, do the following::

    > .venv\scripts\activate
    (venv) >

You are now using your virtualenv (notice how the prompt of your shell has changed to show the active environment).

To install in the virtual environment::

    $ pip install click

And if you want to stop using the virtualenv, use the following command::

    $ deactivate

After doing this, the prompt of your shell should be as familiar as before.
 






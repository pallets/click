==========================
How to contribute to Click
==========================

Thanks for considering contributing to Click.

Support questions
=================

Please, don't use the issue tracker for this. Check whether the `Pocoo IRC
channel <http://www.pocoo.org/irc/>`_ can help with your issue. If your problem
is not strictly Click-specific, ``#python`` on Freenode is generally more
active.  `StackOverflow <https://stackoverflow.com/>`_ is also worth
considering.

Reporting issues
================

- Under which versions of Python does this happen? This is even more important
  if your issue is encoding related.

- Under which versions of Click does this happen? Check if this issue is fixed
  in the repository.

Submitting patches
==================

- Include tests if your patch is supposed to solve a bug, and explain clearly
  under which circumstances the bug happens. Make sure the test fails without
  your patch.

- Try to follow `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_, but you
  may ignore the line-length-limit if following it would make the code uglier.

- For features: Consider whether your feature would be a better fit for an
  `external package <click.pocoo.org/contrib/>`_

Running the testsuite
---------------------

You probably want to set up a `virtualenv
<http://virtualenv.readthedocs.org/en/latest/index.html>`_.

The minimal requirement for running the testsuite is ``py.test``.  You can
install it with::

    pip install pytest

Then you can run the testsuite with::

    py.test

For a more isolated test environment, you can also install ``tox`` instead of
``pytest``. You can install it with::

    pip install tox

The ``tox`` command will then run all tests against multiple combinations of
Python versions and dependency versions.

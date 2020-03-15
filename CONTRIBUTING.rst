==========================
How to contribute to Click
==========================

Thanks for considering contributing to Click.

Support questions
=================

Please, don't use the issue tracker for this. Check whether the
``#pocoo`` IRC channel on Freenode can help with your issue. If your problem
is not strictly Click-specific, ``#python`` on Freenode is generally more
active.  Also try searching or asking on `Stack Overflow`_ with the
``python-click`` tag.

.. _Stack Overflow: https://stackoverflow.com/questions/tagged/python-click?sort=votes

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
  `external package <https://click.palletsprojects.com/en/7.x/contrib/>`_

- For docs and bug fixes: Submit against the latest maintenance branch instead of master!

- Non docs or text related changes need an entry in ``CHANGES.rst``,
  and ``.. versionadded`` or ``.. versionchanged`` markers in the docs.

Running the testsuite
---------------------

You probably want to set up a `virtualenv
<https://virtualenv.readthedocs.io/en/latest/index.html>`_.

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

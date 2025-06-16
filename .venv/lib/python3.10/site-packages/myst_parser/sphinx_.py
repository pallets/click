"""A module for compatibility with the docutils>=0.17 `include` directive, in RST documents.

For example::

   .. include::  path/to/file.md
      :parser: myst_parser.sphinx_
"""

from myst_parser.parsers.sphinx_ import MystParser as Parser  # noqa: F401

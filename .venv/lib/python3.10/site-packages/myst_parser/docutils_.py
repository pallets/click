"""A module for compatibility with the docutils>=0.17 `include` directive, in RST documents:

For example::

   .. include:: path/to/file.md
      :parser: myst_parser.docutils_
"""

from myst_parser.parsers.docutils_ import Parser  # noqa: F401

"""An extended [CommonMark](https://spec.commonmark.org/) compliant parser,
with bridges to [docutils](https://docutils.sourceforge.io/)
and [Sphinx](https://github.com/sphinx-doc/sphinx).
"""

__version__ = "4.0.1"


def setup(app):
    """Initialize the [Sphinx](https://github.com/sphinx-doc/sphinx) extension."""
    from myst_parser.sphinx_ext.main import setup_sphinx

    setup_sphinx(app, load_parser=True)
    return {"version": __version__, "parallel_read_safe": True}

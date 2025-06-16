"""The setup for the sphinx extension."""

from typing import Any

import sphinx
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.transforms import (
    UnreferencedFootnotesDetector as SphinxUnreferencedFootnotesDetector,
)

from myst_parser.mdit_to_docutils.transforms import UnreferencedFootnotesDetector
from myst_parser.parsers.docutils_ import (
    depart_container_html,
    depart_rubric_html,
    visit_container_html,
    visit_rubric_html,
)
from myst_parser.warnings_ import MystWarnings


def setup_sphinx(app: Sphinx, load_parser: bool = False) -> None:
    """Initialize all settings and transforms in Sphinx.

    :param app: The Sphinx application object.
    :param load_parser: Whether to load the parser.
    """
    # we do this separately to setup,
    # so that it can be called by external packages like myst_nb
    from myst_parser.config.main import MdParserConfig
    from myst_parser.parsers.sphinx_ import MystParser
    from myst_parser.sphinx_ext.directives import (
        FigureMarkdown,
        SubstitutionReferenceRole,
    )
    from myst_parser.sphinx_ext.mathjax import override_mathjax
    from myst_parser.sphinx_ext.myst_refs import MystReferenceResolver

    if load_parser:
        app.add_source_suffix(".md", "markdown")
        app.add_source_parser(MystParser)

    app.add_role("sub-ref", SubstitutionReferenceRole())
    app.add_directive("figure-md", FigureMarkdown)

    # TODO currently we globally replace sphinx's transform,
    # to overcome issues it has (https://github.com/sphinx-doc/sphinx/pull/12730),
    # but once this PR is merged/released, we should remove this
    app.registry.transforms.remove(SphinxUnreferencedFootnotesDetector)
    app.add_transform(UnreferencedFootnotesDetector)

    app.add_post_transform(MystReferenceResolver)

    # override only the html writer visit methods for rubric, to use the "level" attribute
    # this allows for nested headers to be correctly rendered
    if sphinx.version_info < (7, 4):
        # This is now added in sphinx: https://github.com/sphinx-doc/sphinx/pull/12506
        app.add_node(
            nodes.rubric, override=True, html=(visit_rubric_html, depart_rubric_html)
        )
    # override only the html writer visit methods for container,
    # to remove the "container" class for divs
    # this avoids CSS clashes with the bootstrap theme
    app.add_node(
        nodes.container,
        override=True,
        html=(visit_container_html, depart_container_html),
    )

    for name, default, field in MdParserConfig().as_triple():
        if "sphinx" not in field.metadata.get("omit", []):
            # TODO add types?
            app.add_config_value(f"myst_{name}", default, "env", types=Any)  # type: ignore[arg-type]

    app.connect("builder-inited", create_myst_config)
    app.connect("builder-inited", override_mathjax)


def create_myst_config(app):
    """Create the myst config object and add it to the sphinx environment."""
    from sphinx.util import logging
    from sphinx.util.console import bold

    from myst_parser import __version__
    from myst_parser.config.main import MdParserConfig

    logger = logging.getLogger(__name__)

    values = {
        name: app.config[f"myst_{name}"]
        for name, _, field in MdParserConfig().as_triple()
        if "sphinx" not in field.metadata.get("omit", [])
    }

    try:
        app.env.myst_config = MdParserConfig(**values)
        logger.info(bold("myst v%s:") + " %s", __version__, app.env.myst_config)
    except (TypeError, ValueError) as error:
        logger.error("myst configuration invalid: %s", error.args[0])
        app.env.myst_config = MdParserConfig()

    if "attrs_image" in app.env.myst_config.enable_extensions:
        logger.warning(
            "The `attrs_image` extension is deprecated, "
            "please use `attrs_inline` instead.",
            type="myst",
            subtype=MystWarnings.DEPRECATED.value,
        )

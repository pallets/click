"""Convert Markdown-it tokens to docutils nodes, including sphinx specific elements."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast
from uuid import uuid4

from docutils import nodes
from markdown_it.tree import SyntaxTreeNode
from sphinx import addnodes
from sphinx.domains.math import MathDomain
from sphinx.environment import BuildEnvironment
from sphinx.ext.intersphinx import InventoryAdapter
from sphinx.util import logging

from myst_parser import inventory
from myst_parser.mdit_to_docutils.base import DocutilsRenderer, token_line
from myst_parser.warnings_ import MystWarnings

LOGGER = logging.getLogger(__name__)


class SphinxRenderer(DocutilsRenderer):
    """A markdown-it-py renderer to populate (in-place) a `docutils.document` AST.

    This is sub-class of `DocutilsRenderer` that handles sphinx specific aspects,
    such as cross-referencing.
    """

    @property
    def sphinx_env(self) -> BuildEnvironment:
        return self.document.settings.env

    def _process_wrap_node(
        self,
        wrap_node: nodes.Element,
        token: SyntaxTreeNode,
        explicit: bool,
        classes: list[str],
        path_dest: str,
    ):
        """Process a wrap node, which is a node that wraps a link."""
        self.add_line_and_source_path(wrap_node, token)
        self.copy_attributes(token, wrap_node, ("class", "id", "title"))
        self.current_node.append(wrap_node)

        if explicit:
            inner_node = nodes.inline("", "", classes=classes)
            with self.current_node_context(inner_node):
                self.render_children(token)
        elif isinstance(wrap_node, addnodes.download_reference):
            inner_node = nodes.literal(path_dest, path_dest, classes=classes)
        else:
            inner_node = nodes.inline("", "", classes=classes)

        wrap_node.append(inner_node)

    def _handle_relative_docs(self, destination: str) -> str:
        """Make the path relative to an "including" document

        This is set when using the `relative-docs` option of the MyST `include` directive
        """
        relative_include = self.md_env.get("relative-docs", None)
        if relative_include is not None and destination.startswith(relative_include[0]):
            source_dir, include_dir = relative_include[1:]
            destination = os.path.relpath(
                os.path.join(include_dir, os.path.normpath(destination)), source_dir
            )
        return destination

    def render_link_project(self, token: SyntaxTreeNode) -> None:
        destination = cast(str, token.attrGet("href") or "")
        if destination.startswith("project:"):
            destination = destination[8:]
        if destination.startswith("#"):
            return self.render_link_anchor(token, destination)

        if not self.sphinx_env.srcdir:  # not set in some test situations
            return self.render_link_url(token)

        destination = self.md.normalizeLinkText(destination)
        destination = self._handle_relative_docs(destination)
        path_dest, *_path_ids = destination.split("#", maxsplit=1)
        path_id = _path_ids[0] if _path_ids else None
        explicit = (token.info != "auto") and (len(token.children or []) > 0)
        _, abs_path = self.sphinx_env.relfn2path(path_dest, self.sphinx_env.docname)
        docname = self.sphinx_env.path2doc(abs_path)
        if not docname:
            self.create_warning(
                f"Could not find document: {abs_path}",
                MystWarnings.XREF_MISSING,
                line=token_line(token, 0),
                append_to=self.current_node,
            )
            return self.render_link_url(token)
        wrap_node = addnodes.pending_xref(
            refdomain="doc",
            reftarget=docname,
            reftargetid=path_id,
            refdoc=self.sphinx_env.docname,
            reftype="myst",
            refexplicit=explicit,
        )
        classes = ["xref", "myst"]
        self._process_wrap_node(wrap_node, token, explicit, classes, destination)

    def render_link_path(self, token: SyntaxTreeNode) -> None:
        destination = self.md.normalizeLinkText(cast(str, token.attrGet("href") or ""))
        if destination.startswith("path:"):
            destination = destination[5:]
        destination = self._handle_relative_docs(destination)
        explicit = (token.info != "auto") and (len(token.children or []) > 0)
        wrap_node = addnodes.download_reference(
            refdomain=None,
            reftarget=destination,
            refdoc=self.sphinx_env.docname,
            reftype="myst",
            refexplicit=explicit,
        )
        classes = ["xref", "download", "myst"]
        self._process_wrap_node(wrap_node, token, explicit, classes, destination)

    def render_link_unknown(self, token: SyntaxTreeNode) -> None:
        """Render link token `[text](link "title")`,
        where the link has not been identified as an external URL.
        """
        destination = self.md.normalizeLinkText(cast(str, token.attrGet("href") or ""))
        destination = self._handle_relative_docs(destination)

        explicit = (token.info != "auto") and (len(token.children or []) > 0)
        kwargs = {
            "refdoc": self.sphinx_env.docname,
            "reftype": "myst",
            "refexplicit": explicit,
        }
        path_dest, *_path_ids = destination.split("#", maxsplit=1)
        path_id = _path_ids[0] if _path_ids else None

        potential_path: None | Path = None
        if self.sphinx_env.srcdir:  # not set in some test situations
            _, path_str = self.sphinx_env.relfn2path(path_dest, self.sphinx_env.docname)
            potential_path = Path(path_str)

        if potential_path and potential_path.is_file():
            docname = self.sphinx_env.path2doc(str(potential_path))
            if docname:
                wrap_node = addnodes.pending_xref(
                    refdomain="doc", reftarget=docname, reftargetid=path_id, **kwargs
                )
                classes = ["xref", "myst"]
            else:
                wrap_node = addnodes.download_reference(
                    refdomain=None, reftarget=path_dest, **kwargs
                )
                classes = ["xref", "download", "myst"]
        else:
            wrap_node = addnodes.pending_xref(
                refdomain=None, reftarget=destination, **kwargs
            )
            classes = ["xref", "myst"]

        self._process_wrap_node(wrap_node, token, explicit, classes, path_dest)

    def get_inventory_matches(
        self,
        *,
        invs: str | None,
        domains: str | None,
        otypes: str | None,
        target: str | None,
    ) -> list[inventory.InvMatch]:
        return list(
            inventory.filter_sphinx_inventories(
                InventoryAdapter(self.sphinx_env).named_inventory,
                invs=invs,
                domains=domains,
                otypes=otypes,
                targets=target,
            )
        )

    def render_math_block_label(self, token: SyntaxTreeNode) -> None:
        """Render math with referenceable labels, e.g. ``$a=1$ (label)``."""
        label = token.info
        content = token.content
        node = nodes.math_block(
            content, content, nowrap=False, number=None, label=label
        )
        target = self.add_math_target(node)
        self.add_line_and_source_path(target, token)
        self.current_node.append(target)
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def _random_label(self) -> str:
        return str(uuid4())

    def render_amsmath(self, token: SyntaxTreeNode) -> None:
        """Renderer for the amsmath extension."""
        # environment = token.meta["environment"]
        content = token.content

        if token.meta["numbered"] != "*":
            # TODO how to parse and reference labels within environment?
            # for now we give create a unique hash, so the equation will be numbered
            # but there will be no reference clashes
            label = self._random_label()
            node = nodes.math_block(
                content,
                content,
                nowrap=True,
                number=None,
                classes=["amsmath"],
                label=label,
            )
            target = self.add_math_target(node)
            self.add_line_and_source_path(target, token)
            self.current_node.append(target)
        else:
            node = nodes.math_block(
                content, content, nowrap=True, number=None, classes=["amsmath"]
            )
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def add_math_target(self, node: nodes.math_block) -> nodes.target:
        # Code mainly copied from sphinx.directives.patches.MathDirective

        # register label to domain
        domain = cast(MathDomain, self.sphinx_env.get_domain("math"))
        domain.note_equation(self.sphinx_env.docname, node["label"], location=node)
        node["number"] = domain.get_equation_number_for(node["label"])
        node["docname"] = self.sphinx_env.docname

        # create target node
        node_id = nodes.make_id("equation-{}".format(node["label"]))
        target = nodes.target("", "", ids=[node_id])
        self.document.note_explicit_target(target)
        return target

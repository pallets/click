"""Directives that can be applied to both Sphinx and docutils."""

from __future__ import annotations

import typing as t

from docutils import nodes
from docutils.transforms import Transform
from docutils.transforms.references import Footnotes
from markdown_it.common.normalize_url import normalizeLink

from myst_parser._compat import findall
from myst_parser.mdit_to_docutils.base import clean_astext
from myst_parser.warnings_ import MystWarnings, create_warning


class UnreferencedFootnotesDetector(Transform):
    """Detect unreferenced footnotes and emit warnings.

    Replicates https://github.com/sphinx-doc/sphinx/pull/12730,
    but also allows for use in docutils (without sphinx).
    """

    default_priority = Footnotes.default_priority + 2

    # document: nodes.document

    def apply(self, **kwargs: t.Any) -> None:
        """Apply the transform."""

        for node in self.document.footnotes:
            # note we do not warn on duplicate footnotes here
            # (i.e. where the name has been moved to dupnames)
            # since this is already reported by docutils
            if not node["backrefs"] and node["names"]:
                create_warning(
                    self.document,
                    "Footnote [{}] is not referenced.".format(node["names"][0])
                    if node["names"]
                    else node["dupnames"][0],
                    wtype="ref",
                    subtype="footnote",
                    node=node,
                )
        for node in self.document.symbol_footnotes:
            if not node["backrefs"]:
                create_warning(
                    self.document,
                    "Footnote [*] is not referenced.",
                    wtype="ref",
                    subtype="footnote",
                    node=node,
                )
        for node in self.document.autofootnotes:
            # note we do not warn on duplicate footnotes here
            # (i.e. where the name has been moved to dupnames)
            # since this is already reported by docutils
            if not node["backrefs"] and node["names"]:
                create_warning(
                    self.document,
                    "Footnote [#] is not referenced.",
                    wtype="ref",
                    subtype="footnote",
                    node=node,
                )


class SortFootnotes(Transform):
    """Sort auto-numbered, labelled footnotes by the order they are referenced.

    This is run before the docutils ``Footnote`` transform, where numbered labels are assigned.
    """

    default_priority = Footnotes.default_priority - 2

    # document: nodes.document

    def apply(self, **kwargs: t.Any) -> None:
        """Apply the transform."""
        if not self.document.settings.myst_footnote_sort:
            return

        ref_order: list[str] = [
            node["refname"]
            for node in self.document.autofootnote_refs
            if "refname" in node
        ]

        def _sort_key(node: nodes.footnote) -> int:
            if node["names"] and node["names"][0] in ref_order:
                return ref_order.index(node["names"][0])
            return 999

        self.document.autofootnotes.sort(key=_sort_key)


class CollectFootnotes(Transform):
    """Transform to move footnotes to the end of the document, and sort by label."""

    default_priority = Footnotes.default_priority + 3

    # document: nodes.document

    def apply(self, **kwargs: t.Any) -> None:
        """Apply the transform."""
        if not self.document.settings.myst_footnote_sort:
            return

        footnotes: list[tuple[str, nodes.footnote]] = []
        for footnote in (
            self.document.symbol_footnotes
            + self.document.footnotes
            + self.document.autofootnotes
        ):
            label = footnote.children[0]
            footnotes.append((label.astext(), footnote))

        if (
            footnotes
            and self.document.settings.myst_footnote_transition
            # avoid warning: Document or section may not begin with a transition
            and not all(isinstance(c, nodes.footnote) for c in self.document.children)
        ):
            transition = nodes.transition(classes=["footnotes"])
            transition.source = self.document.source
            self.document += transition

        def _sort_key(footnote: tuple[str, nodes.footnote]) -> int | str:
            label, _ = footnote
            try:
                # ensure e.g 10 comes after 2
                return int(label)
            except ValueError:
                return label

        for _, footnote in sorted(footnotes, key=_sort_key):
            footnote.parent.remove(footnote)
            self.document += footnote


class ResolveAnchorIds(Transform):
    """Transform for resolving `[name](#id)` type links."""

    default_priority = 879  # this is the same as Sphinx's StandardDomain.process_doc

    def apply(self, **kwargs: t.Any) -> None:
        """Apply the transform."""
        # gather the implicit heading slugs
        # name -> (line, slug, title)
        slugs: dict[str, tuple[int, str, str]] = getattr(
            self.document, "myst_slugs", {}
        )

        # gather explicit references
        # this follows the same logic as Sphinx's StandardDomain.process_doc
        explicit: dict[str, tuple[str, None | str]] = {}
        for name, is_explicit in self.document.nametypes.items():
            if not is_explicit:
                continue
            labelid = self.document.nameids[name]
            if labelid is None:
                continue
            if labelid is None:
                continue
            node = self.document.ids[labelid]
            if isinstance(node, nodes.target) and "refid" in node:
                # indirect hyperlink targets
                node = self.document.ids.get(node["refid"])
                labelid = node["names"][0]
            if (
                node.tagname == "footnote"
                or "refuri" in node
                or node.tagname.startswith("desc_")
            ):
                # ignore footnote labels, labels automatically generated from a
                # link and object descriptions
                continue

            implicit_title = None
            if node.tagname == "rubric":
                implicit_title = clean_astext(node)
            if implicit_title is None:
                # handle sections and and other captioned elements
                for subnode in node:
                    if isinstance(subnode, nodes.caption | nodes.title):
                        implicit_title = clean_astext(subnode)
                        break
            if implicit_title is None:
                # handle definition lists and field lists
                if (
                    isinstance(node, nodes.definition_list | nodes.field_list)
                    and node.children
                ):
                    node = node[0]
                if (
                    isinstance(node, nodes.field | nodes.definition_list_item)
                    and node.children
                ):
                    node = node[0]
                if isinstance(node, nodes.term | nodes.field_name):
                    implicit_title = clean_astext(node)

            explicit[name] = (labelid, implicit_title)

        for refnode in findall(self.document)(nodes.reference):
            if not refnode.get("id_link"):
                continue

            target = refnode["refuri"][1:]
            del refnode["refuri"]

            # search explicit first
            if target in explicit:
                ref_id, implicit_title = explicit[target]
                refnode["refid"] = ref_id
                if not refnode.children and implicit_title:
                    refnode += nodes.inline(
                        implicit_title, implicit_title, classes=["std", "std-ref"]
                    )
                elif not refnode.children:
                    refnode += nodes.inline(
                        "#" + target, "#" + target, classes=["std", "std-ref"]
                    )
                continue

            # now search implicit
            if target in slugs:
                _, sect_id, implicit_title = slugs[target]
                refnode["refid"] = sect_id
                if not refnode.children and implicit_title:
                    refnode += nodes.inline(
                        implicit_title, implicit_title, classes=["std", "std-ref"]
                    )
                continue

            # if still not found, and using sphinx, then create a pending_xref
            if hasattr(self.document.settings, "env"):
                from sphinx import addnodes

                pending = addnodes.pending_xref(
                    refdoc=self.document.settings.env.docname,
                    refdomain=None,
                    reftype="myst",
                    reftarget=target,
                    refexplicit=bool(refnode.children),
                )
                inner_node = nodes.inline(
                    "", "", classes=["xref", "myst"] + refnode["classes"]
                )
                for attr in ("ids", "names", "dupnames"):
                    inner_node[attr] = refnode[attr]
                inner_node += refnode.children
                pending += inner_node
                refnode.parent.replace(refnode, pending)
                continue

            # if still not found, and using docutils, then create a warning
            # and simply output as a url

            create_warning(
                self.document,
                f"'myst' reference target not found: {target!r}",
                MystWarnings.XREF_MISSING,
                line=refnode.line,
                append_to=refnode,
            )
            refnode["refid"] = normalizeLink(target)
            if not refnode.children:
                refnode += nodes.inline(
                    "#" + target, "#" + target, classes=["std", "std-ref"]
                )

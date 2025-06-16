"""A post-transform for overriding the behaviour of sphinx reference resolution.

This is applied to MyST type references only, such as ``[text](target)``,
and allows for nested syntax
"""

from __future__ import annotations

import re
from typing import Any, cast

from docutils import nodes
from docutils.nodes import Element, document
from markdown_it.common.normalize_url import normalizeLink
from sphinx import addnodes
from sphinx.addnodes import pending_xref
from sphinx.domains.std import StandardDomain
from sphinx.errors import NoUri
from sphinx.ext.intersphinx import InventoryAdapter
from sphinx.transforms.post_transforms import ReferencesResolver
from sphinx.util import docname_join, logging
from sphinx.util.nodes import clean_astext, make_refnode

from myst_parser import inventory
from myst_parser._compat import findall
from myst_parser.warnings_ import MystWarnings

LOGGER = logging.getLogger(__name__)


class MystReferenceResolver(ReferencesResolver):
    """Resolves cross-references on doctrees.

    Overrides default sphinx implementation, to allow for nested syntax
    """

    default_priority = 9  # higher priority than ReferencesResolver (10)

    def log_warning(
        self, target: None | str, msg: str, subtype: MystWarnings, **kwargs: Any
    ):
        """Log a warning, with a myst type and specific subtype."""

        # MyST references are warned about by default (the same as the `any` role)
        # However, warnings can also be ignored by adding ("myst", target)
        # nitpick_ignore/nitpick_ignore_regex lists
        # https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpicky
        if (
            target
            and self.config.nitpick_ignore
            and ("myst", target) in self.config.nitpick_ignore
        ):
            return
        if (
            target
            and self.config.nitpick_ignore_regex
            and any(
                (
                    re.fullmatch(ignore_type, "myst")
                    and re.fullmatch(ignore_target, target)
                )
                for ignore_type, ignore_target in self.config.nitpick_ignore_regex
            )
        ):
            return

        LOGGER.warning(msg, type="myst", subtype=subtype.value, **kwargs)

    def run(self, **kwargs: Any) -> None:
        self.document: document
        for node in findall(self.document)(addnodes.pending_xref):
            if node["reftype"] != "myst":
                continue

            if node["refdomain"] == "doc":
                self.resolve_myst_ref_doc(node)
                continue

            newnode = None
            contnode = cast(nodes.TextElement, node[0].deepcopy())
            target = node["reftarget"]
            refdoc = node.get("refdoc", self.env.docname)
            search_domains: None | list[str] = self.env.config.myst_ref_domains

            # try to resolve the reference within the local project,
            # this asks all domains to resolve the reference,
            # return None if no domain could resolve the reference
            # or returns the first result, and logs a warning if
            # multiple domains resolved the reference
            try:
                newnode = self.resolve_myst_ref_any(
                    refdoc, node, contnode, search_domains
                )
            except NoUri:
                newnode = contnode
            if newnode is None:
                # If no local domain could resolve the reference, try to
                # resolve it as an inter-sphinx reference
                newnode = self._resolve_myst_ref_intersphinx(
                    node, contnode, target, search_domains
                )
            if newnode is None:
                # if still not resolved, log a warning,
                self.log_warning(
                    target,
                    f"'myst' cross-reference target not found: {target!r}",
                    MystWarnings.XREF_MISSING,
                    location=node,
                )

            # if the target could not be found, then default to using an external link
            if not newnode:
                newnode = nodes.reference()
                newnode["refid"] = normalizeLink(target)
                newnode.append(node[0].deepcopy())

            # ensure the output node has some content
            if (
                len(newnode.children) == 1
                and isinstance(newnode[0], nodes.inline)
                and not (newnode[0].children)
            ):
                newnode[0].replace_self(nodes.literal(target, target))
            elif not newnode.children:
                newnode.append(nodes.literal(target, target))

            node.replace_self(newnode)

    def resolve_myst_ref_doc(self, node: pending_xref):
        """Resolve a reference, from a markdown link, to another document,
        optionally with a target id within that document.
        """
        from_docname = node.get("refdoc", self.env.docname)
        ref_docname: str = node["reftarget"]
        ref_id: str | None = node["reftargetid"]

        if ref_docname not in self.env.all_docs:
            self.log_warning(
                ref_docname,
                f"Unknown source document {ref_docname!r}",
                MystWarnings.XREF_MISSING,
                location=node,
            )
            node.replace_self(node[0].deepcopy())
            return

        targetid = ""
        implicit_text = ""
        inner_classes = ["std", "std-doc"]

        if ref_id:
            slug_to_section = self.env.metadata[ref_docname].get("myst_slugs", {})
            if ref_id not in slug_to_section:
                self.log_warning(
                    ref_id,
                    f"local id not found in doc {ref_docname!r}: {ref_id!r}",
                    MystWarnings.XREF_MISSING,
                    location=node,
                )
                targetid = ref_id
            else:
                _, targetid, implicit_text = slug_to_section[ref_id]
            inner_classes = ["std", "std-ref"]
        else:
            implicit_text = clean_astext(self.env.titles[ref_docname])

        if node["refexplicit"]:
            caption = node.astext()
            innernode = nodes.inline(caption, "", classes=inner_classes)
            innernode.extend(node[0].children)
        else:
            innernode = nodes.inline(
                implicit_text, implicit_text, classes=inner_classes
            )

        assert self.app.builder
        try:
            ref_node = make_refnode(
                self.app.builder, from_docname, ref_docname, targetid, innernode
            )
        except NoUri:
            ref_node = innernode
        node.replace_self(ref_node)

    def resolve_myst_ref_any(
        self,
        refdoc: str,
        node: pending_xref,
        contnode: Element,
        only_domains: None | list[str],
    ) -> Element | None:
        """Resolve reference generated by the "myst" role; ``[text](#reference)``.

        This builds on the sphinx ``any`` role to also resolve:

        - Document references with extensions; ``[text](./doc.md)``
        - Document references with anchors with anchors; ``[text](./doc.md#target)``
        - Nested syntax for explicit text with std:doc and std:ref;
          ``[**nested**](reference)``

        """
        target: str = node["reftarget"]
        results: list[tuple[str, Element]] = []

        # resolve standard references
        res = self._resolve_ref_nested(node, refdoc)
        if res:
            results.append(("std:ref", res))

        # resolve doc names
        res = self._resolve_doc_nested(node, refdoc)
        if res:
            results.append(("std:doc", res))

        assert self.app.builder

        # next resolve for any other standard reference objects
        if only_domains is None or "std" in only_domains:
            stddomain = cast(StandardDomain, self.env.get_domain("std"))
            for objtype in stddomain.object_types:
                key = (objtype, target)
                if objtype == "term":
                    key = (objtype, target.lower())
                if key in stddomain.objects:
                    docname, labelid = stddomain.objects[key]
                    domain_role = "std:" + (stddomain.role_for_objtype(objtype) or "")
                    ref_node = make_refnode(
                        self.app.builder, refdoc, docname, labelid, contnode
                    )
                    results.append((domain_role, ref_node))

        # finally resolve for any other type of allowed reference domain
        for domain in self.env.domains.values():
            if domain.name == "std":
                continue  # we did this one already
            if only_domains is not None and domain.name not in only_domains:
                continue
            try:
                results.extend(
                    domain.resolve_any_xref(
                        self.env, refdoc, self.app.builder, target, node, contnode
                    )
                )
            except NotImplementedError:
                # the domain doesn't yet support the new interface
                # we have to manually collect possible references (SLOW)
                if not (getattr(domain, "__module__", "").startswith("sphinx.")):
                    self.log_warning(
                        None,
                        f"Domain '{domain.__module__}::{domain.name}' has not "
                        "implemented a `resolve_any_xref` method",
                        MystWarnings.LEGACY_DOMAIN,
                        once=True,
                    )
                for role in domain.roles:
                    res = domain.resolve_xref(
                        self.env, refdoc, self.app.builder, role, target, node, contnode
                    )
                    if res and len(res) and isinstance(res[0], nodes.Element):
                        results.append((f"{domain.name}:{role}", res))

        # now, see how many matches we got...
        if not results:
            return None
        if len(results) > 1:

            def stringify(name, node):
                reftitle = node.get("reftitle", node.astext())
                return f":{name}:`{reftitle}`"

            candidates = " or ".join(stringify(name, role) for name, role in results)
            self.log_warning(
                target,
                f"more than one target found for 'myst' cross-reference {target}: "
                f"could be {candidates}",
                MystWarnings.XREF_AMBIGUOUS,
                location=node,
            )

        res_role, newnode = results[0]
        # Override "myst" class with the actual role type to get the styling
        # approximately correct.
        res_domain = res_role.split(":")[0]
        if len(newnode) > 0 and isinstance(newnode[0], nodes.Element):
            newnode[0]["classes"] = newnode[0].get("classes", []) + [
                res_domain,
                res_role.replace(":", "-"),
            ]

        return newnode

    def _resolve_ref_nested(
        self, node: pending_xref, fromdocname: str, target=None
    ) -> Element | None:
        """This is the same as ``sphinx.domains.std._resolve_ref_xref``,
        but allows for nested syntax, rather than converting the inner node to raw text.
        """
        stddomain = cast(StandardDomain, self.env.get_domain("std"))
        target = target or node["reftarget"].lower()

        if node["refexplicit"]:
            # reference to anonymous label; the reference uses
            # the supplied link caption
            docname, labelid = stddomain.anonlabels.get(target, ("", ""))
            sectname = node.astext()
            innernode = nodes.inline(sectname, "")
            innernode.extend(node[0].children)
        else:
            # reference to named label; the final node will
            # contain the section name after the label
            docname, labelid, sectname = stddomain.labels.get(target, ("", "", ""))
            innernode = nodes.inline(sectname, sectname)

        if not docname:
            return None

        assert self.app.builder
        return make_refnode(self.app.builder, fromdocname, docname, labelid, innernode)

    def _resolve_doc_nested(
        self, node: pending_xref, fromdocname: str
    ) -> Element | None:
        """This is the same as ``sphinx.domains.std._resolve_doc_xref``,
        but allows for nested syntax, rather than converting the inner node to raw text.

        It also allows for extensions on document names.
        """
        docname = docname_join(node.get("refdoc", fromdocname), node["reftarget"])
        if docname not in self.env.all_docs:
            return None

        if node["refexplicit"]:
            # reference with explicit title
            caption = node.astext()
            innernode = nodes.inline(caption, "", classes=["doc"])
            innernode.extend(node[0].children)
        else:
            caption = clean_astext(self.env.titles[docname])
            innernode = nodes.inline(caption, caption, classes=["doc"])

        assert self.app.builder
        return make_refnode(self.app.builder, fromdocname, docname, "", innernode)

    def _resolve_myst_ref_intersphinx(
        self,
        node: nodes.Element,
        contnode: nodes.Element,
        target: str,
        only_domains: list[str] | None,
    ) -> None | nodes.reference:
        """Resolve a myst reference to an intersphinx inventory."""
        matches = [
            m
            for m in inventory.filter_sphinx_inventories(
                InventoryAdapter(self.env).named_inventory,
                targets=target,
            )
            if only_domains is None or m.domain in only_domains
        ]
        if not matches:
            return None
        if len(matches) > 1:
            # log a warning if there are multiple matches
            show_num = 3
            matches_str = ", ".join(
                [
                    inventory.filter_string(m.inv, m.domain, m.otype, m.name)
                    for m in matches[:show_num]
                ]
            )
            if len(matches) > show_num:
                matches_str += ", ..."
            self.log_warning(
                target,
                f"Multiple matches found for {target!r}: {matches_str}",
                MystWarnings.IREF_AMBIGUOUS,
                location=node,
            )
        # get the first match and create a reference node
        match = matches[0]
        newnode = nodes.reference("", "", internal=False, refuri=match.loc)
        if "reftitle" in node:
            newnode["reftitle"] = node["reftitle"]
        else:
            newnode["reftitle"] = f"{match.project} {match.version}".strip()
        if node.get("refexplicit"):
            newnode.append(contnode)
        elif match.text:
            newnode.append(
                contnode.__class__(match.text, match.text, classes=["iref", "myst"])
            )
        else:
            newnode.append(
                nodes.literal(match.name, match.name, classes=["iref", "myst"])
            )

        return newnode

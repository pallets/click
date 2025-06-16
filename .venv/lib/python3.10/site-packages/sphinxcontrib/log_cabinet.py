from itertools import groupby

from docutils import nodes
from packaging.version import parse as parse_version
from sphinx.addnodes import versionmodified
from sphinx.util import logging

__version__ = "1.0.1"
logger = logging.getLogger(__name__)


def setup(app):
    app.add_config_value("log_cabinet_collapse_all", False, "html")
    app.connect("doctree-resolved", handle_doctree_resolved)
    app.add_node(
        CollapsedLog,
        html=(html_visit_CollapsedLog, html_depart_CollapsedLog),
        latex=(visit_nop, visit_nop),
        text=(visit_nop, visit_nop),
        man=(visit_nop, visit_nop),
        texinfo=(visit_nop, visit_nop),
    )
    app.add_config_value("changelog_collapse_all", None, "")
    app.connect("config-inited", check_deprecated_config)
    return {"version": __version__}


def check_deprecated_config(app, config):
    if config.changelog_collapse_all is not None:
        logger.warning(
            "The 'changelog_collapse_all' config has been renamed to"
            " 'log_cabinet_collapse_all'. The old name will be removed"
            " in version 1.1.0."
        )


def _parse_placeholder_version(value, placeholder="x"):
    """Strip version suffix (1.1.x to 1.1) before parsing version.

    :param value: Version string to parse.
    :param placeholder: Suffix to strip from the version string.
    """
    if value.endswith(".{}".format(placeholder)):
        value = value[: -(len(placeholder) + 1)]

    return parse_version(value)


def handle_doctree_resolved(app, doctree, docname):
    visitor = ChangelogVisitor(doctree, app)
    doctree.walk(visitor)
    collapse_all = app.config.changelog_collapse_all
    version = _parse_placeholder_version(app.config.version)

    for after, log in visitor.logs:
        if after is None:
            # log was the first element of a page
            after = log[0]
            index = 0
        else:
            # log came after other nodes on the page
            index = after.parent.index(after) + 1

        del after.parent[index : index + len(log)]

        if not collapse_all:
            visible = []
            hidden = []

            for n in log:
                if parse_version(n["version"]) >= version or n["type"] == "deprecated":
                    visible.append(n)
                else:
                    hidden.append(n)

            if visible:
                after.parent.insert(index, visible)
                index += len(visible)
                log = hidden

        if log:
            collapsed = CollapsedLog()
            collapsed.extend(log)
            after.parent.insert(index, collapsed)


class ChangelogVisitor(nodes.GenericNodeVisitor):
    def __init__(self, document, app):
        nodes.GenericNodeVisitor.__init__(self, document)
        self.logs = []

    def default_visit(self, node):
        after = None

        for key, group in groupby(
            node.children, key=lambda n: isinstance(n, versionmodified)
        ):
            if not key:
                after = list(group)[-1]
                continue

            self.logs.append(
                (
                    after,
                    sorted(
                        group, key=lambda n: parse_version(n["version"]), reverse=True
                    ),
                )
            )

    def default_departure(self, node):
        pass

    unknown_visit = default_visit
    unknown_departure = default_departure


class CollapsedLog(nodes.General, nodes.Element):
    pass


def html_visit_CollapsedLog(self, node):
    self.body.append(self.starttag(node, "details", CLASS="changelog"))
    self.body.append("<summary>Changelog</summary>")


def html_depart_CollapsedLog(self, node):
    self.body.append("</details>")


def visit_nop(self, node):
    pass

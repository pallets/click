""" Tabbed views for Sphinx, with HTML builder """

import base64
from pathlib import Path
from functools import partial
import sphinx


from docutils import nodes
from docutils.parsers.rst import directives
from pygments.lexers import get_all_lexers
from sphinx.highlighting import lexer_classes
from sphinx.util.docutils import SphinxDirective
from sphinx.directives.code import CodeBlock


JS_FILES = [
    "tabs.js",
]

CSS_FILES = [
    "tabs.css",
]

LEXER_MAP = {}
for lexer in get_all_lexers():
    for short_name in lexer[1]:
        LEXER_MAP[short_name] = lexer[0]


def get_compatible_builders(app):
    builders = [
        "html",
        "singlehtml",
        "dirhtml",
        "readthedocs",
        "readthedocsdirhtml",
        "readthedocssinglehtml",
        "readthedocssinglehtmllocalmedia",
        "spelling",
    ]
    builders.extend(app.config["sphinx_tabs_valid_builders"])
    return builders


class SphinxTabsContainer(nodes.container):
    tagname = "div"


class SphinxTabsPanel(nodes.container):
    tagname = "div"


class SphinxTabsTab(nodes.paragraph):
    tagname = "button"


class SphinxTabsTablist(nodes.container):
    tagname = "div"


def visit(translator, node):
    # Borrowed from `sphinx-inline-tabs`
    attrs = node.attributes.copy()
    attrs.pop("classes")
    attrs.pop("ids")
    attrs.pop("names")
    attrs.pop("dupnames")
    attrs.pop("backrefs")
    text = translator.starttag(node, node.tagname, **attrs)
    translator.body.append(text.strip())


def depart(translator, node):
    translator.body.append(f"</{node.tagname}>")


class TabsDirective(SphinxDirective):
    """Top-level tabs directive"""

    has_content = True

    def run(self):
        """Parse a tabs directive"""
        self.assert_has_content()

        node = nodes.container(type="tab-element")
        node["classes"].append("sphinx-tabs")

        if "next_tabs_id" not in self.env.temp_data:
            self.env.temp_data["next_tabs_id"] = 0
        if "tabs_stack" not in self.env.temp_data:
            self.env.temp_data["tabs_stack"] = []

        tabs_id = self.env.temp_data["next_tabs_id"]
        tabs_key = f"tabs_{tabs_id}"
        self.env.temp_data["next_tabs_id"] += 1
        self.env.temp_data["tabs_stack"].append(tabs_id)

        self.env.temp_data[tabs_key] = {}
        self.env.temp_data[tabs_key]["tab_ids"] = []
        self.env.temp_data[tabs_key]["tab_titles"] = []
        self.env.temp_data[tabs_key]["is_first_tab"] = True

        self.state.nested_parse(self.content, self.content_offset, node)

        if self.env.app.builder.name in get_compatible_builders(self.env.app):
            tablist = SphinxTabsTablist()
            tablist["role"] = "tablist"
            tablist["aria-label"] = "Tabbed content"
            if not self.env.config["sphinx_tabs_disable_tab_closing"]:
                tablist["classes"].append("closeable")

            tab_titles = self.env.temp_data[tabs_key]["tab_titles"]
            for idx, [data_tab, tab_name] in enumerate(tab_titles):
                tab_name.attributes["role"] = "tab"
                tab_name["ids"] = [f"tab-{tabs_id}-{data_tab}"]
                tab_name["name"] = data_tab
                tab_name["tabindex"] = "0" if idx == 0 else "-1"
                tab_name["aria-selected"] = "true" if idx == 0 else "false"
                tab_name["aria-controls"] = tab_name["ids"][0].replace("tab-", "panel-")

                tablist += tab_name

            node.insert(0, tablist)

        self.env.temp_data["tabs_stack"].pop()
        return [node]


class TabDirective(SphinxDirective):
    """Tab directive, for adding a tab to a collection of tabs"""

    has_content = True

    def __init__(self, *args, **kwargs):
        self.tab_id = None
        self.tab_classes = set()
        super().__init__(*args, **kwargs)

    def run(self):
        """Parse a tab directive"""
        self.assert_has_content()

        tabs_id = self.env.temp_data["tabs_stack"][-1]
        tabs_key = f"tabs_{tabs_id}"

        include_tabs_id_in_data_tab = False
        if self.tab_id is None:
            tab_id = self.env.new_serialno(tabs_key)
            include_tabs_id_in_data_tab = True
        else:
            tab_id = self.tab_id

        tab_name = SphinxTabsTab()
        self.state.nested_parse(self.content[0:1], 0, tab_name)
        # Remove the paragraph node that is created by nested_parse
        tab_name.children[0].replace_self(tab_name.children[0].children)

        tab_name["classes"].append("sphinx-tabs-tab")
        tab_name["classes"].extend(sorted(self.tab_classes))

        i = 1
        while tab_id in self.env.temp_data[tabs_key]["tab_ids"]:
            tab_id = f"{tab_id}-{i}"
            i += 1
        self.env.temp_data[tabs_key]["tab_ids"].append(tab_id)

        data_tab = str(tab_id)
        if include_tabs_id_in_data_tab:
            data_tab = f"{tabs_id}-{data_tab}"

        self.env.temp_data[tabs_key]["tab_titles"].append((data_tab, tab_name))

        panel = SphinxTabsPanel()
        panel["role"] = "tabpanel"
        panel["ids"] = [f"panel-{tabs_id}-{data_tab}"]
        panel["name"] = data_tab
        panel["tabindex"] = 0
        panel["aria-labelledby"] = panel["ids"][0].replace("panel-", "tab-")
        panel["classes"].append("sphinx-tabs-panel")
        panel["classes"].extend(sorted(self.tab_classes))

        if self.env.temp_data[tabs_key]["is_first_tab"]:
            self.env.temp_data[tabs_key]["is_first_tab"] = False
        else:
            panel["hidden"] = "true"

        self.state.nested_parse(self.content[1:], self.content_offset, panel)

        if self.env.app.builder.name not in get_compatible_builders(self.env.app):
            # Use base docutils classes
            outer_node = nodes.container()
            tab = nodes.container()
            tab_name = nodes.container()
            panel = nodes.container()

            self.state.nested_parse(self.content[0:1], 0, tab_name)
            self.state.nested_parse(self.content[1:], self.content_offset, panel)

            tab += tab_name
            outer_node += tab
            outer_node += panel

            return [outer_node]

        return [panel]


class GroupTabDirective(TabDirective):
    """Tab directive that toggles with same tab names across page"""

    has_content = True

    def run(self):
        self.assert_has_content()
        self.tab_classes.add("group-tab")
        group_name = self.content[0]
        if self.tab_id is None:
            self.tab_id = base64.b64encode(group_name.encode("utf-8")).decode("utf-8")

        node = super().run()
        return node


class CodeTabDirective(GroupTabDirective):
    """Tab directive with a codeblock as its content"""

    has_content = True
    required_arguments = 1  # Lexer name
    optional_arguments = 1  # Custom label
    final_argument_whitespace = True
    option_spec = {  # From sphinx CodeBlock
        "force": directives.flag,
        "linenos": directives.flag,
        "dedent": int,
        "lineno-start": int,
        "emphasize-lines": directives.unchanged_required,
        "caption": directives.unchanged_required,
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self):
        """Parse a code-tab directive"""
        self.assert_has_content()

        if len(self.arguments) > 1:
            tab_name = self.arguments[1]
        elif self.arguments[0] in lexer_classes and not isinstance(
            lexer_classes[self.arguments[0]], partial
        ):
            tab_name = lexer_classes[self.arguments[0]].name
        else:
            try:
                tab_name = LEXER_MAP[self.arguments[0]]
            except KeyError as invalid_lexer_error:
                raise ValueError(
                    f"Lexer not implemented: {self.arguments[0]}"
                ) from invalid_lexer_error

        self.tab_classes.add("code-tab")

        # All content parsed as code
        code_block = CodeBlock.run(self)

        # Reset to generate panel
        self.content.data = [tab_name, ""]
        self.content.items = [(None, 0), (None, 1)]

        node = super().run()
        node[0].extend(code_block)

        return node


class _FindTabsDirectiveVisitor(nodes.NodeVisitor):
    """Visitor pattern than looks for a sphinx tabs
    directive in a document"""

    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self._found = False

    def unknown_visit(self, node):
        if (
            not self._found
            and isinstance(node, nodes.container)
            and "classes" in node
            and isinstance(node["classes"], list)
        ):
            self._found = "sphinx-tabs" in node["classes"]

    @property
    def found_tabs_directive(self):
        """Return whether a sphinx tabs directive was found"""
        return self._found


# pylint: disable=unused-argument
def update_context(app, pagename, templatename, context, doctree):
    """Remove sphinx-tabs CSS and JS asset files if not used in a page"""
    if doctree is None:
        return
    visitor = _FindTabsDirectiveVisitor(doctree)
    doctree.walk(visitor)

    include_assets_in_all_pages = False
    if sphinx.version_info >= (4, 1, 0):
        include_assets_in_all_pages = app.registry.html_assets_policy == "always"

    if visitor.found_tabs_directive or include_assets_in_all_pages:
        if not app.config.sphinx_tabs_disable_css_loading:
            for css in CSS_FILES:
                app.add_css_file(css)
        for js in JS_FILES:
            app.add_js_file(js)


# pylint: enable=unused-argument


def setup(app):
    """Set up the plugin"""
    app.add_config_value("sphinx_tabs_valid_builders", [], "")
    app.add_config_value("sphinx_tabs_disable_css_loading", False, "html", [bool])
    app.add_config_value("sphinx_tabs_disable_tab_closing", False, "html", [bool])
    app.add_node(SphinxTabsContainer, html=(visit, depart))
    app.add_node(SphinxTabsPanel, html=(visit, depart))
    app.add_node(SphinxTabsTab, html=(visit, depart))
    app.add_node(SphinxTabsTablist, html=(visit, depart))
    app.add_directive("tabs", TabsDirective)
    app.add_directive("tab", TabDirective)
    app.add_directive("group-tab", GroupTabDirective)
    app.add_directive("code-tab", CodeTabDirective)
    static_dir = Path(__file__).parent / "static"
    app.connect(
        "builder-inited",
        (lambda app: app.config.html_static_path.insert(0, static_dir.as_posix())),
    )
    app.connect("html-page-context", update_context)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

"""Code to use internally, for documentation."""

from __future__ import annotations

import contextlib
import io
from collections.abc import Sequence
from typing import Union, get_args, get_origin

from docutils import nodes
from docutils.core import Publisher
from docutils.parsers.rst import directives
from sphinx.directives import other
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from myst_parser.parsers.docutils_ import to_html5_demo

from .config.main import MdParserConfig
from .parsers.docutils_ import Parser as DocutilsParser
from .warnings_ import MystWarnings

LOGGER = logging.getLogger(__name__)


class StripUnsupportedLatex(SphinxPostTransform):
    """Remove unsupported nodes from the doctree."""

    default_priority = 900

    def run(self, **kwargs):
        if self.app.builder.format != "latex":
            return
        from docutils import nodes

        for node in self.document.findall():
            if node.tagname == "image" and node["uri"].endswith(".svg"):
                node.parent.replace(node, nodes.inline("", "Removed SVG image"))
            if node.tagname == "mermaid":
                node.parent.replace(node, nodes.inline("", "Removed Mermaid diagram"))


class NumberSections(SphinxPostTransform):
    """Number sections (html only)"""

    default_priority = 710  # same as docutils.SectNum
    formats = ("html",)

    def run(self, **kwargs):
        min_heading_level = 2
        max_heading_level = 3
        stack: list[tuple[list[int], nodes.Element]] = [([], self.document)]
        while stack:
            path, node = stack.pop()
            if len(path) >= min_heading_level:
                title = node[0]
                text = (
                    ".".join(str(i) for i in path[min_heading_level - 1 :])
                    + "."
                    + ("&nbsp;" * 2)
                )
                # docutils SectNum transform
                title.insert(0, nodes.raw("", text, format="html"))
                title["auto"] = 1
            if len(path) < max_heading_level:
                i = 0
                for child in node.children:
                    if isinstance(child, nodes.section):
                        i += 1
                        stack.append((path + [i], child))


class _ConfigBase(SphinxDirective):
    """Directive to automate rendering of the configuration."""

    @staticmethod
    def table_header():
        return [
            "```````{list-table}",
            ":header-rows: 1",
            ":widths: 15 10 20",
            "",
            "* - Name",
            "  - Type",
            "  - Description",
        ]

    @staticmethod
    def field_default(value):
        default = " ".join(f"{value!r}".splitlines())
        return default

    @staticmethod
    def field_type(field):
        ftypes: Sequence[str]
        ftypes = (
            get_args(field.type) if get_origin(field.type) is Union else [field.type]
        )
        ctype = " | ".join(str("None" if ftype is None else ftype) for ftype in ftypes)
        ctype = " ".join(ctype.splitlines())
        ctype = ctype.replace("typing.", "")
        ctype = ctype.replace("typing_extensions.", "")
        for tname in ("str", "int", "float", "bool"):
            ctype = ctype.replace(f"<class '{tname}'>", tname)
        return ctype


class MystConfigDirective(_ConfigBase):
    option_spec = {
        "sphinx": directives.flag,
        "extensions": directives.flag,
        "scope": lambda x: directives.choice(x, ["global", "local"]),
    }

    def run(self):
        """Run the directive."""
        config = MdParserConfig()
        text = self.table_header()
        count = 0
        for name, value, field in config.as_triple():
            if field.metadata.get("deprecated"):
                continue

            # filter by sphinx options
            if "sphinx" in self.options and "sphinx" in field.metadata.get("omit", []):
                continue

            if "extensions" in self.options:
                if not field.metadata.get("extension"):
                    continue
            else:
                if field.metadata.get("extension"):
                    continue

            if self.options.get("scope") == "local" and field.metadata.get(
                "global_only"
            ):
                continue

            if self.options.get("scope") == "global":
                name = f"myst_{name}"

            description = " ".join(field.metadata.get("help", "").splitlines())
            if field.metadata.get("extension"):
                description = f"{field.metadata.get('extension')}: {description}"
            default = self.field_default(value)
            ctype = field.metadata.get("doc_type") or self.field_type(field)
            text.extend(
                [
                    f"* - `{name}`",
                    f"  - `{ctype}`",
                    f"  - {description} (default: `{default}`)",
                ]
            )

            count += 1

        if not count:
            return []

        text.append("```````")
        node = nodes.Element()
        self.state.nested_parse(text, 0, node)
        return node.children


class DocutilsCliHelpDirective(SphinxDirective):
    """Directive to print the docutils CLI help."""

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        """Run the directive."""

        stream = io.StringIO()

        pub = Publisher(parser=DocutilsParser())
        with contextlib.redirect_stdout(stream):
            try:
                pub.process_command_line(
                    ["--help"],
                    usage="myst-docutils-<writer> [options] [<source> [<destination>]]",
                )
            except SystemExit as exc:
                assert not exc.code
        return [nodes.literal_block("", stream.getvalue())]


class DirectiveDoc(SphinxDirective):
    """Load and document a directive."""

    required_arguments = 1  # name of the directive
    has_content = True

    def run(self):
        """Run the directive."""
        name = self.arguments[0]
        # load the directive class
        klass, _ = directives.directive(
            name, self.state.memo.language, self.state.document
        )
        if klass is None:
            LOGGER.warning(f"Directive {name} not found.", line=self.lineno)
            return []
        content = " ".join(self.content)
        text = f"""\
:Name: `{name}`
:Description: {content}
:Arguments: {klass.required_arguments} required, {klass.optional_arguments} optional
:Content: {'yes' if klass.has_content else 'no'}
:Options:
"""
        if klass.option_spec:
            text += "  name | type\n  -----|------\n"
            for key, func in klass.option_spec.items():
                text += f"  {key} | {convert_opt(name, func)}\n"
        node = nodes.Element()
        self.state.nested_parse(text.splitlines(), 0, node)
        return node.children


def convert_opt(name, func):
    """Convert an option function to a string."""
    if func is directives.flag:
        return "flag"
    if func is directives.unchanged:
        return "text"
    if func is directives.unchanged_required:
        return "text"
    if func is directives.class_option:
        return "space-delimited list"
    if func is directives.uri:
        return "URI"
    if func is directives.path:
        return "path"
    if func is int:
        return "integer"
    if func is directives.positive_int:
        return "integer (positive)"
    if func is directives.nonnegative_int:
        return "integer (non-negative)"
    if func is directives.positive_int_list:
        return "space/comma-delimited list of integers (positive)"
    if func is directives.percentage:
        return "percentage"
    if func is directives.length_or_unitless:
        return "length or unitless"
    if func is directives.length_or_percentage_or_unitless:
        return "length, percentage or unitless"
    if func is other.int_or_nothing:
        return "integer"
    return ""


class MystWarningsDirective(SphinxDirective):
    """Directive to print all known warnings."""

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        """Run the directive."""
        from sphinx.pycode import ModuleAnalyzer

        analyzer = ModuleAnalyzer.for_module(MystWarnings.__module__)
        qname = MystWarnings.__qualname__
        analyzer.analyze()
        warning_names = [
            (e.value, analyzer.attr_docs[(qname, e.name)]) for e in MystWarnings
        ]
        text = [f"- `myst.{name}`: {' '.join(doc)}" for name, doc in warning_names]
        node = nodes.Element()
        self.state.nested_parse(text, 0, node)
        return node.children


class MystExampleDirective(SphinxDirective):
    """Directive to create an example, showing the source and output."""

    has_content = True
    option_spec = {
        "alt-output": directives.unchanged,
        "highlight": directives.unchanged,
        # "html": directives.flag,
    }

    def run(self):
        """Run the directive."""
        content_str = "\n".join(self.content)
        output_str = self.options.get("alt-output", content_str)
        highlight = self.options.get("highlight", "myst")
        backticks = "```"
        while backticks in content_str:
            backticks += "`"
        content = f"""
{backticks}``{{div}} myst-example

{backticks}`{{div}} myst-example-source
{backticks}{highlight}
{content_str}
{backticks}
{backticks}`
{backticks}`{{div}} myst-example-render

{output_str}
{backticks}`
{backticks}``
"""
        node_ = nodes.Element()
        self.state.nested_parse(content.splitlines(), self.content_offset, node_)
        return node_.children


class MystAdmonitionDirective(SphinxDirective):
    """Directive to show a set of admonitions, in a tab set."""

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        """Run the directive."""
        types = [t.strip() for t in self.arguments[0].split(",")]
        content = "::::{tab-set}"
        for type_ in types:
            content += f"""
:::{{tab-item}} {type_}
```{{{type_}}}
This is a {type_}
```
:::
"""
        content += "::::"
        node_ = nodes.Element()
        self.state.nested_parse(content.splitlines(), self.content_offset, node_)
        return node_.children


class MystToHTMLDirective(SphinxDirective):
    """Directive to convert MyST to HTML."""

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "extensions": directives.unchanged,
    }

    def run(self):
        """Run the directive."""
        content_str = "\n".join(self.content)
        kwargs = {}
        cli_opt = ""
        if "extensions" in self.options:
            ext = self.options["extensions"].split(",")
            kwargs["myst_enable_extensions"] = ext
            cli_opt += f"--myst-enable-extensions={self.options['extensions']}"
        html = to_html5_demo(content_str, **kwargs)
        content = f"""\
::::myst-example
```bash
myst-docutils-demo example.md {cli_opt}
```
```myst
{content_str}
```
```html
{html}
```
::::
"""
        node_ = nodes.Element()
        self.state.nested_parse(content.splitlines(), self.content_offset, node_)
        return node_.children


### MyST Lexer ###
# TODO when some more work and testing, this should be made available publicly

from pygments import token  # noqa: E402
from pygments.lexer import bygroups, inherit, this, using  # noqa: E402
from pygments.lexers.markup import MarkdownLexer  # noqa: E402


class MystLexer(MarkdownLexer):
    """A custom lexer for MyST Markdown."""

    name = "MyST"
    aliases = ["myst"]
    filenames = ["*.myst"]
    mimetypes = ["text/x-myst"]

    tokens = {
        "root": [
            # (target)=
            (
                r"^(\()([^\n]+)(\)=)(\n)",
                bygroups(
                    token.Punctuation, token.Name.Label, token.Punctuation, token.Text
                ),
            ),
            # :::
            (r"^([\:]{3,})(\n)", bygroups(token.Punctuation, token.Text)),
            # :::name other
            # TODO this seems to "eat" the next line
            # (r"^([\:]{3,})([^\s\n]+)(\s+)([^\n]+)(\n)",
            # bygroups(token.Punctuation, token.Name.Tag, token.Whitespace, token.Text,token.Text)),
            # :::name
            (
                r"^([\:]{3,})([^\n]+)(\n)",
                bygroups(token.Punctuation, token.Name.Tag, token.Text),
            ),
            # :name: value
            (
                r"^(\:)([^\n\:]+)(\:)([^\n]+)(\n)",
                bygroups(
                    token.Punctuation,
                    token.Generic.Strong,
                    token.Punctuation,
                    using(this, state="inline"),
                    token.Text,
                ),
            ),
            inherit,
        ],
        "inline": [
            # escape (we have to copy this from the parent class)
            (r"\\.", token.Text),
            # {name}
            (
                r"(\{)([a-zA-Z0-9+:-]+)(\})",
                bygroups(token.Punctuation, token.Operator.Word, token.Punctuation),
            ),
            # <http:example.com>
            (
                r"(<)(http|https|mailto|project|path|inv)(\:)([^\s>]+)(>)",
                bygroups(
                    token.Punctuation,
                    token.String.Other,
                    token.String.Other,
                    token.Name.Label,
                    token.Punctuation,
                ),
            ),
            inherit,
        ],
    }

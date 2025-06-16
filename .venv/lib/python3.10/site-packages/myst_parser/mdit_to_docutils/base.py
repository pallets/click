"""Convert Markdown-it tokens to docutils nodes."""

from __future__ import annotations

import inspect
import json
import os
import posixpath
import re
from collections.abc import Callable, Iterable, Iterator, MutableMapping, Sequence
from contextlib import contextmanager, suppress
from datetime import date, datetime
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)
from urllib.parse import urlparse

import jinja2
import yaml
from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.languages import get_language
from docutils.parsers.rst import Directive, DirectiveError, directives, roles
from docutils.parsers.rst import Parser as RSTParser
from docutils.parsers.rst.directives.misc import Include
from docutils.parsers.rst.languages import get_language as get_language_rst
from docutils.statemachine import StringList
from docutils.transforms.components import Filter
from docutils.utils import Reporter, SystemMessage, new_document
from docutils.utils.code_analyzer import Lexer, LexerError, NumberLines
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.renderer import RendererProtocol
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from myst_parser import inventory
from myst_parser._compat import findall
from myst_parser.config.main import MdParserConfig, UrlSchemeType
from myst_parser.mocking import (
    MockIncludeDirective,
    MockingError,
    MockInliner,
    MockRSTParser,
    MockState,
    MockStateMachine,
)
from myst_parser.parsers.directives import MarkupError, parse_directive_text
from myst_parser.warnings_ import MystWarnings, create_warning

from .html_to_nodes import html_to_nodes

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


def make_document(source_path="notset", parser_cls=RSTParser) -> nodes.document:
    """Create a new docutils document, with the parser classes' default settings."""
    settings = get_default_settings(parser_cls)
    return new_document(source_path, settings=settings)


REGEX_SCHEME = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):")
"""RFC 7595: A non-empty scheme component followed by a colon (:),
consisting of a sequence of characters beginning with a letter
and followed by any combination of letters, digits, plus (+), period (.), or hyphen (-).
Although schemes are case-insensitive, the canonical form is lowercase
and documents that specify schemes must do so with lowercase letters.
"""
REGEX_URI_TEMPLATE = re.compile(
    r"{{\s*(uri|scheme|netloc|path|params|query|fragment)\s*}}"
)
REGEX_DIRECTIVE_START = re.compile(r"^[\s]{0,3}([`]{3,10}|[~]{3,10}|[:]{3,10})\{")


def token_line(token: SyntaxTreeNode, default: int | None = None) -> int:
    """Retrieve the initial line of a token."""
    if not getattr(token, "map", None):
        if default is not None:
            return default
        raise ValueError(f"token map not set: {token}")
    return token.map[0]  # type: ignore[index]


class DocutilsRenderer(RendererProtocol):
    """A markdown-it-py renderer to populate (in-place) a `docutils.document` AST.

    Note, this render is not dependent on Sphinx.
    """

    __output__ = "docutils"

    def __init__(self, parser: MarkdownIt) -> None:
        """Load the renderer (called by ``MarkdownIt``)"""
        self.md = parser
        self.rules = {
            k: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if k.startswith("render_") and k != "render_children"
        }
        # these are lazy loaded, when needed
        self._inventories: None | dict[str, inventory.InventoryType] = None

    def __getattr__(self, name: str):
        """Warn when the renderer has not been setup yet."""
        if name in (
            "md_env",
            "md_config",
            "md_options",
            "document",
            "current_node",
            "reporter",
            "language_module_rst",
            "_heading_offset",
            "_level_to_section",
        ):
            raise AttributeError(
                f"'{name}' attribute is not available until setup_render() is called"
            )
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def setup_render(
        self, options: dict[str, Any], env: MutableMapping[str, Any]
    ) -> None:
        """Setup the renderer with per render variables."""
        self.md_env = env
        self.md_options = options
        self.md_config: MdParserConfig = options["myst_config"]
        self.document: nodes.document = options.get("document", make_document())
        self.current_node: nodes.Element = options.get("current_node", self.document)
        self.reporter: Reporter = self.document.reporter
        # note there are actually two possible language modules:
        # one from docutils.languages, and one from docutils.parsers.rst.languages
        self.language_module_rst: ModuleType = get_language_rst(
            self.document.settings.language_code
        )
        self._heading_offset: int = 0
        # a mapping of heading levels to its currently associated node
        self._level_to_section: dict[int, nodes.document | nodes.section] = {
            0: self.document
        }
        # mapping of section slug to (line, id, implicit_text)
        self._heading_slugs: dict[str, tuple[int | None, str, str]] = {}

    @property
    def sphinx_env(self) -> BuildEnvironment | None:
        """Return the sphinx env, if using Sphinx."""
        try:
            return self.document.settings.env
        except AttributeError:
            return None

    def create_warning(
        self,
        message: str,
        subtype: MystWarnings | str,
        *,
        wtype: str | None = None,
        line: int | None = None,
        append_to: nodes.Element | None = None,
    ) -> nodes.system_message | None:
        """Generate a warning, logging if it is necessary.

        If the warning type is listed in the ``suppress_warnings`` configuration,
        then ``None`` will be returned and no warning logged.
        """
        return create_warning(
            self.document,
            message,
            subtype,
            wtype=wtype,
            line=line,
            append_to=append_to,
        )

    def _render_tokens(self, tokens: list[Token]) -> None:
        """Render the tokens."""
        # propagate line number down to inline elements
        for token in tokens:
            if not token.map:
                continue
            # For docutils we want 1 based line numbers (not 0)
            token.map = [token.map[0] + 1, token.map[1] + 1]
            for token_child in token.children or []:
                token_child.map = token.map

        # nest tokens
        node_tree = SyntaxTreeNode(tokens)
        # render
        for child in node_tree.children:
            # skip hidden?
            if f"render_{child.type}" in self.rules:
                self.rules[f"render_{child.type}"](child)
            else:
                self.create_warning(
                    f"No render method for: {child.type}",
                    MystWarnings.RENDER_METHOD,
                    line=token_line(child, default=0),
                    append_to=self.current_node,
                )

    def render(
        self, tokens: Sequence[Token], options, md_env: MutableMapping[str, Any]
    ) -> nodes.document:
        """Run the render on a token stream.

        :param tokens: list on block tokens to render
        :param options: params of parser instance
        :param md_env: the markdown-it environment sandbox associated with the tokens,
            containing additional metadata like reference info
        """
        self.setup_render(options, md_env)
        self._render_initialise()
        self._render_tokens(list(tokens))
        self._render_finalise()
        return self.document

    def _render_initialise(self) -> None:
        """Initialise the render of the document."""
        self.current_node.extend(
            html_meta_to_nodes(
                self.md_config.html_meta,
                document=self.document,
                line=0,
                reporter=self.reporter,
            )
        )

    def _render_finalise(self) -> None:
        """Finalise the render of the document."""

        # save for later reference resolution
        self.document.myst_slugs = self._heading_slugs
        if self._heading_slugs and self.sphinx_env:
            self.sphinx_env.metadata[self.sphinx_env.docname]["myst_slugs"] = (
                self._heading_slugs
            )

        # ensure these settings are set for later footnote transforms
        self.document.settings.myst_footnote_transition = (
            self.md_config.footnote_transition
        )
        self.document.settings.myst_footnote_sort = self.md_config.footnote_sort

        # log warnings for duplicate reference definitions
        # "duplicate_refs": [{"href": "ijk", "label": "B", "map": [4, 5], "title": ""}],
        for dup_ref in self.md_env.get("duplicate_refs", []):
            self.create_warning(
                f"Duplicate reference definition: {dup_ref['label']}",
                MystWarnings.MD_DEF_DUPE,
                line=dup_ref["map"][0] + 1,
                append_to=self.document,
            )

        # Add the wordcount, generated by the ``mdit_py_plugins.wordcount_plugin``.
        wordcount_metadata = self.md_env.get("wordcount", {})
        if wordcount_metadata:
            # save the wordcount to the sphinx BuildEnvironment metadata
            if self.sphinx_env is not None:
                meta = self.sphinx_env.metadata.setdefault(self.sphinx_env.docname, {})
                meta["wordcount"] = wordcount_metadata

            # now add the wordcount as substitution definitions,
            # so we can reference them in the document
            for key in ("words", "minutes"):
                value = wordcount_metadata.get(key, None)
                if value is None:
                    continue
                substitution_node = nodes.substitution_definition(
                    str(value), nodes.Text(str(value))
                )
                substitution_node.source = self.document["source"]
                substitution_node["names"].append(f"wordcount-{key}")
                self.document.note_substitution_def(
                    substitution_node, f"wordcount-{key}"
                )

    def nested_render_text(
        self,
        text: str,
        lineno: int,
        inline: bool = False,
        temp_root_node: None | nodes.Element = None,
        heading_offset: int = 0,
    ) -> None:
        """Render unparsed text (appending to the current node).

        :param text: the text to render
        :param lineno: the starting line number of the text, within the full source
        :param inline: whether the text is inline or block
        :param temp_root_node: If set, allow sections to be created as children of this node
        :param heading_offset: offset heading levels by this amount
        """
        tokens = (
            self.md.parseInline(text, self.md_env)
            if inline
            else self.md.parse(text + "\n", self.md_env)
        )

        # remove front matter, if present, e.g. from included documents
        if tokens and tokens[0].type == "front_matter":
            tokens.pop(0)

        # update the line numbers
        for token in tokens:
            if token.map:
                token.map = [token.map[0] + lineno, token.map[1] + lineno]

        @contextmanager
        def _restore():
            current_heading_offset = self._heading_offset
            self._heading_offset = heading_offset
            if temp_root_node is not None:
                # we need to temporarily set the root node,
                # and we also want to restore the level_to_section mapping at the end
                current_level_to_section = dict(self._level_to_section.items())
                current_root_node = self.md_env.get("temp_root_node", None)
                self.md_env["temp_root_node"] = temp_root_node
            yield
            self._heading_offset = current_heading_offset
            if temp_root_node is not None:
                self.md_env["temp_root_node"] = current_root_node
                self._level_to_section = current_level_to_section

        with _restore():
            self._render_tokens(tokens)

    @contextmanager
    def current_node_context(
        self, node: nodes.Element, append: bool = False
    ) -> Iterator[None]:
        """Context manager for temporarily setting the current node."""
        if append:
            self.current_node.append(node)
        current_node = self.current_node
        self.current_node = node
        yield
        self.current_node = current_node

    def render_children(self, token: SyntaxTreeNode) -> None:
        """Render the children of a token."""
        for child in token.children or []:
            if f"render_{child.type}" in self.rules:
                self.rules[f"render_{child.type}"](child)
            else:
                self.create_warning(
                    f"No render method for: {child.type}",
                    MystWarnings.RENDER_METHOD,
                    line=token_line(child, default=0),
                    append_to=self.current_node,
                )

    def add_line_and_source_path(self, node, token: SyntaxTreeNode) -> None:
        """Copy the line number and document source path to the docutils node."""
        with suppress(ValueError):
            node.line = token_line(token)
        node.source = self.document["source"]

    def add_line_and_source_path_r(
        self, nodes_: list[nodes.Element], token: SyntaxTreeNode
    ) -> None:
        """Copy the line number and document source path to the docutils nodes,
        and recursively to all descendants.
        """
        for node in nodes_:
            self.add_line_and_source_path(node, token)
            for child in findall(node)():
                self.add_line_and_source_path(child, token)

    def copy_attributes(
        self,
        token: SyntaxTreeNode,
        node: nodes.Element,
        keys: Sequence[str] = ("class",),
        *,
        converters: dict[str, Callable[[str], Any]] | None = None,
        aliases: dict[str, str] | None = None,
    ) -> None:
        """Copy attributes on the token to the docutils node.

        :param token: the token to copy attributes from
        :param node: the node to copy attributes to
        :param keys: the keys to copy from the token (after aliasing)
        :param converters: a dictionary of converters for the attributes
        :param aliases: a dictionary mapping the token key name to the node key name
        """
        if converters is None:
            converters = {}
        if aliases is None:
            aliases = {}
        for key, value in token.attrs.items():
            key = aliases.get(key, key)
            if key not in keys:
                continue
            if key == "class":
                node["classes"].extend(str(value).split())
            elif key == "id":
                name = nodes.fully_normalize_name(str(value))
                node["names"].append(name)
                self.document.note_explicit_target(node, node)
            else:
                if key in converters:
                    try:
                        value = converters[key](str(value))
                    except ValueError:
                        self.create_warning(
                            f"Invalid {key!r} attribute value: {token.attrs[key]!r}",
                            MystWarnings.INVALID_ATTRIBUTE,
                            line=token_line(token, default=0),
                            append_to=node,
                        )
                        continue
                node[key] = value

    def update_section_level_state(self, section: nodes.section, level: int) -> None:
        """Update the section level state, with the new current section and level."""
        # find the closest parent section
        parent_level = max(
            section_level
            for section_level in self._level_to_section
            if level > section_level
        )
        parent = self._level_to_section[parent_level]

        # if we are jumping up to a non-consecutive level,
        # then warn about this, since this will not be propagated in the docutils AST
        if (level > parent_level) and (parent_level + 1 != level):
            msg = f"Non-consecutive header level increase; H{parent_level} to H{level}"
            if parent_level == 0:
                msg = f"Document headings start at H{level}, not H1"
            self.create_warning(
                msg,
                MystWarnings.MD_HEADING_NON_CONSECUTIVE,
                line=section.line,
                append_to=self.current_node,
            )

        # append the new section to the parent
        parent.append(section)
        # update the state for this section level
        self._level_to_section[level] = section

        # Remove all descendant sections from the section level state
        self._level_to_section = {
            section_level: section
            for section_level, section in self._level_to_section.items()
            if section_level <= level
        }

    def renderInlineAsText(self, tokens: list[SyntaxTreeNode]) -> str:  # noqa: N802
        """Special kludge for image `alt` attributes to conform CommonMark spec.

        Don't try to use it! Spec requires to show `alt` content with stripped markup,
        instead of simple escaping.
        """
        result = ""

        for token in tokens or []:
            if token.type == "text":
                result += token.content
            # elif token.type == "image":
            #     result += self.renderInlineAsText(token.children)
            else:
                result += self.renderInlineAsText(token.children or [])
        return result

    # ### render methods for commonmark tokens

    def render_paragraph(self, token: SyntaxTreeNode) -> None:
        para = nodes.paragraph(token.children[0].content if token.children else "")
        self.copy_attributes(token, para, keys=("class", "id"))
        self.add_line_and_source_path(para, token)
        with self.current_node_context(para, append=True):
            self.render_children(token)

    def render_inline(self, token: SyntaxTreeNode) -> None:
        self.render_children(token)

    def render_text(self, token: SyntaxTreeNode) -> None:
        self.current_node.append(nodes.Text(token.content))

    def render_bullet_list(self, token: SyntaxTreeNode) -> None:
        list_node = nodes.bullet_list()
        if token.markup:
            list_node["bullet"] = token.markup
        self.copy_attributes(token, list_node, keys=("class", "id"))
        self.add_line_and_source_path(list_node, token)
        with self.current_node_context(list_node, append=True):
            self.render_children(token)

    def render_ordered_list(self, token: SyntaxTreeNode) -> None:
        style = "arabic"
        if "style" in token.attrs:
            style = {
                "decimal": "arabic",
                "lower-alpha": "loweralpha",
                "upper-alpha": "upperalpha",
                "lower-roman": "lowerroman",
                "upper-roman": "upperroman",
            }.get(str(token.attrs["style"]), style)
        list_node = nodes.enumerated_list(enumtype=style, prefix="")
        list_node["suffix"] = token.markup  # for CommonMark, this should be "." or ")"
        # start is starting number
        self.copy_attributes(token, list_node, keys=("class", "id", "start"))
        self.add_line_and_source_path(list_node, token)
        with self.current_node_context(list_node, append=True):
            self.render_children(token)

    def render_list_item(self, token: SyntaxTreeNode) -> None:
        item_node = nodes.list_item()
        self.copy_attributes(token, item_node, keys=("class", "id"))
        self.add_line_and_source_path(item_node, token)
        with self.current_node_context(item_node, append=True):
            self.render_children(token)

    def render_em(self, token: SyntaxTreeNode) -> None:
        node = nodes.emphasis()
        self.add_line_and_source_path(node, token)
        with self.current_node_context(node, append=True):
            self.render_children(token)

    def render_softbreak(self, token: SyntaxTreeNode) -> None:
        self.current_node.append(nodes.Text("\n"))

    def render_hardbreak(self, token: SyntaxTreeNode) -> None:
        self.current_node.append(nodes.raw("", "<br />\n", format="html"))
        self.current_node.append(nodes.raw("", "\\\\\n", format="latex"))

    def render_strong(self, token: SyntaxTreeNode) -> None:
        node = nodes.strong()
        self.add_line_and_source_path(node, token)
        with self.current_node_context(node, append=True):
            self.render_children(token)

    def render_blockquote(self, token: SyntaxTreeNode) -> None:
        quote = nodes.block_quote()
        self.copy_attributes(token, quote, keys=("class", "id"))
        self.add_line_and_source_path(quote, token)
        with self.current_node_context(quote, append=True):
            self.render_children(token)
            if "attribution" in token.attrs:
                attribution = nodes.attribution(token.attrs["attribution"], "")
                self.add_line_and_source_path(attribution, token)
                with self.current_node_context(attribution, append=True):
                    self.nested_render_text(
                        str(token.attrs["attribution"]),
                        token_line(token, 0),
                        inline=True,
                    )

    def render_hr(self, token: SyntaxTreeNode) -> None:
        node = nodes.transition()
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_code_inline(self, token: SyntaxTreeNode) -> None:
        node = nodes.literal(token.content, token.content)
        self.add_line_and_source_path(node, token)
        self.copy_attributes(
            token,
            node,
            ("class", "id", "language"),
            aliases={"lexer": "language", "l": "language"},
        )
        if "language" in node and "code" not in node["classes"]:
            node["classes"].append("code")
        self.current_node.append(node)

    @staticmethod
    def _parse_linenos(emphasize_lines: str, num_lines: int) -> list[int]:
        """Parse the `emphasize_lines` argument.

        Raises ValueError if the argument is invalid.
        """
        from sphinx.util import parselinenos

        hl_lines = parselinenos(emphasize_lines, num_lines)
        if any(i >= num_lines for i in hl_lines):
            raise ValueError(f"out of range(1-{num_lines}")

        return [x + 1 for x in hl_lines if x < num_lines]

    def create_highlighted_code_block(
        self,
        text: str,
        lexer_name: str | None,
        number_lines: bool = False,
        lineno_start: int = 1,
        source: str | None = None,
        line: int | None = None,
        node_cls: type[nodes.Element] = nodes.literal_block,
        emphasize_lines: list[int] | str | None = None,
    ) -> nodes.Element:
        """Create a literal block with syntax highlighting.

        This mimics the behaviour of the `code-block` directive.

        In docutils, this directive directly parses the text with the pygments lexer,
        whereas in sphinx, the lexer name is only recorded as the `language` attribute,
        and the text is lexed later by pygments within the `visit_literal_block`
        method of the output format ``SphinxTranslator``.

        Note, this function does not add the literal block to the document.
        """
        if self.sphinx_env is not None:
            node = node_cls(text, text, language=lexer_name or "none")
            if number_lines:
                node["linenos"] = True
                if lineno_start != 1:
                    node["highlight_args"] = {"linenostart": lineno_start}
            if isinstance(emphasize_lines, str):
                try:
                    emphasize_lines = self._parse_linenos(
                        emphasize_lines, len(text.splitlines())
                    )
                except ValueError as err:
                    self.create_warning(
                        f"emphasize_lines: {err}",
                        MystWarnings.INVALID_ATTRIBUTE,
                        line=line,
                    )
            if isinstance(emphasize_lines, list | tuple):
                # TODO emphasize_lines in docutils?
                if "highlight_args" not in node:
                    node["highlight_args"] = {}
                node["highlight_args"]["hl_lines"] = emphasize_lines
        else:
            node = node_cls(
                text, classes=["code"] + ([lexer_name] if lexer_name else [])
            )
            try:
                lex_tokens = Lexer(
                    text,
                    lexer_name or "",
                    "short" if self.md_config.highlight_code_blocks else "none",
                )
            except LexerError as err:
                self.reporter.warning(
                    str(err),
                    **{
                        name: value
                        for name, value in (("source", source), ("line", line))
                        if value is not None
                    },
                )
                lex_tokens = Lexer(text, lexer_name or "", "none")

            if number_lines:
                lex_tokens = NumberLines(
                    lex_tokens, lineno_start, lineno_start + len(text.splitlines())
                )

            for classes, value in lex_tokens:
                if classes:
                    node += nodes.inline(value, value, classes=classes)
                else:
                    # insert as Text to decrease the verbosity of the output
                    node += nodes.Text(value)

        if source is not None:
            node.source = source
        if line is not None:
            node.line = line
        return node

    def render_code_block(self, token: SyntaxTreeNode) -> None:
        lexer = token.info.split()[0] if token.info else None
        lineno_start = 1
        number_lines = False
        emphasize_lines = (
            str(token.attrs.get("emphasize-lines"))
            if "emphasize-lines" in token.attrs
            else None
        )
        if "lineno-start" in token.attrs:
            with suppress(ValueError):
                lineno_start = int(token.attrs["lineno-start"])
                number_lines = True
        node = self.create_highlighted_code_block(
            token.content,
            lexer,
            lineno_start=lineno_start,
            number_lines=number_lines,
            source=self.document["source"],
            line=token_line(token, 0) or None,
            emphasize_lines=emphasize_lines,
        )
        self.copy_attributes(token, node, ("class", "id"))
        self.current_node.append(node)

    def render_fence(self, token: SyntaxTreeNode) -> None:
        """Render a fenced code block."""
        # split the info into possible ```name arguments
        parts = (token.info.strip() if token.info else "").split(maxsplit=1)
        name = parts[0] if parts else ""
        arguments = parts[1] if len(parts) > 1 else ""

        if (not self.md_config.commonmark_only) and (not self.md_config.gfm_only):
            if name == "{eval-rst}":
                return self.render_restructuredtext(token)
            if name.startswith("{") and name.endswith("}"):
                return self.render_directive(token, name[1:-1], arguments)
            if name in self.md_config.fence_as_directive:
                options = {k: str(v) for k, v in token.attrs.items()}
                if "id" in options:
                    options["name"] = options.pop("id")
                return self.render_directive(
                    token, name, arguments, additional_options=options
                )

        if not name and self.sphinx_env is not None:
            # use the current highlight setting, via the ``highlight`` directive,
            # or ``highlight_language`` configuration.
            name = (
                self.sphinx_env.temp_data.get("highlight_language")
                or self.sphinx_env.config.highlight_language
            )

        lineno_start = 1
        number_lines = name in self.md_config.number_code_blocks
        emphasize_lines = (
            str(token.attrs.get("emphasize-lines"))
            if "emphasize-lines" in token.attrs
            else None
        )
        if "lineno-start" in token.attrs:
            with suppress(ValueError):
                lineno_start = int(token.attrs["lineno-start"])
                number_lines = True

        node = self.create_highlighted_code_block(
            token.content,
            name,
            number_lines=number_lines,
            lineno_start=lineno_start,
            source=self.document["source"],
            line=token_line(token, 0) or None,
            emphasize_lines=emphasize_lines,
        )
        self.copy_attributes(token, node, ("class", "id"))
        self.current_node.append(node)

    @property
    def blocks_mathjax_processing(self) -> bool:
        """Only add mathjax ignore classes if using sphinx,
        and using the ``dollarmath`` extension, and ``myst_update_mathjax=True``.
        """
        return (
            self.sphinx_env is not None
            and "dollarmath" in self.md_config.enable_extensions
            and self.md_config.update_mathjax
        )

    def generate_heading_target(
        self,
        token: SyntaxTreeNode,
        level: int,
        node: nodes.Element,
        title_node: nodes.Element,
    ) -> None:
        """Generate a heading target, and add it to the document."""

        implicit_text = clean_astext(title_node)

        # create a target reference for the section, based on the heading text.
        # Note, this is an implicit target, meaning that it is not prioritised,
        # during ref resolution, and is not stored in the document.
        # TODO this is purely to mimic docutils, but maybe we don't need it?
        # (since we have the slugify logic below)
        name = nodes.fully_normalize_name(implicit_text)
        node["names"].append(name)
        self.document.note_implicit_target(node, node)

        if level > self.md_config.heading_anchors:
            return

        # Create an implicit reference slug.
        # The problem with this reference slug,
        # is that it might not be in the "normalised" format required by docutils,
        # https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#normalized-reference-names
        # so we store it separately, and have separate logic than docutils
        # TODO maybe revisit this assumption, or improve the logic
        try:
            slug = compute_unique_slug(
                token,
                self._heading_slugs,
                self.md_config.heading_slug_func,
            )
        except Exception as error:
            self.create_warning(
                str(error),
                MystWarnings.HEADING_SLUG,
                line=token_line(token, default=0),
                append_to=self.current_node,
            )
        else:
            node["slug"] = slug
            self._heading_slugs[slug] = (node.line, node["ids"][0], implicit_text)

    def render_heading(self, token: SyntaxTreeNode) -> None:
        """Render a heading, e.g. `# Heading`."""

        level = int(token.tag[1]) + self._heading_offset

        # sections are only allowed as a parent of a document or another section
        # the only exception to this, is if a directive has called a nested parse,
        # and specifically specified that sections are allowed to be created as children
        # of its root node (a.k.a match_titles=True)
        parent_of_temp_root = (
            self.md_env.get("temp_root_node", None) is not None
            and self.current_node == self.md_env["temp_root_node"]
        )
        if not (
            parent_of_temp_root
            or isinstance(self.current_node, nodes.document | nodes.section)
        ):
            # if this is not the case, we create a rubric node instead
            rubric = nodes.rubric(token.content, "", level=level)
            self.add_line_and_source_path(rubric, token)
            self.copy_attributes(token, rubric, ("class", "id"))
            with self.current_node_context(rubric, append=True):
                self.render_children(token)
            self.generate_heading_target(token, level, rubric, rubric)
            return

        # create the section node
        new_section = nodes.section()
        self.add_line_and_source_path(new_section, token)
        self.copy_attributes(token, new_section, ("class", "id"))
        # if a top level section,
        # then add classes to set default mathjax processing to false
        # we then turn it back on, on a per-node basis
        if level == 1 and self.blocks_mathjax_processing:
            new_section["classes"].extend(["tex2jax_ignore", "mathjax_ignore"])

        # update the state of the section levels
        self.update_section_level_state(new_section, level)

        # create the title for this section
        title_node = nodes.title(token.children[0].content if token.children else "")
        self.add_line_and_source_path(title_node, token)
        new_section.append(title_node)
        # render the heading children into the title
        with self.current_node_context(title_node):
            self.render_children(token)

        self.generate_heading_target(token, level, new_section, title_node)

        # set the section as the current node for subsequent rendering
        self.current_node = new_section

    def render_link(self, token: SyntaxTreeNode) -> None:
        """Parse `<http://link.com>` or `[text](link "title")` syntax to docutils AST:

        - If `myst_all_links_external` is True, forward to `render_link_url`
        - If the link token has a class attribute containing `external`,
            forward to `render_link_url`
        - If the link is an id link (e.g. `#id`), forward to `render_link_anchor`
        - If the link has a schema, and the schema is in `url_schemes` (e.g. `http:`),
          forward to `render_link_url`
        - If the link has an `inv:` schema, forward to `render_link_inventory`
        - If the link is an autolink/linkify type link, forward to `render_link_url`
        - Otherwise, forward to `render_link_internal`
        """
        if (
            self.md_config.commonmark_only
            or self.md_config.gfm_only
            or self.md_config.all_links_external
        ):
            return self.render_link_url(token)

        if "class" in token.attrs and "external" in str(token.attrs["class"]).split():
            return self.render_link_url(token)

        href = cast(str, token.attrGet("href") or "")
        if href.startswith("#"):
            return self.render_link_anchor(token, href)

        scheme_match = REGEX_SCHEME.match(href)
        scheme = None if scheme_match is None else scheme_match.group(1)
        if scheme in self.md_config.url_schemes:
            return self.render_link_url(token, self.md_config.url_schemes[scheme])

        if scheme == "inv":
            return self.render_link_inventory(token)
        if scheme == "path":
            return self.render_link_path(token)
        if scheme == "project":
            return self.render_link_project(token)

        if token.info == "auto":
            # handles both autolink and linkify
            return self.render_link_url(token)

        return self.render_link_unknown(token)

    def render_link_url(
        self, token: SyntaxTreeNode, conversion: None | UrlSchemeType = None
    ) -> None:
        """Render link token (including autolink and linkify),
        where the link has been identified as an external URL.
        """
        ref_node = nodes.reference()
        self.add_line_and_source_path(ref_node, token)
        attribute_keys = ["class", "id", "reftitle", "target", "rel"]
        if self.md_config.links_external_new_tab:
            token.attrs["target"] = "_blank"
            token.attrs["rel"] = "noreferer noopener"
        self.copy_attributes(
            token, ref_node, attribute_keys, aliases={"title": "reftitle"}
        )
        uri = cast(str, token.attrGet("href") or "")
        implicit_text: str | None = None

        if conversion is not None:
            # implicit_template: str | None = None
            # if isinstance(conversion, (list, tuple)):
            #     href_template, implicit_template = conversion
            # else:
            #     href_template = conversion
            # markdown-it encodes unsafe characters with percent-encoding
            # we want to get back the original, source input
            uri = self.md.normalizeLinkText(uri)
            _parsed = urlparse(uri)
            parsed = {
                "uri": uri,
                "scheme": _parsed.scheme,
                "netloc": _parsed.netloc,
                "path": _parsed.path,
                "params": _parsed.params,
                "query": _parsed.query,
                "fragment": _parsed.fragment,
            }
            # Note we specifically do not use jinja2 here,
            # to restrict the scope of the templating language,
            # so that it can be used in a language agnostic way
            if "url" in conversion:
                uri = re.sub(
                    REGEX_URI_TEMPLATE,
                    lambda match: parsed.get(match.group(1), ""),
                    conversion["url"],
                )
                uri = self.md.normalizeLink(uri)
            if "title" in conversion and (token.info == "auto" or not token.children):
                implicit_text = re.sub(
                    REGEX_URI_TEMPLATE,
                    lambda match: parsed.get(match.group(1), ""),
                    conversion["title"],
                )
            if "classes" in conversion:
                ref_node["classes"].extend(conversion["classes"])

        ref_node["refuri"] = escapeHtml(uri)
        if implicit_text is not None:
            with self.current_node_context(ref_node, append=True):
                self.current_node.append(nodes.Text(implicit_text))
        else:
            with self.current_node_context(ref_node, append=True):
                self.render_children(token)

    def render_link_path(self, token: SyntaxTreeNode) -> None:
        """Render a link token like `<path:...>`."""
        self.create_warning(
            "`path:` scheme not yet supported in docutils",
            MystWarnings.NOT_SUPPORTED,
            line=token_line(token, 0),
            append_to=self.current_node,
        )
        return self.render_link_url(token)

    def render_link_project(self, token: SyntaxTreeNode) -> None:
        """Render a link token like `<project:...>`."""
        destination = cast(str, token.attrGet("href") or "")
        if destination.startswith("project:"):
            destination = destination[8:]
        if destination.startswith("#"):
            return self.render_link_anchor(token, destination)
        self.create_warning(
            "`project:` scheme for file paths not yet supported in docutils",
            MystWarnings.NOT_SUPPORTED,
            line=token_line(token, 0),
            append_to=self.current_node,
        )
        return self.render_link_url(token)

    def render_link_anchor(self, token: SyntaxTreeNode, target: str) -> None:
        """Render link token like `[text](#target)`, to a local target.

        :target: the target id, e.g. `#target`
        """
        ref_node = nodes.reference()
        self.add_line_and_source_path(ref_node, token)
        ref_node["id_link"] = True
        ref_node["refuri"] = self.md.normalizeLinkText(target)
        self.copy_attributes(
            token, ref_node, ("class", "id", "reftitle"), aliases={"title": "reftitle"}
        )
        self.current_node.append(ref_node)
        if token.info != "auto":
            with self.current_node_context(ref_node):
                self.render_children(token)

    def render_link_unknown(self, token: SyntaxTreeNode) -> None:
        """Render link token `[text](link "title")`,
        where the link has not been identified as an external URL::

            <reference refname="link" title="title">
                text

        `text` can contain nested syntax, e.g. `[**bold**](link "title")`.

        Note, this is overridden by `SphinxRenderer`, to use `pending_xref` nodes.
        """
        ref_node = nodes.reference()
        self.add_line_and_source_path(ref_node, token)
        self.copy_attributes(
            token, ref_node, ("class", "id", "reftitle"), aliases={"title": "reftitle"}
        )
        ref_node["refname"] = cast(str, token.attrGet("href") or "")
        self.document.note_refname(ref_node)
        with self.current_node_context(ref_node, append=True):
            self.render_children(token)

    def render_link_inventory(self, token: SyntaxTreeNode) -> None:
        r"""Create a link to an inventory object.

        This assumes the href is of the form `<scheme>:<path>#<target>`.
        The path is of the form `<invs>:<domains>:<otypes>`,
        where each of the parts is optional, hence `<scheme>:#<target>` is also valid.
        Each of the path parts can contain the `*` wildcard, for example:
        `<scheme>:key:*:obj#targe*`.
        `\*` is treated as a plain `*`.
        """

        # markdown-it encodes unsafe characters with percent-encoding
        # we want to get back the original, source input
        href = self.md.normalizeLinkText(cast(str, token.attrGet("href") or ""))

        # note if the link had explicit text or not (autolinks are always implicit)
        explicit = (token.info != "auto") and bool(token.children)

        # split the href up into parts
        uri_parts = urlparse(href)
        target = uri_parts.fragment
        invs, domains, otypes = None, None, None
        if uri_parts.path:
            path_parts = uri_parts.path.split(":")
            with suppress(IndexError):
                invs = path_parts[0]
                domains = path_parts[1]
                otypes = path_parts[2]

        # find the matches
        matches = self.get_inventory_matches(
            target=target, invs=invs, domains=domains, otypes=otypes
        )

        # warn for 0 or >1 matches
        if not matches:
            filter_str = inventory.filter_string(invs, domains, otypes, target)
            self.create_warning(
                f"No matches for {filter_str!r}",
                MystWarnings.IREF_MISSING,
                line=token_line(token, default=0),
                append_to=self.current_node,
            )
            return
        if len(matches) > 1:
            show_num = 3
            filter_str = inventory.filter_string(invs, domains, otypes, target)
            matches_str = ", ".join(
                [
                    inventory.filter_string(m.inv, m.domain, m.otype, m.name)
                    for m in matches[:show_num]
                ]
            )
            if len(matches) > show_num:
                matches_str += ", ..."
            self.create_warning(
                f"Multiple matches for {filter_str!r}: {matches_str}",
                MystWarnings.IREF_AMBIGUOUS,
                line=token_line(token, default=0),
                append_to=self.current_node,
            )

        # create the docutils node
        match = matches[0]
        ref_node = nodes.reference("", "", internal=False)
        ref_node["inv_match"] = inventory.filter_string(
            match.inv, match.domain, match.otype, match.name
        )
        self.add_line_and_source_path(ref_node, token)
        self.copy_attributes(
            token, ref_node, ("class", "id", "reftitle"), aliases={"title": "reftitle"}
        )
        ref_node["refuri"] = (
            posixpath.join(match.base_url, match.loc) if match.base_url else match.loc
        )
        if "reftitle" not in ref_node:
            ref_node["reftitle"] = f"{match.project} {match.version}".strip()
        self.current_node.append(ref_node)
        if explicit:
            with self.current_node_context(ref_node):
                self.render_children(token)
        elif match.text:
            ref_node.append(nodes.Text(match.text))
        else:
            ref_node.append(nodes.literal(match.name, match.name))

    def get_inventory_matches(
        self,
        *,
        invs: str | None,
        domains: str | None,
        otypes: str | None,
        target: str | None,
    ) -> list[inventory.InvMatch]:
        """Return inventory matches.

        This will be overridden for sphinx, to use intersphinx config.
        """
        if self._inventories is None:
            self._inventories = {}
            for key, (uri, path) in self.md_config.inventories.items():
                load_path = posixpath.join(uri, "objects.inv") if path is None else path
                self.reporter.info(f"Loading inventory {key!r}: {load_path}")
                try:
                    inv = inventory.fetch_inventory(load_path, base_url=uri)
                except Exception as exc:
                    self.create_warning(
                        f"Failed to load inventory {key!r}: {exc}",
                        MystWarnings.INV_LOAD,
                    )
                else:
                    self._inventories[key] = inv

        return list(
            inventory.filter_inventories(
                self._inventories,
                invs=invs,
                domains=domains,
                otypes=otypes,
                targets=target,
            )
        )

    def render_html_inline(self, token: SyntaxTreeNode) -> None:
        self.render_html_block(token)

    def render_html_block(self, token: SyntaxTreeNode) -> None:
        node_list = html_to_nodes(token.content, token_line(token), self)
        self.current_node.extend(node_list)

    def render_image(self, token: SyntaxTreeNode) -> None:
        img_node = nodes.image()
        self.add_line_and_source_path(img_node, token)
        destination = cast(str, token.attrGet("src") or "")

        if self.md_env.get(
            "relative-images", None
        ) is not None and not REGEX_SCHEME.match(destination):
            # make the path relative to an "including" document
            # this is set when using the `relative-images` option of the MyST `include` directive
            destination = os.path.normpath(
                os.path.join(
                    self.md_env.get("relative-images", ""),
                    os.path.normpath(destination),
                )
            )

        img_node["uri"] = destination

        img_node["alt"] = self.renderInlineAsText(token.children or [])

        self.copy_attributes(
            token,
            img_node,
            ("class", "id", "title", "width", "height", "align"),
            converters={
                "width": directives.length_or_percentage_or_unitless,
                "height": directives.length_or_unitless,
                "align": lambda x: directives.choice(x, ("left", "center", "right")),
            },
            aliases={"w": "width", "h": "height", "a": "align"},
        )

        self.current_node.append(img_node)

    # ### render methods for plugin tokens

    def render_span(self, token: SyntaxTreeNode) -> None:
        """Render an inline span token."""
        node = nodes.inline()
        self.add_line_and_source_path(node, token)
        self.copy_attributes(token, node, ("class", "id"))
        with self.current_node_context(node, append=True):
            self.render_children(token)

    def render_front_matter(self, token: SyntaxTreeNode) -> None:
        """Pass document front matter data."""
        position = token_line(token, default=0)

        if isinstance(token.content, str):
            try:
                data = yaml.safe_load(token.content)
            except (yaml.parser.ParserError, yaml.scanner.ScannerError):
                self.create_warning(
                    "Malformed YAML",
                    MystWarnings.MD_TOPMATTER,
                    line=position,
                    append_to=self.current_node,
                )
                return
        else:
            data = token.content

        if not isinstance(data, dict):
            self.create_warning(
                f"YAML is not a dict: {type(data)}",
                MystWarnings.MD_TOPMATTER,
                line=position,
                append_to=self.current_node,
            )
            return

        fields = {
            k: v
            for k, v in data.items()
            if k not in ("myst", "mystnb", "substitutions", "html_meta")
        }
        if fields:
            field_list = self.dict_to_fm_field_list(
                fields, language_code=self.document.settings.language_code
            )
            self.current_node.append(field_list)

        if data.get("title") and self.md_config.title_to_header:
            self.nested_render_text(f"# {data['title']}", 0)

    def dict_to_fm_field_list(
        self, data: dict[str, Any], language_code: str, line: int = 0
    ) -> nodes.field_list:
        """Render each key/val pair as a docutils ``field_node``.

        Bibliographic keys below will be parsed as Markdown,
        all others will be left as literal text.

        The field list should be at the start of the document,
        and will then be converted to a `docinfo` node during the
        `docutils.docutils.transforms.frontmatter.DocInfo` transform (priority 340),
        and bibliographic keys (or their translation) will be converted to nodes::

            {'author': docutils.nodes.author,
            'authors': docutils.nodes.authors,
            'organization': docutils.nodes.organization,
            'address': docutils.nodes.address,
            'contact': docutils.nodes.contact,
            'version': docutils.nodes.version,
            'revision': docutils.nodes.revision,
            'status': docutils.nodes.status,
            'date': docutils.nodes.date,
            'copyright': docutils.nodes.copyright,
            'dedication': docutils.nodes.topic,
            'abstract': docutils.nodes.topic}

        Also, the 'dedication' and 'abstract' will be placed outside the `docinfo`,
        and so will always be shown in the document.

        If using sphinx, this `docinfo` node will later be extracted from the AST,
        by the `DoctreeReadEvent` transform (priority 880),
        calling `MetadataCollector.process_doc`.
        In this case keys and values will be converted to strings and stored in
        `app.env.metadata[app.env.docname]`

        See
        https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html
        for docinfo fields used by sphinx.

        """
        field_list = nodes.field_list()
        field_list.source, field_list.line = self.document["source"], line

        bibliofields = get_language(language_code).bibliographic_fields

        for key, value in data.items():
            if not isinstance(value, str | int | float | date | datetime):
                value = json.dumps(value)
            value = str(value)
            body = nodes.paragraph()
            body.source, body.line = self.document["source"], line
            if key in bibliofields:
                with self.current_node_context(body):
                    self.nested_render_text(value, line, inline=True)
            else:
                body += nodes.literal(value, value)

            field_node = nodes.field()
            field_node.source = value
            field_node += nodes.field_name(key, "", nodes.Text(key))
            field_node += nodes.field_body(value, *[body])
            field_list += field_node

        return field_list

    def render_table(self, token: SyntaxTreeNode) -> None:
        # markdown-it table always contains at least a header:
        assert token.children
        header = token.children[0]
        # with one header row
        assert header.children
        header_row = header.children[0]
        assert header_row.children

        # top-level element
        table = nodes.table()
        table["classes"] += ["colwidths-auto"]
        self.copy_attributes(token, table, ("class", "id"))
        self.add_line_and_source_path(table, token)
        self.current_node.append(table)

        # column settings element
        maxcols = len(header_row.children)
        colwidths = [100 // maxcols] * maxcols
        tgroup = nodes.tgroup(cols=len(colwidths))
        table += tgroup
        for colwidth in colwidths:
            colspec = nodes.colspec(colwidth=colwidth)
            tgroup += colspec

        # header
        thead = nodes.thead()
        tgroup += thead
        with self.current_node_context(thead):
            self.render_table_row(header_row)

        # body
        if len(token.children) > 1:
            body = token.children[1]
            tbody = nodes.tbody()
            tgroup += tbody
            with self.current_node_context(tbody):
                for body_row in body.children or []:
                    self.render_table_row(body_row)

    def render_table_row(self, token: SyntaxTreeNode) -> None:
        row = nodes.row()
        with self.current_node_context(row, append=True):
            for child in token.children or []:
                entry = nodes.entry()
                para = nodes.paragraph(
                    child.children[0].content if child.children else ""
                )
                style = child.attrGet("style")  # i.e. the alignment when using e.g. :--
                if style and style in (
                    "text-align:left",
                    "text-align:right",
                    "text-align:center",
                ):
                    entry["classes"].append(f"text-{cast(str, style).split(':')[1]}")
                with (
                    self.current_node_context(entry, append=True),
                    self.current_node_context(para, append=True),
                ):
                    self.render_children(child)

    def render_s(self, token: SyntaxTreeNode) -> None:
        """Render a strikethrough token."""
        # TODO strikethrough not currently directly supported in docutils
        self.create_warning(
            "Strikethrough is currently only supported in HTML output",
            MystWarnings.STRIKETHROUGH,
            line=token_line(token, 0),
            append_to=self.current_node,
        )
        self.current_node.append(nodes.raw("", "<s>", format="html"))
        self.render_children(token)
        self.current_node.append(nodes.raw("", "</s>", format="html"))

    def render_math_inline(self, token: SyntaxTreeNode) -> None:
        content = token.content
        node = nodes.math(content, content)
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_math_inline_double(self, token: SyntaxTreeNode) -> None:
        content = token.content
        node = nodes.math_block(content, content, nowrap=False, number=None)
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_math_single(self, token: SyntaxTreeNode) -> None:
        content = token.content
        node = nodes.math(content, content)
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_math_block(self, token: SyntaxTreeNode) -> None:
        content = token.content
        node = nodes.math_block(content, content, nowrap=False, number=None)
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_math_block_label(self, token: SyntaxTreeNode) -> None:
        content = token.content
        label = token.info
        node = nodes.math_block(content, content, nowrap=False, number=None)
        self.add_line_and_source_path(node, token)
        name = nodes.fully_normalize_name(label)
        node["names"].append(name)
        self.document.note_explicit_target(node, node)
        self.current_node.append(node)

    def render_amsmath(self, token: SyntaxTreeNode) -> None:
        # note docutils does not currently support the nowrap attribute
        # or equation numbering, so this is overridden in the sphinx renderer
        node = nodes.math_block(
            token.content, token.content, nowrap=True, classes=["amsmath"]
        )
        if token.meta["numbered"] != "*":
            node["numbered"] = True
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_footnote_ref(self, token: SyntaxTreeNode) -> None:
        """Footnote references are added as auto-numbered,
        .i.e. `[^a]` is read as rST `[#a]_`
        """
        target = token.meta["label"]

        refnode = nodes.footnote_reference(f"[^{target}]")
        self.add_line_and_source_path(refnode, token)
        if target.isdigit():
            # a manually numbered footnote, similar to rST ``[1]_``
            refnode += nodes.Text(target)
        else:
            # an auto-numbered footnote, similar to rST ``[#label]_``
            refnode["auto"] = 1
            self.document.note_autofootnote_ref(refnode)

        refnode["refname"] = target
        self.document.note_footnote_ref(refnode)

        self.current_node.append(refnode)

    def render_footnote_reference(self, token: SyntaxTreeNode) -> None:
        """Despite the name, this is actually a footnote definition, e.g. `[^a]: ...`"""
        target = token.meta["label"]

        if target in self.document.nameids:
            # note we chose to directly omit these footnotes in the parser,
            # rather than let docutils/sphinx handle them, since otherwise you end up with a confusing warning:
            # WARNING: Duplicate explicit target name: "x". [docutils]
            # we use [ref.footnote] as the type/subtype, rather than a myst specific warning,
            # to make it more aligned with sphinx warnings for unreferenced footnotes
            self.create_warning(
                f"Duplicate footnote definition found for label: '{target}'",
                "footnote",
                wtype="ref",
                line=token_line(token),
                append_to=self.current_node,
            )
            return

        footnote = nodes.footnote()
        self.add_line_and_source_path(footnote, token)
        footnote["names"].append(target)
        if target.isdigit():
            # a manually numbered footnote, similar to rST ``.. [1]``
            footnote += nodes.label("", target)
            self.document.note_footnote(footnote)
        else:
            # an auto-numbered footnote, similar to rST ``.. [#label]``
            footnote["auto"] = 1
            self.document.note_autofootnote(footnote)

        self.document.note_explicit_target(footnote, footnote)
        with self.current_node_context(footnote, append=True):
            self.render_children(token)

    def render_myst_block_break(self, token: SyntaxTreeNode) -> None:
        block_break = nodes.comment(token.content, token.content)
        block_break["classes"] += ["block_break"]
        self.add_line_and_source_path(block_break, token)
        self.current_node.append(block_break)

    def render_myst_target(self, token: SyntaxTreeNode) -> None:
        text = token.content
        name = nodes.fully_normalize_name(text)
        target = nodes.target(text)
        target["names"].append(name)
        self.add_line_and_source_path(target, token)
        self.document.note_explicit_target(target, self.current_node)
        self.current_node.append(target)

    def render_myst_line_comment(self, token: SyntaxTreeNode) -> None:
        self.current_node.append(nodes.comment(token.content, token.content.strip()))

    def render_myst_role(self, token: SyntaxTreeNode) -> None:
        name = token.meta["name"]
        text = token.content
        rawsource = f":{name}:`{token.content}`"
        lineno = token_line(token) if token.map else 0
        role_func, messages = roles.role(
            name, self.language_module_rst, lineno, self.reporter
        )
        if not role_func:
            self.create_warning(
                f'Unknown interpreted text role "{name}".',
                MystWarnings.UNKNOWN_ROLE,
                line=lineno,
                append_to=self.current_node,
            )
            self.current_node.extend(messages)
            return
        inliner = MockInliner(self)
        _nodes, messages2 = role_func(name, rawsource, text, lineno, inliner)
        self.current_node += _nodes + messages2

    def render_colon_fence(self, token: SyntaxTreeNode) -> None:
        """Render a div block, with ``:`` colon delimiters."""
        # split the info into possible :::name arguments
        parts = (token.info.strip() if token.info else "").split(maxsplit=1)
        name = parts[0] if parts else ""
        arguments = parts[1] if len(parts) > 1 else ""

        if name.startswith("{") and name.endswith("}"):
            if token.content.startswith(":::"):
                # the content starts with a nested fence block,
                # but must distinguish between ``:options:``, so we add a new line
                assert token.token is not None, '"colon_fence" must have a `token`'
                linear_token = token.token.copy()
                linear_token.content = "\n" + linear_token.content
                token.token = linear_token
            return self.render_directive(token, name[1:-1], arguments)

        container = nodes.container(is_div=True)
        self.add_line_and_source_path(container, token)
        self.copy_attributes(token, container, ("class", "id"))
        if name:
            # note, as per djot, the name is added to the end of the classes
            container["classes"].append(name)
        with self.current_node_context(container, append=True):
            self.nested_render_text(token.content, token_line(token, 0))

    def render_dl(self, token: SyntaxTreeNode) -> None:
        """Render a definition list."""
        node = nodes.definition_list(classes=["simple", "myst"])
        self.copy_attributes(token, node, ("class", "id"))
        self.add_line_and_source_path(node, token)
        make_terms = ("glossary" in node["classes"]) and (self.sphinx_env is not None)
        with self.current_node_context(node, append=True):
            item = None
            for child in token.children or []:
                if child.type == "dt":
                    item = nodes.definition_list_item()
                    self.add_line_and_source_path(item, child)
                    with self.current_node_context(item, append=True):
                        term = nodes.term(
                            child.children[0].content if child.children else ""
                        )
                        self.add_line_and_source_path(term, child)
                        with self.current_node_context(term):
                            self.render_children(child)
                        if make_terms:
                            from sphinx.domains.std import make_glossary_term

                            term = make_glossary_term(
                                self.sphinx_env,  # type: ignore[arg-type]
                                term.children,
                                None,
                                term.source,
                                term.line,
                                node_id=None,
                                document=self.document,
                            )
                        self.current_node.append(term)
                elif child.type == "dd":
                    if item is None:
                        error = self.reporter.error(
                            (
                                "Found a definition in a definition list, "
                                "with no preceding term"
                            ),
                            # nodes.literal_block(content, content),
                            line=token_line(child),
                        )
                        self.current_node += [error]
                    with self.current_node_context(item):
                        definition = nodes.definition()
                        self.add_line_and_source_path(definition, child)
                        with self.current_node_context(definition, append=True):
                            self.render_children(child)
                else:
                    error_msg = self.reporter.error(
                        (
                            "Expected a term/definition as a child of a definition list"
                            f", but found a: {child.type}"
                        ),
                        # nodes.literal_block(content, content),
                        line=token_line(child),
                    )
                    self.current_node += [error_msg]

    def render_field_list(self, token: SyntaxTreeNode) -> None:
        """Render a field list."""
        field_list = nodes.field_list(classes=["myst"])
        self.copy_attributes(token, field_list, ("class", "id"))
        self.add_line_and_source_path(field_list, token)
        with self.current_node_context(field_list, append=True):
            # raise ValueError(token.pretty(show_text=True))
            children = (token.children or [])[:]
            while children:
                child = children.pop(0)
                if child.type != "fieldlist_name":
                    error_msg = self.reporter.error(
                        (
                            "Expected a fieldlist_name as a child of a field_list"
                            f", but found a: {child.type}"
                        ),
                        # nodes.literal_block(content, content),
                        line=token_line(child),
                    )
                    self.current_node += [error_msg]
                    break
                field = nodes.field()
                self.add_line_and_source_path(field, child)
                field_list += field
                field_name = nodes.field_name()
                self.add_line_and_source_path(field_name, child)
                field += field_name
                with self.current_node_context(field_name):
                    self.render_children(child)
                field_body = nodes.field_body()
                self.add_line_and_source_path(field_name, child)
                field += field_body
                if children and children[0].type == "fieldlist_body":
                    child = children.pop(0)
                    with self.current_node_context(field_body):
                        self.render_children(child)

    def render_restructuredtext(self, token: SyntaxTreeNode) -> None:
        """Render the content of the token as restructuredtext."""
        # copy necessary elements (source, line no, env, reporter)
        newdoc = make_document()
        newdoc["source"] = self.document["source"]
        newdoc.settings = self.document.settings
        newdoc.reporter = self.reporter
        # pad the line numbers artificially so they offset with the fence block
        pseudosource = ("\n" * token_line(token)) + token.content
        # actually parse the rst into our document
        MockRSTParser().parse(pseudosource, newdoc)
        for node in newdoc:
            if node["names"]:
                self.document.note_explicit_target(node, node)
        self.current_node.extend(newdoc.children)

    def render_directive(
        self,
        token: SyntaxTreeNode,
        name: str,
        arguments: str,
        *,
        additional_options: dict[str, str] | None = None,
    ) -> None:
        """Render special fenced code blocks as directives.

        :param token: the token to render
        :param name: the name of the directive
        :param arguments: The remaining text on the same line as the directive name.
        """
        position = token_line(token)
        nodes_list = self.run_directive(
            name,
            arguments,
            token.content,
            position,
            additional_options=additional_options,
        )
        self.current_node += nodes_list

    def run_directive(
        self,
        name: str,
        first_line: str,
        content: str,
        position: int,
        additional_options: dict[str, str] | None = None,
    ) -> list[nodes.Element]:
        """Run a directive and return the generated nodes.

        :param name: the name of the directive
        :param first_line: The text on the same line as the directive name.
            May be an argument or body text, dependent on the directive
        :param content: All text after the first line. Can include options.
        :param position: The line number of the first line
        :param additional_options: Additional options to add to the directive,
            above those parsed from the content.

        """
        self.document.current_line = position

        # get directive class
        output: tuple[Directive | None, list[SystemMessage]] = directives.directive(
            name, self.language_module_rst, self.document
        )
        directive_class, messages = output
        if not directive_class:
            warn_node = self.create_warning(
                f"Unknown directive type: {name!r}",
                MystWarnings.UNKNOWN_DIRECTIVE,
                line=position,
            )
            return ([warn_node] if warn_node else []) + messages

        if issubclass(directive_class, Include):
            # this is a Markdown only option,
            # to allow for altering relative image reference links
            directive_class.option_spec["relative-images"] = directives.flag
            directive_class.option_spec["relative-docs"] = directives.path
            directive_class.option_spec["heading-offset"] = directives.nonnegative_int

        try:
            parsed = parse_directive_text(
                directive_class,
                first_line,
                content,
                line=position,
                additional_options=additional_options,
            )
        except MarkupError as error:
            error = self.reporter.error(
                f"Directive '{name}': {error}",
                line=position,
            )
            return [error]

        for _warning in parsed.warnings:
            self.create_warning(
                f"{name!r}: {_warning.msg}",
                _warning.type,
                line=_warning.lineno if _warning.lineno is not None else position,
                append_to=self.current_node,
            )

        # initialise directive
        if issubclass(directive_class, Include):
            directive_instance = MockIncludeDirective(
                self,
                name=name,
                klass=directive_class,
                arguments=parsed.arguments,
                options=parsed.options,
                body=parsed.body,
                lineno=position,
            )
        else:
            state_machine = MockStateMachine(self, position)
            state = MockState(self, state_machine, position)
            directive_instance = directive_class(
                name=name,
                # the list of positional arguments
                arguments=parsed.arguments,
                # a dictionary mapping option names to values
                options=parsed.options,
                # the directive content line by line
                content=StringList(parsed.body, self.document["source"]),
                # the absolute line number of the first line of the directive
                lineno=position,
                # the line offset of the first line of the content
                content_offset=parsed.body_offset,
                # a string containing the entire directive
                block_text="\n".join(parsed.body),
                state=state,
                state_machine=state_machine,
            )

        # run directive
        try:
            result = directive_instance.run()
        except DirectiveError as error:
            msg_node = self.reporter.system_message(
                error.level, error.msg, line=position
            )
            msg_node += nodes.literal_block(content, content)
            result = [msg_node]
        except MockingError as exc:
            error_msg = self.reporter.error(
                f"Directive '{name}' cannot be mocked: {exc.__class__.__name__}: {exc}",
                nodes.literal_block(content, content),
                line=position,
            )
            return [error_msg]

        assert isinstance(
            result, list
        ), f'Directive "{name}" must return a list of nodes.'
        for i in range(len(result)):
            assert isinstance(
                result[i], nodes.Node
            ), f'Directive "{name}" returned non-Node object (index {i}): {result[i]}'
        return result

    def render_substitution_inline(self, token: SyntaxTreeNode) -> None:
        """Render inline substitution {{key}}."""
        self.render_substitution(token, inline=True)

    def render_substitution_block(self, token: SyntaxTreeNode) -> None:
        """Render block substitution {{key}}."""
        self.render_substitution(token, inline=False)

    def render_substitution(self, token: SyntaxTreeNode, inline: bool) -> None:
        """Substitutions are rendered by:

        1. Combining global substitutions with front-matter substitutions
           to create a variable context (front-matter takes priority)
        2. Add the sphinx `env` to the variable context (if available)
        3. Create the string content with Jinja2 (passing it the variable context)
        4. If the substitution is inline and not a directive,
           parse to nodes ignoring block syntaxes (like lists or block-quotes),
           otherwise parse to nodes with all syntax rules.

        """
        position = token_line(token)

        # front-matter substitutions take priority over config ones
        variable_context: dict[str, Any] = {**self.md_config.substitutions}
        if self.sphinx_env is not None:
            variable_context["env"] = self.sphinx_env

        # fail on undefined variables
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)

        # try rendering
        try:
            rendered = env.from_string(f"{{{{{token.content}}}}}").render(
                variable_context
            )
        except Exception as error:
            self.create_warning(
                f"Substitution error:{error.__class__.__name__}: {error}",
                MystWarnings.SUBSTITUTION,
                line=position,
                append_to=self.current_node,
            )
            return

        # handle circular references
        ast = env.parse(f"{{{{{token.content}}}}}")
        references = {
            n.name for n in ast.find_all(jinja2.nodes.Name) if n.name != "env"
        }
        self.document.sub_references = getattr(self.document, "sub_references", set())
        cyclic = references.intersection(self.document.sub_references)
        if cyclic:
            self.create_warning(
                f"circular substitution reference: {cyclic}",
                MystWarnings.SUBSTITUTION,
                line=position,
                append_to=self.current_node,
            )
            return

        # TODO improve error reporting;
        # at present, for a multi-line substitution,
        # an error may point to a line lower than the substitution
        # should it point to the source of the substitution?
        # or the error message should at least indicate that its a substitution

        # we record used references before nested parsing, then remove them after
        self.document.sub_references.update(references)
        try:
            if inline and not REGEX_DIRECTIVE_START.match(rendered):
                self.nested_render_text(rendered, position, inline=True)
            else:
                self.nested_render_text(rendered, position)
        finally:
            self.document.sub_references.difference_update(references)


def html_meta_to_nodes(
    data: dict[str, Any], document: nodes.document, line: int, reporter: Reporter
) -> list[nodes.pending | nodes.system_message]:
    """Replicate the `meta` directive,
    by converting a dictionary to a list of pending meta nodes

    See:
    https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#html-metadata
    """
    if not data:
        return []

    output = []

    for key, value in data.items():
        content = str(value or "")
        meta_node = nodes.meta(content)
        meta_node.source = document["source"]
        meta_node.line = line
        meta_node["content"] = content
        try:
            if not content:
                raise ValueError("No content")
            for i, key_part in enumerate(key.split()):
                if "=" not in key_part and i == 0:
                    meta_node["name"] = key_part
                    continue
                if "=" not in key_part:
                    raise ValueError(f"no '=' in {key_part}")
                attr_name, attr_val = key_part.split("=", 1)
                if not (attr_name and attr_val):
                    raise ValueError(f"malformed {key_part}")
                meta_node[attr_name.lower()] = attr_val
        except ValueError as error:
            msg = reporter.error(f'Error parsing meta tag attribute "{key}": {error}.')
            output.append(msg)
            continue

        pending = nodes.pending(
            Filter,
            {"component": "writer", "format": "html", "nodes": [meta_node]},
        )
        document.note_pending(pending)
        output.append(pending)

    return output


def clean_astext(node: nodes.Element) -> str:
    """Like node.astext(), but ignore images.
    Copied from sphinx.
    """
    node = node.deepcopy()
    for img in findall(node)(nodes.image):
        img["alt"] = ""
    for raw in list(findall(node)(nodes.raw)):
        raw.parent.remove(raw)
    return node.astext()


_SLUGIFY_CLEAN_REGEX = re.compile(r"[^\w\u4e00-\u9fff\- ]")


def default_slugify(title: str) -> str:
    """Default slugify function.

    This aims to mimic the GitHub Markdown format, see:

    - https://github.com/jch/html-pipeline/blob/master/lib/html/pipeline/toc_filter.rb
    - https://gist.github.com/asabaylus/3071099
    """
    return _SLUGIFY_CLEAN_REGEX.sub("", title.lower().replace(" ", "-"))


def compute_unique_slug(
    token_tree: SyntaxTreeNode,
    slugs: Iterable[str],
    slug_func: None | Callable[[str], str] = None,
) -> str:
    """Compute the slug for a token.

    This directly mirrors the logic in `mdit_py_plugins.anchors_plugin`
    """
    slug_func = default_slugify if slug_func is None else slug_func
    tokens = token_tree.to_tokens()
    inline_token = tokens[1]
    title = "".join(
        child.content
        for child in (inline_token.children or [])
        if child.type in ["text", "code_inline"]
    )
    slug = slug_func(title)
    i = 1
    while slug in slugs:
        slug = f"{slug}-{i}"
        i += 1
    return slug

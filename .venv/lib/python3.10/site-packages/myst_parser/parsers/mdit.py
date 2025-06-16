"""This module holds the ``create_md_parser`` function,
which creates a parser from the config.
"""

from __future__ import annotations

from collections.abc import Callable

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
from mdit_py_plugins.amsmath import amsmath_plugin
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.colon_fence import colon_fence_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.field_list import fieldlist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.myst_blocks import myst_block_plugin
from mdit_py_plugins.myst_role import myst_role_plugin
from mdit_py_plugins.substitution import substitution_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.wordcount import wordcount_plugin

from myst_parser.config.main import MdParserConfig


def create_md_parser(
    config: MdParserConfig, renderer: Callable[[MarkdownIt], RendererProtocol]
) -> MarkdownIt:
    """Return a Markdown parser with the required MyST configuration."""

    # TODO warn if linkify required and linkify-it-py not installed
    # (currently the parse will unceremoniously except)

    if config.commonmark_only:
        # see https://spec.commonmark.org/
        md = MarkdownIt("commonmark", renderer_cls=renderer).use(
            wordcount_plugin, per_minute=config.words_per_minute
        )
        md.options.update({"myst_config": config})
        return md

    if config.gfm_only:
        # see https://github.github.com/gfm/
        md = (
            MarkdownIt("commonmark", renderer_cls=renderer)
            # note, strikethrough currently only supported tentatively for HTML
            .enable("strikethrough")
            .enable("table")
            .use(tasklists_plugin, enabled=config.enable_checkboxes)
            .enable("linkify")
            .use(wordcount_plugin, per_minute=config.words_per_minute)
        )
        md.options.update({"linkify": True, "myst_config": config})
        return md

    md = (
        MarkdownIt("commonmark", renderer_cls=renderer)
        .enable("table")
        .use(front_matter_plugin)
        .use(myst_block_plugin)
        .use(myst_role_plugin)
        .use(footnote_plugin, inline=False, move_to_end=False, always_match_refs=True)
        .use(wordcount_plugin, per_minute=config.words_per_minute)
    )

    typographer = False
    if "smartquotes" in config.enable_extensions:
        md.enable("smartquotes")
        typographer = True
    if "replacements" in config.enable_extensions:
        md.enable("replacements")
        typographer = True
    if "linkify" in config.enable_extensions:
        md.enable("linkify")
        if md.linkify is not None:
            md.linkify.set({"fuzzy_link": config.linkify_fuzzy_links})
    if "strikethrough" in config.enable_extensions:
        md.enable("strikethrough")
    if "dollarmath" in config.enable_extensions:
        md.use(
            dollarmath_plugin,
            allow_labels=config.dmath_allow_labels,
            allow_space=config.dmath_allow_space,
            allow_digits=config.dmath_allow_digits,
            double_inline=config.dmath_double_inline,
        )
    if "colon_fence" in config.enable_extensions:
        md.use(colon_fence_plugin)
    if "amsmath" in config.enable_extensions:
        md.use(amsmath_plugin)
    if "deflist" in config.enable_extensions:
        md.use(deflist_plugin)
    if "fieldlist" in config.enable_extensions:
        md.use(fieldlist_plugin)
    if "tasklist" in config.enable_extensions:
        md.use(tasklists_plugin, enabled=config.enable_checkboxes)
    if "substitution" in config.enable_extensions:
        md.use(substitution_plugin, *config.sub_delimiters)
    if "attrs_inline" in config.enable_extensions:
        md.use(
            attrs_plugin,
            after=("image", "code_inline", "link_close", "span_close"),
            spans=True,
            span_after="footnote_ref",
        )
    elif "attrs_image" in config.enable_extensions:
        # TODO deprecate
        md.use(attrs_plugin, after=("image",))
    if "attrs_block" in config.enable_extensions:
        md.use(attrs_block_plugin)
    for name in config.disable_syntax:
        md.disable(name, True)

    md.options.update(
        {
            "typographer": typographer,
            "linkify": "linkify" in config.enable_extensions,
            "myst_config": config,
        }
    )

    return md

import re
from typing import Callable, List, Optional, Set

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token


def anchors_plugin(
    md: MarkdownIt,
    min_level: int = 1,
    max_level: int = 2,
    slug_func: Optional[Callable[[str], str]] = None,
    permalink: bool = False,
    permalinkSymbol: str = "¶",
    permalinkBefore: bool = False,
    permalinkSpace: bool = True,
) -> None:
    """Plugin for adding header anchors, based on
    `markdown-it-anchor <https://github.com/valeriangalliat/markdown-it-anchor>`__

    .. code-block:: md

        # Title String

    renders as:

    .. code-block:: html

        <h1 id="title-string">Title String <a class="header-anchor" href="#title-string">¶</a></h1>

    :param min_level: minimum header level to apply anchors
    :param max_level: maximum header level to apply anchors
    :param slug_func: function to convert title text to id slug.
    :param permalink: Add a permalink next to the title
    :param permalinkSymbol: the symbol to show
    :param permalinkBefore: Add the permalink before the title, otherwise after
    :param permalinkSpace: Add a space between the permalink and the title

    Note, the default slug function aims to mimic the GitHub Markdown format, see:

    - https://github.com/jch/html-pipeline/blob/master/lib/html/pipeline/toc_filter.rb
    - https://gist.github.com/asabaylus/3071099

    """
    selected_levels = list(range(min_level, max_level + 1))
    md.core.ruler.push(
        "anchor",
        _make_anchors_func(
            selected_levels,
            slug_func or slugify,
            permalink,
            permalinkSymbol,
            permalinkBefore,
            permalinkSpace,
        ),
    )


def _make_anchors_func(
    selected_levels: List[int],
    slug_func: Callable[[str], str],
    permalink: bool,
    permalinkSymbol: str,
    permalinkBefore: bool,
    permalinkSpace: bool,
) -> Callable[[StateCore], None]:
    def _anchor_func(state: StateCore) -> None:
        slugs: Set[str] = set()
        for idx, token in enumerate(state.tokens):
            if token.type != "heading_open":
                continue
            level = int(token.tag[1])
            if level not in selected_levels:
                continue
            inline_token = state.tokens[idx + 1]
            assert inline_token.children is not None
            title = "".join(
                child.content
                for child in inline_token.children
                if child.type in ["text", "code_inline"]
            )
            slug = unique_slug(slug_func(title), slugs)
            token.attrSet("id", slug)

            if permalink:
                link_open = Token(
                    "link_open",
                    "a",
                    1,
                )
                link_open.attrSet("class", "header-anchor")
                link_open.attrSet("href", f"#{slug}")
                link_tokens = [
                    link_open,
                    Token("html_block", "", 0, content=permalinkSymbol),
                    Token("link_close", "a", -1),
                ]
                if permalinkBefore:
                    inline_token.children = (
                        link_tokens
                        + (
                            [Token("text", "", 0, content=" ")]
                            if permalinkSpace
                            else []
                        )
                        + inline_token.children
                    )
                else:
                    inline_token.children.extend(
                        ([Token("text", "", 0, content=" ")] if permalinkSpace else [])
                        + link_tokens
                    )

    return _anchor_func


def slugify(title: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff\- ]", "", title.strip().lower().replace(" ", "-"))


def unique_slug(slug: str, slugs: Set[str]) -> str:
    uniq = slug
    i = 1
    while uniq in slugs:
        uniq = f"{slug}-{i}"
        i += 1
    slugs.add(uniq)
    return uniq

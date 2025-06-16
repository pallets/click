# Process admonitions and pass to cb.

from __future__ import annotations

from contextlib import suppress
import re
from typing import TYPE_CHECKING, Callable, Sequence

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict


def _get_multiple_tags(params: str) -> tuple[list[str], str]:
    """Check for multiple tags when the title is double quoted."""
    re_tags = re.compile(r'^\s*(?P<tokens>[^"]+)\s+"(?P<title>.*)"\S*$')
    match = re_tags.match(params)
    if match:
        tags = match["tokens"].strip().split(" ")
        return [tag.lower() for tag in tags], match["title"]
    raise ValueError("No match found for parameters")


def _get_tag(_params: str) -> tuple[list[str], str]:
    """Separate the tag name from the admonition title."""
    params = _params.strip()
    if not params:
        return [""], ""

    with suppress(ValueError):
        return _get_multiple_tags(params)

    tag, *_title = params.split(" ")
    joined = " ".join(_title)

    title = ""
    if not joined:
        title = tag.title()
    elif joined != '""':  # Specifically check for no title
        title = joined
    return [tag.lower()], title


def _validate(params: str) -> bool:
    """Validate the presence of the tag name after the marker."""
    tag = params.strip().split(" ", 1)[-1] or ""
    return bool(tag)


MARKER_LEN = 3  # Regardless of extra characters, block indent stays the same
MARKERS = ("!!!", "???", "???+")
MARKER_CHARS = {_m[0] for _m in MARKERS}
MAX_MARKER_LEN = max(len(_m) for _m in MARKERS)


def _extra_classes(markup: str) -> list[str]:
    """Return the list of additional classes based on the markup."""
    if markup.startswith("?"):
        if markup.endswith("+"):
            return ["is-collapsible collapsible-open"]
        return ["is-collapsible collapsible-closed"]
    return []


def admonition(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    if is_code_block(state, startLine):
        return False

    start = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    # Check out the first character quickly, which should filter out most of non-containers
    if state.src[start] not in MARKER_CHARS:
        return False

    # Check out the rest of the marker string
    marker = ""
    marker_len = MAX_MARKER_LEN
    while marker_len > 0:
        marker_pos = start + marker_len
        markup = state.src[start:marker_pos]
        if markup in MARKERS:
            marker = markup
            break
        marker_len -= 1
    else:
        return False

    params = state.src[marker_pos:maximum]

    if not _validate(params):
        return False

    # Since start is found, we can report success here in validation mode
    if silent:
        return True

    old_parent = state.parentType
    old_line_max = state.lineMax
    old_indent = state.blkIndent

    blk_start = marker_pos
    while blk_start < maximum and state.src[blk_start] == " ":
        blk_start += 1

    state.parentType = "admonition"
    # Correct block indentation when extra marker characters are present
    marker_alignment_correction = MARKER_LEN - len(marker)
    state.blkIndent += blk_start - start + marker_alignment_correction

    was_empty = False

    # Search for the end of the block
    next_line = startLine
    while True:
        next_line += 1
        if next_line >= endLine:
            # unclosed block should be autoclosed by end of document.
            # also block seems to be autoclosed by end of parent
            break
        pos = state.bMarks[next_line] + state.tShift[next_line]
        maximum = state.eMarks[next_line]
        is_empty = state.sCount[next_line] < state.blkIndent

        # two consecutive empty lines autoclose the block
        if is_empty and was_empty:
            break
        was_empty = is_empty

        if pos < maximum and state.sCount[next_line] < state.blkIndent:
            # non-empty line with negative indent should stop the block:
            # - !!!
            #  test
            break

    # this will prevent lazy continuations from ever going past our end marker
    state.lineMax = next_line

    tags, title = _get_tag(params)
    tag = tags[0]

    token = state.push("admonition_open", "div", 1)
    token.markup = markup
    token.block = True
    token.attrs = {"class": " ".join(["admonition", *tags, *_extra_classes(markup)])}
    token.meta = {"tag": tag}
    token.content = title
    token.info = params
    token.map = [startLine, next_line]

    if title:
        title_markup = f"{markup} {tag}"
        token = state.push("admonition_title_open", "p", 1)
        token.markup = title_markup
        token.attrs = {"class": "admonition-title"}
        token.map = [startLine, startLine + 1]

        token = state.push("inline", "", 0)
        token.content = title
        token.map = [startLine, startLine + 1]
        token.children = []

        token = state.push("admonition_title_close", "p", -1)

    state.md.block.tokenize(state, startLine + 1, next_line)

    token = state.push("admonition_close", "div", -1)
    token.markup = markup
    token.block = True

    state.parentType = old_parent
    state.lineMax = old_line_max
    state.blkIndent = old_indent
    state.line = next_line

    return True


def admon_plugin(md: MarkdownIt, render: None | Callable[..., str] = None) -> None:
    """Plugin to use
    `python-markdown style admonitions
    <https://python-markdown.github.io/extensions/admonition>`_.

    .. code-block:: md

        !!! note
            *content*

    `And mkdocs-style collapsible blocks
    <https://squidfunk.github.io/mkdocs-material/reference/admonitions/#collapsible-blocks>`_.

    .. code-block:: md

        ???+ note
            *content*

    Note, this is ported from
    `markdown-it-admon
    <https://github.com/commenthol/markdown-it-admon>`_.
    """

    def renderDefault(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        _options: OptionsDict,
        env: EnvType,
    ) -> str:
        return self.renderToken(tokens, idx, _options, env)  # type: ignore[attr-defined,no-any-return]

    render = render or renderDefault

    md.add_render_rule("admonition_open", render)
    md.add_render_rule("admonition_close", render)
    md.add_render_rule("admonition_title_open", render)
    md.add_render_rule("admonition_title_close", render)

    md.block.ruler.before(
        "fence",
        "admonition",
        admonition,
        {"alt": ["paragraph", "reference", "blockquote", "list"]},
    )

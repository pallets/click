from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml, unescapeAll
from markdown_it.rules_block import StateBlock

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict


def colon_fence_plugin(md: MarkdownIt) -> None:
    """This plugin directly mimics regular fences, but with `:` colons.

    Example::

        :::name
        contained text
        :::

    """

    md.block.ruler.before(
        "fence",
        "colon_fence",
        _rule,
        {"alt": ["paragraph", "reference", "blockquote", "list", "footnote_def"]},
    )
    md.add_render_rule("colon_fence", _render)


def _rule(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    if is_code_block(state, startLine):
        return False

    haveEndMarker = False
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if pos + 3 > maximum:
        return False

    marker = state.src[pos]

    if marker != ":":
        return False

    # scan marker length
    mem = pos
    pos = _skipCharsStr(state, pos, marker)

    length = pos - mem

    if length < 3:
        return False

    markup = state.src[mem:pos]
    params = state.src[pos:maximum]

    # Since start is found, we can report success here in validation mode
    if silent:
        return True

    # search end of block
    nextLine = startLine

    while True:
        nextLine += 1
        if nextLine >= endLine:
            # unclosed block should be autoclosed by end of document.
            # also block seems to be autoclosed by end of parent
            break

        pos = mem = state.bMarks[nextLine] + state.tShift[nextLine]
        maximum = state.eMarks[nextLine]

        if pos < maximum and state.sCount[nextLine] < state.blkIndent:
            # non-empty line with negative indent should stop the list:
            # - ```
            #  test
            break

        if state.src[pos] != marker:
            continue

        if is_code_block(state, nextLine):
            continue

        pos = _skipCharsStr(state, pos, marker)

        # closing code fence must be at least as long as the opening one
        if pos - mem < length:
            continue

        # make sure tail has spaces only
        pos = state.skipSpaces(pos)

        if pos < maximum:
            continue

        haveEndMarker = True
        # found!
        break

    # If a fence has heading spaces, they should be removed from its inner block
    length = state.sCount[startLine]

    state.line = nextLine + (1 if haveEndMarker else 0)

    token = state.push("colon_fence", "code", 0)
    token.info = params
    token.content = state.getLines(startLine + 1, nextLine, length, True)
    token.markup = markup
    token.map = [startLine, state.line]

    return True


def _skipCharsStr(state: StateBlock, pos: int, ch: str) -> int:
    """Skip character string from given position."""
    # TODO this can be replaced with StateBlock.skipCharsStr in markdown-it-py 3.0.0
    while True:
        try:
            current = state.src[pos]
        except IndexError:
            break
        if current != ch:
            break
        pos += 1
    return pos


def _render(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    token = tokens[idx]
    info = unescapeAll(token.info).strip() if token.info else ""
    content = escapeHtml(token.content)
    block_name = ""

    if info:
        block_name = info.split()[0]

    return (
        "<pre><code"
        + (f' class="block-{block_name}" ' if block_name else "")
        + ">"
        + content
        + "</code></pre>\n"
    )

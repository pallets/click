from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Sequence

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.rules_block import StateBlock

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict


def myst_block_plugin(md: MarkdownIt) -> None:
    """Parse MyST targets (``(name)=``), blockquotes (``% comment``) and block breaks (``+++``)."""
    md.block.ruler.before(
        "blockquote",
        "myst_line_comment",
        line_comment,
        {"alt": ["paragraph", "reference", "blockquote", "list", "footnote_def"]},
    )
    md.block.ruler.before(
        "hr",
        "myst_block_break",
        block_break,
        {"alt": ["paragraph", "reference", "blockquote", "list", "footnote_def"]},
    )
    md.block.ruler.before(
        "hr",
        "myst_target",
        target,
        {"alt": ["paragraph", "reference", "blockquote", "list", "footnote_def"]},
    )
    md.add_render_rule("myst_target", render_myst_target)
    md.add_render_rule("myst_line_comment", render_myst_line_comment)


def line_comment(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    if is_code_block(state, startLine):
        return False

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.src[pos] != "%":
        return False

    if silent:
        return True

    token = state.push("myst_line_comment", "", 0)
    token.attrSet("class", "myst-line-comment")
    token.content = state.src[pos + 1 : maximum].rstrip()
    token.markup = "%"

    # search end of block while appending lines to `token.content`
    for nextLine in itertools.count(startLine + 1):
        if nextLine >= endLine:
            break
        pos = state.bMarks[nextLine] + state.tShift[nextLine]
        maximum = state.eMarks[nextLine]

        if state.src[pos] != "%":
            break
        token.content += "\n" + state.src[pos + 1 : maximum].rstrip()

    state.line = nextLine
    token.map = [startLine, nextLine]

    return True


def block_break(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    if is_code_block(state, startLine):
        return False

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    marker = state.src[pos]
    pos += 1

    # Check block marker
    if marker != "+":
        return False

    # markers can be mixed with spaces, but there should be at least 3 of them

    cnt = 1
    while pos < maximum:
        ch = state.src[pos]
        if ch != marker and ch not in ("\t", " "):
            break
        if ch == marker:
            cnt += 1
        pos += 1

    if cnt < 3:
        return False

    if silent:
        return True

    state.line = startLine + 1

    token = state.push("myst_block_break", "hr", 0)
    token.attrSet("class", "myst-block")
    token.content = state.src[pos:maximum].strip()
    token.map = [startLine, state.line]
    token.markup = marker * cnt

    return True


def target(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    if is_code_block(state, startLine):
        return False

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    text = state.src[pos:maximum].strip()
    if not text.startswith("("):
        return False
    if not text.endswith(")="):
        return False
    if not text[1:-2]:
        return False

    if silent:
        return True

    state.line = startLine + 1

    token = state.push("myst_target", "", 0)
    token.attrSet("class", "myst-target")
    token.content = text[1:-2]
    token.map = [startLine, state.line]

    return True


def render_myst_target(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    label = tokens[idx].content
    class_name = "myst-target"
    target = f'<a href="#{label}">({label})=</a>'
    return f'<div class="{class_name}">{target}</div>'


def render_myst_line_comment(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    # Strip leading whitespace from all lines
    content = "\n".join(line.lstrip() for line in tokens[idx].content.split("\n"))
    return f"<!-- {escapeHtml(content)} -->"

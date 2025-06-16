"""Process footnotes"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Sequence, TypedDict

from markdown_it import MarkdownIt
from markdown_it.helpers import parseLinkLabel
from markdown_it.rules_block import StateBlock
from markdown_it.rules_core import StateCore
from markdown_it.rules_inline import StateInline
from markdown_it.token import Token

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.utils import EnvType, OptionsDict


def footnote_plugin(
    md: MarkdownIt,
    *,
    inline: bool = True,
    move_to_end: bool = True,
    always_match_refs: bool = False,
) -> None:
    """Plugin ported from
    `markdown-it-footnote <https://github.com/markdown-it/markdown-it-footnote>`__.

    It is based on the
    `pandoc definition <http://johnmacfarlane.net/pandoc/README.html#footnotes>`__:

    .. code-block:: md

        Normal footnote:

        Here is a footnote reference,[^1] and another.[^longnote]

        [^1]: Here is the footnote.

        [^longnote]: Here's one with multiple blocks.

            Subsequent paragraphs are indented to show that they
        belong to the previous footnote.

    :param inline: If True, also parse inline footnotes (^[...]).
    :param move_to_end: If True, move footnote definitions to the end of the token stream.
    :param always_match_refs: If True, match references, even if the footnote is not defined.

    """
    md.block.ruler.before(
        "reference", "footnote_def", footnote_def, {"alt": ["paragraph", "reference"]}
    )
    _footnote_ref = partial(footnote_ref, always_match=always_match_refs)
    if inline:
        md.inline.ruler.after("image", "footnote_inline", footnote_inline)
        md.inline.ruler.after("footnote_inline", "footnote_ref", _footnote_ref)
    else:
        md.inline.ruler.after("image", "footnote_ref", _footnote_ref)
    if move_to_end:
        md.core.ruler.after("inline", "footnote_tail", footnote_tail)

    md.add_render_rule("footnote_ref", render_footnote_ref)
    md.add_render_rule("footnote_block_open", render_footnote_block_open)
    md.add_render_rule("footnote_block_close", render_footnote_block_close)
    md.add_render_rule("footnote_open", render_footnote_open)
    md.add_render_rule("footnote_close", render_footnote_close)
    md.add_render_rule("footnote_anchor", render_footnote_anchor)

    # helpers (only used in other rules, no tokens are attached to those)
    md.add_render_rule("footnote_caption", render_footnote_caption)
    md.add_render_rule("footnote_anchor_name", render_footnote_anchor_name)


class _RefData(TypedDict, total=False):
    # standard
    label: str
    count: int
    # inline
    content: str
    tokens: list[Token]


class _FootnoteData(TypedDict):
    refs: dict[str, int]
    """A mapping of all footnote labels (prefixed with ``:``) to their ID (-1 if not yet set)."""
    list: dict[int, _RefData]
    """A mapping of all footnote IDs to their data."""


def _data_from_env(env: EnvType) -> _FootnoteData:
    footnotes = env.setdefault("footnotes", {})
    footnotes.setdefault("refs", {})
    footnotes.setdefault("list", {})
    return footnotes  # type: ignore[no-any-return]


# ## RULES ##


def footnote_def(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    """Process footnote block definition"""

    if is_code_block(state, startLine):
        return False

    start = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    # line should be at least 5 chars - "[^x]:"
    if start + 4 > maximum:
        return False

    if state.src[start] != "[":
        return False
    if state.src[start + 1] != "^":
        return False

    pos = start + 2
    while pos < maximum:
        if state.src[pos] == " ":
            return False
        if state.src[pos] == "]":
            break
        pos += 1

    if pos == start + 2:  # no empty footnote labels
        return False
    pos += 1
    if pos >= maximum or state.src[pos] != ":":
        return False
    if silent:
        return True
    pos += 1

    label = state.src[start + 2 : pos - 2]
    footnote_data = _data_from_env(state.env)
    footnote_data["refs"][":" + label] = -1

    open_token = Token("footnote_reference_open", "", 1)
    open_token.meta = {"label": label}
    open_token.level = state.level
    state.level += 1
    state.tokens.append(open_token)

    oldBMark = state.bMarks[startLine]
    oldTShift = state.tShift[startLine]
    oldSCount = state.sCount[startLine]
    oldParentType = state.parentType

    posAfterColon = pos
    initial = offset = (
        state.sCount[startLine]
        + pos
        - (state.bMarks[startLine] + state.tShift[startLine])
    )

    while pos < maximum:
        ch = state.src[pos]

        if ch == "\t":
            offset += 4 - offset % 4
        elif ch == " ":
            offset += 1

        else:
            break

        pos += 1

    state.tShift[startLine] = pos - posAfterColon
    state.sCount[startLine] = offset - initial

    state.bMarks[startLine] = posAfterColon
    state.blkIndent += 4
    state.parentType = "footnote"

    if state.sCount[startLine] < state.blkIndent:
        state.sCount[startLine] += state.blkIndent

    state.md.block.tokenize(state, startLine, endLine)

    state.parentType = oldParentType
    state.blkIndent -= 4
    state.tShift[startLine] = oldTShift
    state.sCount[startLine] = oldSCount
    state.bMarks[startLine] = oldBMark

    open_token.map = [startLine, state.line]

    token = Token("footnote_reference_close", "", -1)
    state.level -= 1
    token.level = state.level
    state.tokens.append(token)

    return True


def footnote_inline(state: StateInline, silent: bool) -> bool:
    """Process inline footnotes (^[...])"""

    maximum = state.posMax
    start = state.pos

    if start + 2 >= maximum:
        return False
    if state.src[start] != "^":
        return False
    if state.src[start + 1] != "[":
        return False

    labelStart = start + 2
    labelEnd = parseLinkLabel(state, start + 1)

    # parser failed to find ']', so it's not a valid note
    if labelEnd < 0:
        return False

    # We found the end of the link, and know for a fact it's a valid link
    # so all that's left to do is to call tokenizer.
    #
    if not silent:
        refs = _data_from_env(state.env)["list"]
        footnoteId = len(refs)

        tokens: list[Token] = []
        state.md.inline.parse(
            state.src[labelStart:labelEnd], state.md, state.env, tokens
        )

        token = state.push("footnote_ref", "", 0)
        token.meta = {"id": footnoteId}

        refs[footnoteId] = {"content": state.src[labelStart:labelEnd], "tokens": tokens}

    state.pos = labelEnd + 1
    state.posMax = maximum
    return True


def footnote_ref(
    state: StateInline, silent: bool, *, always_match: bool = False
) -> bool:
    """Process footnote references ([^...])"""

    maximum = state.posMax
    start = state.pos

    # should be at least 4 chars - "[^x]"
    if start + 3 > maximum:
        return False

    footnote_data = _data_from_env(state.env)

    if not (always_match or footnote_data["refs"]):
        return False
    if state.src[start] != "[":
        return False
    if state.src[start + 1] != "^":
        return False

    pos = start + 2
    while pos < maximum:
        if state.src[pos] in (" ", "\n"):
            return False
        if state.src[pos] == "]":
            break
        pos += 1

    if pos == start + 2:  # no empty footnote labels
        return False
    if pos >= maximum:
        return False
    pos += 1

    label = state.src[start + 2 : pos - 1]
    if ((":" + label) not in footnote_data["refs"]) and not always_match:
        return False

    if not silent:
        if footnote_data["refs"].get(":" + label, -1) < 0:
            footnoteId = len(footnote_data["list"])
            footnote_data["list"][footnoteId] = {"label": label, "count": 0}
            footnote_data["refs"][":" + label] = footnoteId
        else:
            footnoteId = footnote_data["refs"][":" + label]

        footnoteSubId = footnote_data["list"][footnoteId]["count"]
        footnote_data["list"][footnoteId]["count"] += 1

        token = state.push("footnote_ref", "", 0)
        token.meta = {"id": footnoteId, "subId": footnoteSubId, "label": label}

    state.pos = pos
    state.posMax = maximum
    return True


def footnote_tail(state: StateCore) -> None:
    """Post-processing step, to move footnote tokens to end of the token stream.

    Also removes un-referenced tokens.
    """

    insideRef = False
    refTokens = {}

    if "footnotes" not in state.env:
        return

    current: list[Token] = []
    tok_filter = []
    for tok in state.tokens:
        if tok.type == "footnote_reference_open":
            insideRef = True
            current = []
            currentLabel = tok.meta["label"]
            tok_filter.append(False)
            continue

        if tok.type == "footnote_reference_close":
            insideRef = False
            # prepend ':' to avoid conflict with Object.prototype members
            refTokens[":" + currentLabel] = current
            tok_filter.append(False)
            continue

        if insideRef:
            current.append(tok)

        tok_filter.append(not insideRef)

    state.tokens = [t for t, f in zip(state.tokens, tok_filter) if f]

    footnote_data = _data_from_env(state.env)
    if not footnote_data["list"]:
        return

    token = Token("footnote_block_open", "", 1)
    state.tokens.append(token)

    for i, foot_note in footnote_data["list"].items():
        token = Token("footnote_open", "", 1)
        token.meta = {"id": i, "label": foot_note.get("label", None)}
        # TODO propagate line positions of original foot note
        # (but don't store in token.map, because this is used for scroll syncing)
        state.tokens.append(token)

        if "tokens" in foot_note:
            tokens = []

            token = Token("paragraph_open", "p", 1)
            token.block = True
            tokens.append(token)

            token = Token("inline", "", 0)
            token.children = foot_note["tokens"]
            token.content = foot_note["content"]
            tokens.append(token)

            token = Token("paragraph_close", "p", -1)
            token.block = True
            tokens.append(token)

        elif "label" in foot_note:
            tokens = refTokens.get(":" + foot_note["label"], [])

        state.tokens.extend(tokens)
        if state.tokens[len(state.tokens) - 1].type == "paragraph_close":
            lastParagraph: Token | None = state.tokens.pop()
        else:
            lastParagraph = None

        t = (
            foot_note["count"]
            if (("count" in foot_note) and (foot_note["count"] > 0))
            else 1
        )
        j = 0
        while j < t:
            token = Token("footnote_anchor", "", 0)
            token.meta = {"id": i, "subId": j, "label": foot_note.get("label", None)}
            state.tokens.append(token)
            j += 1

        if lastParagraph:
            state.tokens.append(lastParagraph)

        token = Token("footnote_close", "", -1)
        state.tokens.append(token)

    token = Token("footnote_block_close", "", -1)
    state.tokens.append(token)


########################################
# Renderer partials


def render_footnote_anchor_name(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    n = str(tokens[idx].meta["id"] + 1)
    prefix = ""

    doc_id = env.get("docId", None)
    if isinstance(doc_id, str):
        prefix = f"-{doc_id}-"

    return prefix + n


def render_footnote_caption(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    n = str(tokens[idx].meta["id"] + 1)

    if tokens[idx].meta.get("subId", -1) > 0:
        n += ":" + str(tokens[idx].meta["subId"])

    return "[" + n + "]"


def render_footnote_ref(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    ident: str = self.rules["footnote_anchor_name"](tokens, idx, options, env)  # type: ignore[attr-defined]
    caption: str = self.rules["footnote_caption"](tokens, idx, options, env)  # type: ignore[attr-defined]
    refid = ident

    if tokens[idx].meta.get("subId", -1) > 0:
        refid += ":" + str(tokens[idx].meta["subId"])

    return (
        '<sup class="footnote-ref"><a href="#fn'
        + ident
        + '" id="fnref'
        + refid
        + '">'
        + caption
        + "</a></sup>"
    )


def render_footnote_block_open(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    return (
        (
            '<hr class="footnotes-sep" />\n'
            if options.xhtmlOut
            else '<hr class="footnotes-sep">\n'
        )
        + '<section class="footnotes">\n'
        + '<ol class="footnotes-list">\n'
    )


def render_footnote_block_close(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    return "</ol>\n</section>\n"


def render_footnote_open(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    ident: str = self.rules["footnote_anchor_name"](tokens, idx, options, env)  # type: ignore[attr-defined]

    if tokens[idx].meta.get("subId", -1) > 0:
        ident += ":" + tokens[idx].meta["subId"]

    return '<li id="fn' + ident + '" class="footnote-item">'


def render_footnote_close(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    return "</li>\n"


def render_footnote_anchor(
    self: RendererProtocol,
    tokens: Sequence[Token],
    idx: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    ident: str = self.rules["footnote_anchor_name"](tokens, idx, options, env)  # type: ignore[attr-defined]

    if tokens[idx].meta["subId"] > 0:
        ident += ":" + str(tokens[idx].meta["subId"])

    # ↩ with escape code to prevent display as Apple Emoji on iOS
    return ' <a href="#fnref' + ident + '" class="footnote-backref">\u21a9\ufe0e</a>'

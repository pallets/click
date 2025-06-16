from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable, Sequence

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml, isWhiteSpace
from markdown_it.rules_block import StateBlock
from markdown_it.rules_inline import StateInline

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict


def dollarmath_plugin(
    md: MarkdownIt,
    *,
    allow_labels: bool = True,
    allow_space: bool = True,
    allow_digits: bool = True,
    allow_blank_lines: bool = True,
    double_inline: bool = False,
    label_normalizer: Callable[[str], str] | None = None,
    renderer: Callable[[str, dict[str, Any]], str] | None = None,
    label_renderer: Callable[[str], str] | None = None,
) -> None:
    """Plugin for parsing dollar enclosed math,
    e.g. inline: ``$a=1$``, block: ``$$b=2$$``

    This is an improved version of ``texmath``; it is more performant,
    and handles ``\\`` escaping properly and allows for more configuration.

    :param allow_labels: Capture math blocks with label suffix, e.g. ``$$a=1$$ (eq1)``
    :param allow_space: Parse inline math when there is space
        after/before the opening/closing ``$``, e.g. ``$ a $``
    :param allow_digits: Parse inline math when there is a digit
        before/after the opening/closing ``$``, e.g. ``1$`` or ``$2``.
        This is useful when also using currency.
    :param allow_blank_lines: Allow blank lines inside ``$$``. Note that blank lines are
        not allowed in LaTeX, executablebooks/markdown-it-dollarmath, or the Github or
        StackExchange markdown dialects. Hoever, they have special semantics if used
        within Sphinx `..math` admonitions, so are allowed for backwards-compatibility.
    :param double_inline: Search for double-dollar math within inline contexts
    :param label_normalizer: Function to normalize the label,
        by default replaces whitespace with `-`
    :param renderer: Function to render content: `(str, {"display_mode": bool}) -> str`,
        by default escapes HTML
    :param label_renderer: Function to render labels, by default creates anchor

    """
    if label_normalizer is None:
        label_normalizer = lambda label: re.sub(r"\s+", "-", label)  # noqa: E731

    md.inline.ruler.before(
        "escape",
        "math_inline",
        math_inline_dollar(allow_space, allow_digits, double_inline),
    )
    md.block.ruler.before(
        "fence",
        "math_block",
        math_block_dollar(allow_labels, label_normalizer, allow_blank_lines),
    )

    # TODO the current render rules are really just for testing
    # would be good to allow "proper" math rendering,
    # e.g. https://github.com/roniemartinez/latex2mathml

    _renderer = (
        (lambda content, _: escapeHtml(content)) if renderer is None else renderer
    )

    _label_renderer: Callable[[str], str]
    if label_renderer is None:
        _label_renderer = (  # noqa: E731
            lambda label: f'<a href="#{label}" class="mathlabel" title="Permalink to this equation">¶</a>'
        )
    else:
        _label_renderer = label_renderer

    def render_math_inline(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        content = _renderer(str(tokens[idx].content).strip(), {"display_mode": False})
        return f'<span class="math inline">{content}</span>'

    def render_math_inline_double(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        content = _renderer(str(tokens[idx].content).strip(), {"display_mode": True})
        return f'<div class="math inline">{content}</div>'

    def render_math_block(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        content = _renderer(str(tokens[idx].content).strip(), {"display_mode": True})
        return f'<div class="math block">\n{content}\n</div>\n'

    def render_math_block_label(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        content = _renderer(str(tokens[idx].content).strip(), {"display_mode": True})
        _id = tokens[idx].info
        label = _label_renderer(tokens[idx].info)
        return f'<div id="{_id}" class="math block">\n{label}\n{content}\n</div>\n'

    md.add_render_rule("math_inline", render_math_inline)
    md.add_render_rule("math_inline_double", render_math_inline_double)

    md.add_render_rule("math_block", render_math_block)
    md.add_render_rule("math_block_label", render_math_block_label)


def is_escaped(state: StateInline, back_pos: int, mod: int = 0) -> bool:
    """Test if dollar is escaped."""
    # count how many \ are before the current position
    backslashes = 0
    while back_pos >= 0:
        back_pos = back_pos - 1
        if state.src[back_pos] == "\\":
            backslashes += 1
        else:
            break

    if not backslashes:
        return False

    # if an odd number of \ then ignore
    if (backslashes % 2) != mod:
        return True

    return False


def math_inline_dollar(
    allow_space: bool = True, allow_digits: bool = True, allow_double: bool = False
) -> Callable[[StateInline, bool], bool]:
    """Generate inline dollar rule.

    :param allow_space: Parse inline math when there is space
        after/before the opening/closing ``$``, e.g. ``$ a $``
    :param allow_digits: Parse inline math when there is a digit
        before/after the opening/closing ``$``, e.g. ``1$`` or ``$2``.
        This is useful when also using currency.
    :param allow_double: Search for double-dollar math within inline contexts

    """

    def _math_inline_dollar(state: StateInline, silent: bool) -> bool:
        """Inline dollar rule.

        - Initial check:
            - check if first character is a $
            - check if the first character is escaped
            - check if the next character is a space (if not allow_space)
            - check if the next character is a digit (if not allow_digits)
        - Advance one, if allow_double
        - Find closing (advance one, if allow_double)
        - Check closing:
            - check if the previous character is a space (if not allow_space)
            - check if the next character is a digit (if not allow_digits)
        - Check empty content
        """

        # TODO options:
        # even/odd backslash escaping

        if state.src[state.pos] != "$":
            return False

        if not allow_space:
            # whitespace not allowed straight after opening $
            try:
                if isWhiteSpace(ord(state.src[state.pos + 1])):
                    return False
            except IndexError:
                return False

        if not allow_digits:
            # digit not allowed straight before opening $
            try:
                if state.src[state.pos - 1].isdigit():
                    return False
            except IndexError:
                pass

        if is_escaped(state, state.pos):
            return False

        try:
            is_double = allow_double and state.src[state.pos + 1] == "$"
        except IndexError:
            return False

        # find closing $
        pos = state.pos + 1 + (1 if is_double else 0)
        found_closing = False
        while not found_closing:
            try:
                end = state.src.index("$", pos)
            except ValueError:
                return False

            if is_escaped(state, end):
                pos = end + 1
                continue

            try:
                if is_double and state.src[end + 1] != "$":
                    pos = end + 1
                    continue
            except IndexError:
                return False

            if is_double:
                end += 1

            found_closing = True

        if not found_closing:
            return False

        if not allow_space:
            # whitespace not allowed straight before closing $
            try:
                if isWhiteSpace(ord(state.src[end - 1])):
                    return False
            except IndexError:
                return False

        if not allow_digits:
            # digit not allowed straight after closing $
            try:
                if state.src[end + 1].isdigit():
                    return False
            except IndexError:
                pass

        text = (
            state.src[state.pos + 2 : end - 1]
            if is_double
            else state.src[state.pos + 1 : end]
        )

        # ignore empty
        if not text:
            return False

        if not silent:
            token = state.push(
                "math_inline_double" if is_double else "math_inline", "math", 0
            )
            token.content = text
            token.markup = "$$" if is_double else "$"

        state.pos = end + 1

        return True

    return _math_inline_dollar


# reversed end of block dollar equation, with equation label
DOLLAR_EQNO_REV = re.compile(r"^\s*\)([^)$\r\n]+?)\(\s*\${2}")


def math_block_dollar(
    allow_labels: bool = True,
    label_normalizer: Callable[[str], str] | None = None,
    allow_blank_lines: bool = False,
) -> Callable[[StateBlock, int, int, bool], bool]:
    """Generate block dollar rule."""

    def _math_block_dollar(
        state: StateBlock, startLine: int, endLine: int, silent: bool
    ) -> bool:
        # TODO internal backslash escaping

        if is_code_block(state, startLine):
            return False

        haveEndMarker = False
        startPos = state.bMarks[startLine] + state.tShift[startLine]
        end = state.eMarks[startLine]

        if startPos + 2 > end:
            return False

        if state.src[startPos] != "$" or state.src[startPos + 1] != "$":
            return False

        # search for end of block
        nextLine = startLine
        label = None

        # search for end of block on same line
        lineText = state.src[startPos:end]
        if len(lineText.strip()) > 3:
            if lineText.strip().endswith("$$"):
                haveEndMarker = True
                end = end - 2 - (len(lineText) - len(lineText.strip()))
            elif allow_labels:
                # reverse the line and match
                eqnoMatch = DOLLAR_EQNO_REV.match(lineText[::-1])
                if eqnoMatch:
                    haveEndMarker = True
                    label = eqnoMatch.group(1)[::-1]
                    end = end - eqnoMatch.end()

        # search for end of block on subsequent line
        if not haveEndMarker:
            while True:
                nextLine += 1
                if nextLine >= endLine:
                    break

                start = state.bMarks[nextLine] + state.tShift[nextLine]
                end = state.eMarks[nextLine]

                lineText = state.src[start:end]

                if lineText.strip().endswith("$$"):
                    haveEndMarker = True
                    end = end - 2 - (len(lineText) - len(lineText.strip()))
                    break
                if lineText.strip() == "" and not allow_blank_lines:
                    break  # blank lines are not allowed within $$

                # reverse the line and match
                if allow_labels:
                    eqnoMatch = DOLLAR_EQNO_REV.match(lineText[::-1])
                    if eqnoMatch:
                        haveEndMarker = True
                        label = eqnoMatch.group(1)[::-1]
                        end = end - eqnoMatch.end()
                        break

        if not haveEndMarker:
            return False

        state.line = nextLine + (1 if haveEndMarker else 0)

        token = state.push("math_block_label" if label else "math_block", "math", 0)
        token.block = True
        token.content = state.src[startPos + 2 : end]
        token.markup = "$$"
        token.map = [startLine, state.line]
        if label:
            token.info = label if label_normalizer is None else label_normalizer(label)

        return True

    return _math_block_dollar

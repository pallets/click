"""An extension to capture amsmath latex environments."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable, Sequence

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.rules_block import StateBlock

from mdit_py_plugins.utils import is_code_block

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict

# Taken from amsmath version 2.1
# http://anorien.csc.warwick.ac.uk/mirrors/CTAN/macros/latex/required/amsmath/amsldoc.pdf
ENVIRONMENTS = [
    # 3.2 single equation with an automatically gen-erated number
    "equation",
    # 3.3 variation equation, used for equations that dont fit on a single line
    "multline",
    # 3.5 a group of consecutive equations when there is no alignment desired among them
    "gather",
    # 3.6 Used for two or more equations when vertical alignment is desired
    "align",
    # allows the horizontal space between equationsto be explicitly specified.
    "alignat",
    # stretches the space betweenthe equation columns to the maximum possible width
    "flalign",
    # 4.1 The pmatrix, bmatrix, Bmatrix, vmatrix and Vmatrix have (respectively)
    # (),[],{},||,and ‖‖ delimiters built in.
    "matrix",
    "pmatrix",
    "bmatrix",
    "Bmatrix",
    "vmatrix",
    "Vmatrix",
    # eqnarray is another math environment, it is not part of amsmath,
    # and note that it is better to use align or equation+split instead
    "eqnarray",
]
# other "non-top-level" environments:

# 3.4 the split environment is for single equations that are too long to fit on one line
# and hence must be split into multiple lines,
# it is intended for use only inside some other displayed equation structure,
# usually an equation, align, or gather environment

# 3.7 variants gathered, aligned,and alignedat are provided
# whose total width is the actual width of the contents;
# thus they can be used as a component in a containing expression

RE_OPEN = r"\\begin\{(" + "|".join(ENVIRONMENTS) + r")([\*]?)\}"


def amsmath_plugin(
    md: MarkdownIt, *, renderer: Callable[[str], str] | None = None
) -> None:
    """Parses TeX math equations, without any surrounding delimiters,
    only for top-level `amsmath <https://ctan.org/pkg/amsmath>`__ environments:

    .. code-block:: latex

        \\begin{gather*}
        a_1=b_1+c_1\\\\
        a_2=b_2+c_2-d_2+e_2
        \\end{gather*}

    :param renderer: Function to render content, by default escapes HTML

    """
    md.block.ruler.before(
        "blockquote",
        "amsmath",
        amsmath_block,
        {"alt": ["paragraph", "reference", "blockquote", "list", "footnote_def"]},
    )

    _renderer = (lambda content: escapeHtml(content)) if renderer is None else renderer

    def render_amsmath_block(
        self: RendererProtocol,
        tokens: Sequence[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        content = _renderer(str(tokens[idx].content))
        return f'<div class="math amsmath">\n{content}\n</div>\n'

    md.add_render_rule("amsmath", render_amsmath_block)


def amsmath_block(
    state: StateBlock, startLine: int, endLine: int, silent: bool
) -> bool:
    # note the code principally follows the logic in markdown_it/rules_block/fence.py,
    # except that:
    # (a) it allows for closing tag on same line as opening tag
    # (b) it does not allow for opening tag without closing tag (i.e. no auto-closing)

    if is_code_block(state, startLine):
        return False

    # does the first line contain the beginning of an amsmath environment
    first_start = state.bMarks[startLine] + state.tShift[startLine]
    first_end = state.eMarks[startLine]
    first_text = state.src[first_start:first_end]

    if not (match_open := re.match(RE_OPEN, first_text)):
        return False

    # construct the closing tag
    environment = match_open.group(1)
    numbered = match_open.group(2)
    closing = rf"\end{{{match_open.group(1)}{match_open.group(2)}}}"

    # start looking for the closing tag, including the current line
    nextLine = startLine - 1

    while True:
        nextLine += 1
        if nextLine >= endLine:
            # reached the end of the block without finding the closing tag
            return False

        next_start = state.bMarks[nextLine] + state.tShift[nextLine]
        next_end = state.eMarks[nextLine]
        if next_start < first_end and state.sCount[nextLine] < state.blkIndent:
            # non-empty line with negative indent should stop the list:
            # - \begin{align}
            #  test
            return False

        if state.src[next_start:next_end].rstrip().endswith(closing):
            # found the closing tag
            break

    state.line = nextLine + 1

    if not silent:
        token = state.push("amsmath", "math", 0)
        token.block = True
        token.content = state.getLines(
            startLine, state.line, state.sCount[startLine], False
        )
        token.meta = {"environment": environment, "numbered": numbered}
        token.map = [startLine, nextLine]

    return True

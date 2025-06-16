"""Field list plugin"""

from contextlib import contextmanager
from typing import Iterator, Optional, Tuple

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock

from mdit_py_plugins.utils import is_code_block


def fieldlist_plugin(md: MarkdownIt) -> None:
    """Field lists are mappings from field names to field bodies, based on the
    `reStructureText syntax
    <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#field-lists>`_.

    .. code-block:: md

        :name *markup*:
        :name1: body content
        :name2: paragraph 1

                paragraph 2
        :name3:
          paragraph 1

          paragraph 2

    A field name may consist of any characters except colons (":").
    Inline markup is parsed in field names.

    The field name is followed by whitespace and the field body.
    The field body may be empty or contain multiple body elements.

    Since the field marker may be quite long,
    the second and subsequent lines of the field body do not have to
    line up with the first line, but they must be indented relative to the
    field name marker, and they must line up with each other.
    """
    md.block.ruler.before(
        "paragraph",
        "fieldlist",
        _fieldlist_rule,
        {"alt": ["paragraph", "reference", "blockquote"]},
    )


def parseNameMarker(state: StateBlock, startLine: int) -> Tuple[int, str]:
    """Parse field name: `:name:`

    :returns: position after name marker, name text
    """
    start = state.bMarks[startLine] + state.tShift[startLine]
    pos = start
    maximum = state.eMarks[startLine]

    # marker should have at least 3 chars (colon + character + colon)
    if pos + 2 >= maximum:
        return -1, ""

    # first character should be ':'
    if state.src[pos] != ":":
        return -1, ""

    # scan name length
    name_length = 1
    found_close = False
    for ch in state.src[pos + 1 :]:
        if ch == "\n":
            break
        if ch == ":":
            # TODO backslash escapes
            found_close = True
            break
        name_length += 1

    if not found_close:
        return -1, ""

    # get name
    name_text = state.src[pos + 1 : pos + name_length]

    # name should contain at least one character
    if not name_text.strip():
        return -1, ""

    return pos + name_length + 1, name_text


@contextmanager
def set_parent_type(state: StateBlock, name: str) -> Iterator[None]:
    """Temporarily set parent type to `name`"""
    oldParentType = state.parentType
    state.parentType = name
    yield
    state.parentType = oldParentType


def _fieldlist_rule(
    state: StateBlock, startLine: int, endLine: int, silent: bool
) -> bool:
    # adapted from markdown_it/rules_block/list.py::list_block

    if is_code_block(state, startLine):
        return False

    posAfterName, name_text = parseNameMarker(state, startLine)
    if posAfterName < 0:
        return False

    # For validation mode we can terminate immediately
    if silent:
        return True

    # start field list
    token = state.push("field_list_open", "dl", 1)
    token.attrSet("class", "field-list")
    token.map = listLines = [startLine, 0]

    # iterate list items
    nextLine = startLine

    with set_parent_type(state, "fieldlist"):
        while nextLine < endLine:
            # create name tokens
            token = state.push("fieldlist_name_open", "dt", 1)
            token.map = [startLine, startLine]
            token = state.push("inline", "", 0)
            token.map = [startLine, startLine]
            token.content = name_text
            token.children = []
            token = state.push("fieldlist_name_close", "dt", -1)

            # set indent positions
            pos = posAfterName
            maximum: int = state.eMarks[nextLine]
            first_line_body_indent = (
                state.sCount[nextLine]
                + posAfterName
                - (state.bMarks[startLine] + state.tShift[startLine])
            )

            # find indent to start of body on first line
            while pos < maximum:
                ch = state.src[pos]

                if ch == "\t":
                    first_line_body_indent += (
                        4 - (first_line_body_indent + state.bsCount[nextLine]) % 4
                    )
                elif ch == " ":
                    first_line_body_indent += 1
                else:
                    break

                pos += 1

            contentStart = pos

            # to figure out the indent of the body,
            # we look at all non-empty, indented lines and find the minimum indent
            block_indent: Optional[int] = None
            _line = startLine + 1
            while _line < endLine:
                # if start_of_content < end_of_content, then non-empty line
                if (state.bMarks[_line] + state.tShift[_line]) < state.eMarks[_line]:
                    if state.tShift[_line] <= 0:
                        # the line has no indent, so it's the end of the field
                        break
                    block_indent = (
                        state.tShift[_line]
                        if block_indent is None
                        else min(block_indent, state.tShift[_line])
                    )

                _line += 1

            has_first_line = contentStart < maximum
            if block_indent is None:  # no body content
                if not has_first_line:  # noqa: SIM108
                    # no body or first line, so just use default
                    block_indent = 2
                else:
                    # only a first line, so use it's indent
                    block_indent = first_line_body_indent
            else:
                block_indent = min(block_indent, first_line_body_indent)

            # Run subparser on the field body
            token = state.push("fieldlist_body_open", "dd", 1)
            token.map = [startLine, startLine]

            with temp_state_changes(state, startLine):
                diff = 0
                if has_first_line and block_indent < first_line_body_indent:
                    # this is a hack to get the first line to render correctly
                    # we temporarily "shift" it to the left by the difference
                    # between the first line indent and the block indent
                    # and replace the "hole" left with space,
                    # so that src indexes still match
                    diff = first_line_body_indent - block_indent
                    state.src = (
                        state.src[: contentStart - diff]
                        + " " * diff
                        + state.src[contentStart:]
                    )

                state.tShift[startLine] = contentStart - diff - state.bMarks[startLine]
                state.sCount[startLine] = first_line_body_indent - diff
                state.blkIndent = block_indent

                state.md.block.tokenize(state, startLine, endLine)

            state.push("fieldlist_body_close", "dd", -1)

            nextLine = startLine = state.line
            token.map[1] = nextLine

            if nextLine >= endLine:
                break

            contentStart = state.bMarks[startLine]

            # Try to check if list is terminated or continued.
            if state.sCount[nextLine] < state.blkIndent:
                break

            if is_code_block(state, startLine):
                break

            # get next field item
            posAfterName, name_text = parseNameMarker(state, startLine)
            if posAfterName < 0:
                break

        # Finalize list
        token = state.push("field_list_close", "dl", -1)
        listLines[1] = nextLine
        state.line = nextLine

    return True


@contextmanager
def temp_state_changes(state: StateBlock, startLine: int) -> Iterator[None]:
    """Allow temporarily changing certain state attributes."""
    oldTShift = state.tShift[startLine]
    oldSCount = state.sCount[startLine]
    oldBlkIndent = state.blkIndent
    oldSrc = state.src
    yield
    state.blkIndent = oldBlkIndent
    state.tShift[startLine] = oldTShift
    state.sCount[startLine] = oldSCount
    state.src = oldSrc

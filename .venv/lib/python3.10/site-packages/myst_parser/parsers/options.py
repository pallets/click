"""Parser for directive options.

This is a highly restricted parser for YAML,
which only allows a subset of YAML to be used for directive options:

- Only block mappings are allowed at the top level
- Mapping keys are parsed as strings (plain or quoted)
- Mapping values are parsed as strings (plain, quoted, literal `|`, folded `>`)
- `#` Comments are allowed and blank lines

Adapted from:
https://github.com/yaml/pyyaml/commit/957ae4d495cf8fcb5475c6c2f1bce801096b68a5

For a good description of multi-line YAML strings, see:
https://stackoverflow.com/a/21699210/5033292
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import ClassVar, Final, Literal, cast


@dataclass
class Position:
    """Position of a character in a stream."""

    index: int
    line: int
    column: int


class StreamBuffer:
    """A buffer for a stream of characters."""

    def __init__(self, stream: str):
        self._buffer = stream + _CHARS_END
        self._index = 0
        self._line = 0
        self._column = 0

    @property
    def index(self) -> int:
        return self._index

    @property
    def line(self) -> int:
        return self._line

    @property
    def column(self) -> int:
        return self._column

    def peek(self, index: int = 0) -> str:
        return self._buffer[self._index + index]

    def prefix(self, length: int = 1) -> str:
        return self._buffer[self._index : self._index + length]

    def forward(self, length: int = 1) -> None:
        while length:
            ch = self._buffer[self._index]
            self._index += 1
            if ch in "\n\x85\u2028\u2029" or (
                ch == "\r" and self._buffer[self._index] != "\n"
            ):
                self._line += 1
                self._column = 0
            elif ch != "\ufeff":
                self._column += 1
            length -= 1

    def get_position(self) -> Position:
        return Position(self._index, self._line, self._column)


@dataclass
class Token:
    """A parsed token from a directive option stream."""

    id: ClassVar[str] = "<unknown>"
    start: Position
    end: Position


@dataclass
class KeyToken(Token):
    id: ClassVar[str] = "<key>"
    value: str
    style: Literal[None, "'", '"'] = None
    """The original style of the string."""


@dataclass
class ValueToken(Token):
    id: ClassVar[str] = "<value>"
    value: str
    style: Literal[None, "'", '"', "|", ">"] = None
    """The original style of the string."""


@dataclass
class ColonToken(Token):
    id: ClassVar[str] = "<colon>"


class TokenizeError(Exception):
    def __init__(
        self,
        problem: str,
        problem_mark: Position,
        context: str | None = None,
        context_mark: Position | None = None,
    ):
        """A YAML error with optional context.

        :param problem: The problem encountered
        :param problem_mark: The position of the problem
        :param context: The context of the error, e.g. the parent being scanned
        :param context_mark: The position of the context
        """
        self.context = context
        self.context_mark = context_mark
        self.problem = problem
        self.problem_mark = problem_mark

    def clone(self, line_offset: int, column_offset: int) -> TokenizeError:
        """Clone the error with the given line and column offsets."""
        return TokenizeError(
            self.problem,
            replace(
                self.problem_mark,
                line=self.problem_mark.line + line_offset,
                column=self.problem_mark.column + column_offset,
            ),
            self.context,
            None
            if self.context_mark is None
            else replace(
                self.context_mark,
                line=self.context_mark.line + line_offset,
                column=self.context_mark.column + column_offset,
            ),
        )

    def __str__(self) -> str:
        lines = []
        if self.context is not None:
            lines.append(self.context)
        if self.context_mark is not None and (
            self.context_mark.line != self.problem_mark.line
            or self.context_mark.column != self.problem_mark.column
        ):
            lines.append(
                f"at line {self.context_mark.line}, column {self.context_mark.column}"
            )
        if self.problem is not None:
            lines.append(self.problem)
        if self.problem_mark is not None:
            lines.append(
                f"at line {self.problem_mark.line}, column {self.problem_mark.column}"
            )
        return "\n".join(lines)


@dataclass
class State:
    has_comments: bool = False


def options_to_items(
    text: str, line_offset: int = 0, column_offset: int = 0
) -> tuple[list[tuple[str, str]], State]:
    """Parse a directive option block into (key, value) tuples.

    :param text: The directive option text.
    :param line_offset: The line offset to apply to the error positions.
    :param column_offset: The column offset to apply to the error positions.

    :raises: `TokenizeError`
    """
    output = []
    state = State()
    for key_token, value_token in _to_tokens(text, state, line_offset, column_offset):
        output.append(
            (key_token.value, value_token.value if value_token is not None else "")
        )
    return output, state


def _to_tokens(
    text: str, state: State, line_offset: int = 0, column_offset: int = 0
) -> Iterable[tuple[KeyToken, ValueToken | None]]:
    """Parse a directive option, and yield key/value token pairs.

    :param text: The directive option text.
    :param line_offset: The line offset to apply to the error positions.
    :param column_offset: The column offset to apply to the error positions.

    :raises: `TokenizeError`
    """
    key_token: KeyToken | None = None
    try:
        for token in _tokenize(text, state):
            if isinstance(token, KeyToken):
                if key_token is not None:
                    yield key_token, None
                key_token = token
            elif isinstance(token, ValueToken):
                if key_token is None:
                    raise TokenizeError("expected key before value", token.start)
                yield key_token, token
                key_token = None
        if key_token is not None:
            yield key_token, None
    except TokenizeError as exc:
        if line_offset or column_offset:
            raise exc.clone(line_offset, column_offset) from exc
        raise


def _tokenize(text: str, state: State) -> Iterable[Token]:
    """Yield tokens from a directive option stream."""
    stream = StreamBuffer(text)

    while True:
        _scan_to_next_token(stream, state)

        if stream.peek() == _CHARS_END:
            break

        if not stream.column == 0:
            raise TokenizeError(
                "expected key to start at column 0", stream.get_position()
            )

        # find key
        ch = stream.peek()
        if ch in ("'", '"'):
            yield _scan_flow_scalar(stream, cast(Literal['"', "'"], ch), is_key=True)
        else:
            yield _scan_plain_scalar(stream, state, is_key=True)

        _scan_to_next_token(stream, state)

        # check next char is colon + space
        if stream.peek() != ":":
            raise TokenizeError("expected ':' after key", stream.get_position())

        start_mark = stream.get_position()
        stream.forward()
        end_mark = stream.get_position()
        yield ColonToken(start_mark, end_mark)

        _scan_to_next_token(stream, state)

        # now find value
        ch = stream.peek()
        if stream.column == 0:
            pass
        elif ch in ("|", ">"):
            yield _scan_block_scalar(stream, cast(Literal["|", ">"], ch), state)
        elif ch in ("'", '"'):
            yield _scan_flow_scalar(stream, cast(Literal['"', "'"], ch), is_key=False)
        else:
            yield _scan_plain_scalar(stream, state, is_key=False)


def _scan_to_next_token(stream: StreamBuffer, state: State) -> None:
    """Skip spaces, line breaks and comments.

    The byte order mark is also stripped,
    if it's the first character in the stream.
    """
    if stream.index == 0 and stream.peek() == "\ufeff":
        stream.forward()
    found = False
    while not found:
        while stream.peek() == " ":
            stream.forward()
        if stream.peek() == "#":
            state.has_comments = True
            while stream.peek() not in _CHARS_END_NEWLINE:
                stream.forward()
        if not _scan_line_break(stream):
            found = True


def _scan_plain_scalar(
    stream: StreamBuffer, state: State, is_key: bool = False
) -> KeyToken | ValueToken:
    chunks = []
    start_mark = stream.get_position()
    end_mark = start_mark
    indent = 0 if is_key else 1
    spaces: list[str] = []
    while True:
        length = 0
        if stream.peek() == "#":
            state.has_comments = True
            break
        while True:
            ch = stream.peek(length)
            if ch in _CHARS_END_SPACE_TAB_NEWLINE or (
                is_key
                and ch == ":"
                and stream.peek(length + 1) in _CHARS_END_SPACE_TAB_NEWLINE
            ):
                break
            length += 1
        if length == 0:
            break
        chunks.extend(spaces)
        chunks.append(stream.prefix(length))
        stream.forward(length)
        end_mark = stream.get_position()
        spaces = _scan_plain_spaces(stream, allow_newline=(not is_key))
        if not spaces or stream.peek() == "#" or (stream.column < indent):
            if stream.peek() == "#":
                state.has_comments = True
            break

    return (
        KeyToken(start_mark, end_mark, "".join(chunks))
        if is_key
        else ValueToken(start_mark, end_mark, "".join(chunks))
    )


def _scan_plain_spaces(stream: StreamBuffer, allow_newline: bool = True) -> list[str]:
    chunks = []
    length = 0
    while stream.peek(length) == " ":
        length += 1
    whitespaces = stream.prefix(length)
    stream.forward(length)
    ch = stream.peek()
    if allow_newline and ch in _CHARS_NEWLINE:
        line_break = _scan_line_break(stream)
        breaks = []
        while stream.peek() in _CHARS_SPACE_NEWLINE:
            if stream.peek() == " ":
                stream.forward()
            else:
                breaks.append(_scan_line_break(stream))
        if line_break != "\n":
            chunks.append(line_break)
        elif not breaks:
            chunks.append(" ")
        chunks.extend(breaks)
    elif whitespaces:
        chunks.append(whitespaces)
    return chunks


def _scan_line_break(stream: StreamBuffer) -> str:
    # Transforms:
    #   '\r\n'      :   '\n'
    #   '\r'        :   '\n'
    #   '\n'        :   '\n'
    #   '\x85'      :   '\n'
    #   '\u2028'    :   '\u2028'
    #   '\u2029     :   '\u2029'
    #   default     :   ''
    ch = stream.peek()
    if ch in "\r\n\x85":
        if stream.prefix(2) == "\r\n":
            stream.forward(2)
        else:
            stream.forward()
        return "\n"
    elif ch in "\u2028\u2029":
        stream.forward()
        return ch
    return ""


def _scan_flow_scalar(
    stream: StreamBuffer, style: Literal["'", '"'], is_key: bool = False
) -> KeyToken | ValueToken:
    double = style == '"'
    chunks = []
    start_mark = stream.get_position()
    quote = stream.peek()
    stream.forward()
    chunks.extend(_scan_flow_scalar_non_spaces(stream, double, start_mark))
    while stream.peek() != quote:
        chunks.extend(_scan_flow_scalar_spaces(stream, start_mark))
        chunks.extend(_scan_flow_scalar_non_spaces(stream, double, start_mark))
    stream.forward()
    end_mark = stream.get_position()
    return (
        KeyToken(start_mark, end_mark, "".join(chunks), style)
        if is_key
        else ValueToken(start_mark, end_mark, "".join(chunks), style)
    )


def _scan_flow_scalar_non_spaces(
    stream: StreamBuffer, double: bool, start_mark: Position
) -> list[str]:
    chunks = []
    while True:
        length = 0
        while stream.peek(length) not in "'\"\\" + _CHARS_END_SPACE_TAB_NEWLINE:
            length += 1
        if length:
            chunks.append(stream.prefix(length))
            stream.forward(length)
        ch = stream.peek()
        if not double and ch == "'" and stream.peek(1) == "'":
            chunks.append("'")
            stream.forward(2)
        elif (double and ch == "'") or (not double and ch in '"\\'):
            chunks.append(ch)
            stream.forward()
        elif double and ch == "\\":
            stream.forward()
            ch = stream.peek()
            if ch in _ESCAPE_REPLACEMENTS:
                chunks.append(_ESCAPE_REPLACEMENTS[ch])
                stream.forward()
            elif ch in _ESCAPE_CODES:
                length = _ESCAPE_CODES[ch]
                stream.forward()
                for k in range(length):
                    if stream.peek(k) not in "0123456789ABCDEFabcdef":
                        raise TokenizeError(
                            f"expected escape sequence of {length} hexadecimal numbers, but found {stream.peek(k)!r}",
                            stream.get_position(),
                            "while scanning a double-quoted scalar",
                            start_mark,
                        )
                code = int(stream.prefix(length), 16)
                chunks.append(chr(code))
                stream.forward(length)
            elif ch in _CHARS_NEWLINE:
                _scan_line_break(stream)
                chunks.extend(_scan_flow_scalar_breaks(stream))
            else:
                raise TokenizeError(
                    f"found unknown escape character {ch!r}",
                    stream.get_position(),
                    "while scanning a double-quoted scalar",
                    start_mark,
                )
        else:
            return chunks


def _scan_flow_scalar_spaces(stream: StreamBuffer, start_mark: Position) -> list[str]:
    chunks = []
    length = 0
    while stream.peek(length) in " \t":
        length += 1
    whitespaces = stream.prefix(length)
    stream.forward(length)
    ch = stream.peek()
    if ch == _CHARS_END:
        raise TokenizeError(
            "found unexpected end of stream",
            stream.get_position(),
            "while scanning a quoted scalar",
            start_mark,
        )
    elif ch in _CHARS_NEWLINE:
        line_break = _scan_line_break(stream)
        breaks = _scan_flow_scalar_breaks(stream)
        if line_break != "\n":
            chunks.append(line_break)
        elif not breaks:
            chunks.append(" ")
        chunks.extend(breaks)
    else:
        chunks.append(whitespaces)
    return chunks


def _scan_flow_scalar_breaks(stream: StreamBuffer) -> list[str]:
    chunks = []
    while True:
        while stream.peek() in " \t":
            stream.forward()
        if stream.peek() in _CHARS_NEWLINE:
            chunks.append(_scan_line_break(stream))
        else:
            return chunks


def _scan_block_scalar(
    stream: StreamBuffer, style: Literal["|", ">"], state: State
) -> ValueToken:
    indent = 0
    folded = style == ">"
    chunks = []
    start_mark = stream.get_position()

    # Scan the header.
    stream.forward()
    chomping, increment = _scan_block_scalar_indicators(stream, start_mark)
    _scan_block_scalar_ignored_line(stream, start_mark, state)

    # Determine the indentation level and go to the first non-empty line.
    min_indent = indent + 1
    if min_indent < 1:
        min_indent = 1
    if increment is None:
        breaks, max_indent, end_mark = _scan_block_scalar_indentation(stream)
        indent = max(min_indent, max_indent)
    else:
        indent = min_indent + increment - 1
        breaks, end_mark = _scan_block_scalar_breaks(stream, indent)
    line_break = ""

    # Scan the inner part of the block scalar.
    while stream.column == indent and stream.peek() != _CHARS_END:
        chunks.extend(breaks)
        leading_non_space = stream.peek() not in " \t"
        length = 0
        while stream.peek(length) not in _CHARS_END_NEWLINE:
            length += 1
        chunks.append(stream.prefix(length))
        stream.forward(length)
        line_break = _scan_line_break(stream)
        breaks, end_mark = _scan_block_scalar_breaks(stream, indent)
        if stream.column == indent and stream.peek() != _CHARS_END:
            if (
                folded
                and line_break == "\n"
                and leading_non_space
                and stream.peek() not in " \t"
            ):
                if not breaks:
                    chunks.append(" ")
            else:
                chunks.append(line_break)
        else:
            break

    # Chomp the tail.
    if chomping is not False:
        chunks.append(line_break)
    if chomping is True:
        chunks.extend(breaks)

    # We are done.
    return ValueToken(start_mark, end_mark, "".join(chunks), style)


def _scan_block_scalar_indicators(
    stream: StreamBuffer, start_mark: Position
) -> tuple[bool | None, int | None]:
    chomping = None
    increment = None
    ch = stream.peek()
    if ch in "+-":
        chomping = ch == "+"
        stream.forward()
        ch = stream.peek()
        if ch in "0123456789":
            increment = int(ch)
            if increment == 0:
                raise TokenizeError(
                    "expected indentation indicator in the range 1-9, but found 0",
                    stream.get_position(),
                    "while scanning a block scalar",
                    start_mark,
                )
            stream.forward()
    elif ch in "0123456789":
        increment = int(ch)
        if increment == 0:
            raise TokenizeError(
                "expected indentation indicator in the range 1-9, but found 0",
                stream.get_position(),
                "while scanning a block scalar",
                start_mark,
            )
        stream.forward()
        ch = stream.peek()
        if ch in "+-":
            chomping = ch == "+"
            stream.forward()
    ch = stream.peek()
    if ch not in _CHARS_END_SPACE_NEWLINE:
        raise TokenizeError(
            f"expected chomping or indentation indicators, but found {ch!r}",
            stream.get_position(),
            "while scanning a block scalar",
            start_mark,
        )
    return chomping, increment


def _scan_block_scalar_ignored_line(
    stream: StreamBuffer, start_mark: Position, state: State
) -> None:
    while stream.peek() == " ":
        stream.forward()
    if stream.peek() == "#":
        state.has_comments = True
        while stream.peek() not in _CHARS_END_NEWLINE:
            stream.forward()
    ch = stream.peek()
    if ch not in _CHARS_END_NEWLINE:
        raise TokenizeError(
            f"expected a comment or a line break, but found {ch!r}",
            stream.get_position(),
            "while scanning a block scalar",
            start_mark,
        )
    _scan_line_break(stream)


def _scan_block_scalar_indentation(
    stream: StreamBuffer,
) -> tuple[list[str], int, Position]:
    chunks = []
    max_indent = 0
    end_mark = stream.get_position()
    while stream.peek() in _CHARS_SPACE_NEWLINE:
        if stream.peek() != " ":
            chunks.append(_scan_line_break(stream))
            end_mark = stream.get_position()
        else:
            stream.forward()
            if stream.column > max_indent:
                max_indent = stream.column
    return chunks, max_indent, end_mark


def _scan_block_scalar_breaks(
    stream: StreamBuffer, indent: int
) -> tuple[list[str], Position]:
    chunks = []
    end_mark = stream.get_position()
    while stream.column < indent and stream.peek() == " ":
        stream.forward()
    while stream.peek() in _CHARS_NEWLINE:
        chunks.append(_scan_line_break(stream))
        end_mark = stream.get_position()
        while stream.column < indent and stream.peek() == " ":
            stream.forward()
    return chunks, end_mark


_CHARS_END: Final[str] = "\0"
_CHARS_NEWLINE: Final[str] = "\r\n\x85\u2028\u2029"
_CHARS_END_NEWLINE: Final[str] = "\0\r\n\x85\u2028\u2029"
_CHARS_SPACE_NEWLINE: Final[str] = " \r\n\x85\u2028\u2029"
_CHARS_END_SPACE_NEWLINE: Final[str] = "\0 \r\n\x85\u2028\u2029"
_CHARS_END_SPACE_TAB_NEWLINE: Final[str] = "\0 \t\r\n\x85\u2028\u2029"

_ESCAPE_REPLACEMENTS: Final[dict[str, str]] = {
    "0": "\0",
    "a": "\x07",
    "b": "\x08",
    "t": "\x09",
    "\t": "\x09",
    "n": "\x0a",
    "v": "\x0b",
    "f": "\x0c",
    "r": "\x0d",
    "e": "\x1b",
    " ": "\x20",
    '"': '"',
    "\\": "\\",
    "/": "/",
    "N": "\x85",
    "_": "\xa0",
    "L": "\u2028",
    "P": "\u2029",
}

_ESCAPE_CODES: Final[dict[str, int]] = {
    "x": 2,
    "u": 4,
    "U": 8,
}

"""Parser for attributes::

    attributes { id = "foo", class = "bar baz",
                key1 = "val1", key2 = "val2" }

Adapted from:
https://github.com/jgm/djot/blob/fae7364b86bfce69bc6d5b5eede1f5196d845fd6/djot/attributes.lua#L1

syntax:

attributes <- '{' whitespace* attribute (whitespace attribute)* whitespace* '}'
attribute <- identifier | class | keyval
identifier <- '#' name
class <- '.' name
name <- (nonspace, nonpunctuation other than ':', '_', '-')+
keyval <- key '=' val
key <- (ASCII_ALPHANUM | ':' | '_' | '-')+
val <- bareval | quotedval
bareval <- (ASCII_ALPHANUM | ':' | '_' | '-')+
quotedval <- '"' ([^"] | '\"') '"'
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Callable


class State(Enum):
    START = 0
    SCANNING = 1
    SCANNING_ID = 2
    SCANNING_CLASS = 3
    SCANNING_KEY = 4
    SCANNING_VALUE = 5
    SCANNING_BARE_VALUE = 6
    SCANNING_QUOTED_VALUE = 7
    SCANNING_COMMENT = 8
    SCANNING_ESCAPED = 9
    DONE = 10


REGEX_SPACE = re.compile(r"\s")
REGEX_SPACE_PUNCTUATION = re.compile(r"[\s!\"#$%&'()*+,./;<=>?@[\]^`{|}~]")
REGEX_KEY_CHARACTERS = re.compile(r"[a-zA-Z\d_:-]")


class TokenState:
    def __init__(self) -> None:
        self._tokens: list[tuple[int, int, str]] = []
        self.start: int = 0

    def set_start(self, start: int) -> None:
        self.start = start

    def append(self, start: int, end: int, ttype: str) -> None:
        self._tokens.append((start, end, ttype))

    def compile(self, string: str) -> dict[str, str]:
        """compile the tokens into a dictionary"""
        attributes = {}
        classes = []
        idx = 0
        while idx < len(self._tokens):
            start, end, ttype = self._tokens[idx]
            if ttype == "id":
                attributes["id"] = string[start:end]
            elif ttype == "class":
                classes.append(string[start:end])
            elif ttype == "key":
                key = string[start:end]
                if idx + 1 < len(self._tokens):
                    start, end, ttype = self._tokens[idx + 1]
                    if ttype == "value":
                        if key == "class":
                            classes.append(string[start:end])
                        else:
                            attributes[key] = string[start:end]
                        idx += 1
            idx += 1
        if classes:
            attributes["class"] = " ".join(classes)
        return attributes

    def __str__(self) -> str:
        return str(self._tokens)

    def __repr__(self) -> str:
        return repr(self._tokens)


class ParseError(Exception):
    def __init__(self, msg: str, pos: int) -> None:
        self.pos = pos
        super().__init__(msg + f" at position {pos}")


def parse(string: str) -> tuple[int, dict[str, str]]:
    """Parse attributes from start of string.

    :returns: (length of parsed string, dict of attributes)
    """
    pos = 0
    state: State = State.START
    tokens = TokenState()
    while pos < len(string):
        state = HANDLERS[state](string[pos], pos, tokens)
        if state == State.DONE:
            return pos, tokens.compile(string)
        pos = pos + 1

    return pos, tokens.compile(string)


def handle_start(char: str, pos: int, tokens: TokenState) -> State:
    if char == "{":
        return State.SCANNING
    raise ParseError("Attributes must start with '{'", pos)


def handle_scanning(char: str, pos: int, tokens: TokenState) -> State:
    if char == " " or char == "\t" or char == "\n" or char == "\r":
        return State.SCANNING
    if char == "}":
        return State.DONE
    if char == "#":
        tokens.set_start(pos)
        return State.SCANNING_ID
    if char == "%":
        tokens.set_start(pos)
        return State.SCANNING_COMMENT
    if char == ".":
        tokens.set_start(pos)
        return State.SCANNING_CLASS
    if REGEX_KEY_CHARACTERS.fullmatch(char):
        tokens.set_start(pos)
        return State.SCANNING_KEY

    raise ParseError(f"Unexpected character whilst scanning: {char}", pos)


def handle_scanning_comment(char: str, pos: int, tokens: TokenState) -> State:
    if char == "%":
        return State.SCANNING

    return State.SCANNING_COMMENT


def handle_scanning_id(char: str, pos: int, tokens: TokenState) -> State:
    if not REGEX_SPACE_PUNCTUATION.fullmatch(char):
        return State.SCANNING_ID

    if char == "}":
        if (pos - 1) > tokens.start:
            tokens.append(tokens.start + 1, pos, "id")
        return State.DONE

    if REGEX_SPACE.fullmatch(char):
        if (pos - 1) > tokens.start:
            tokens.append(tokens.start + 1, pos, "id")
        return State.SCANNING

    raise ParseError(f"Unexpected character whilst scanning id: {char}", pos)


def handle_scanning_class(char: str, pos: int, tokens: TokenState) -> State:
    if not REGEX_SPACE_PUNCTUATION.fullmatch(char):
        return State.SCANNING_CLASS

    if char == "}":
        if (pos - 1) > tokens.start:
            tokens.append(tokens.start + 1, pos, "class")
        return State.DONE

    if REGEX_SPACE.fullmatch(char):
        if (pos - 1) > tokens.start:
            tokens.append(tokens.start + 1, pos, "class")
        return State.SCANNING

    raise ParseError(f"Unexpected character whilst scanning class: {char}", pos)


def handle_scanning_key(char: str, pos: int, tokens: TokenState) -> State:
    if char == "=":
        tokens.append(tokens.start, pos, "key")
        return State.SCANNING_VALUE

    if REGEX_KEY_CHARACTERS.fullmatch(char):
        return State.SCANNING_KEY

    raise ParseError(f"Unexpected character whilst scanning key: {char}", pos)


def handle_scanning_value(char: str, pos: int, tokens: TokenState) -> State:
    if char == '"':
        tokens.set_start(pos)
        return State.SCANNING_QUOTED_VALUE

    if REGEX_KEY_CHARACTERS.fullmatch(char):
        tokens.set_start(pos)
        return State.SCANNING_BARE_VALUE

    raise ParseError(f"Unexpected character whilst scanning value: {char}", pos)


def handle_scanning_bare_value(char: str, pos: int, tokens: TokenState) -> State:
    if REGEX_KEY_CHARACTERS.fullmatch(char):
        return State.SCANNING_BARE_VALUE

    if char == "}":
        tokens.append(tokens.start, pos, "value")
        return State.DONE

    if REGEX_SPACE.fullmatch(char):
        tokens.append(tokens.start, pos, "value")
        return State.SCANNING

    raise ParseError(f"Unexpected character whilst scanning bare value: {char}", pos)


def handle_scanning_escaped(char: str, pos: int, tokens: TokenState) -> State:
    return State.SCANNING_QUOTED_VALUE


def handle_scanning_quoted_value(char: str, pos: int, tokens: TokenState) -> State:
    if char == '"':
        tokens.append(tokens.start + 1, pos, "value")
        return State.SCANNING

    if char == "\\":
        return State.SCANNING_ESCAPED

    if char == "{" or char == "}":
        raise ParseError(
            f"Unexpected character whilst scanning quoted value: {char}", pos
        )

    if char == "\n":
        tokens.append(tokens.start + 1, pos, "value")
        return State.SCANNING_QUOTED_VALUE

    return State.SCANNING_QUOTED_VALUE


HANDLERS: dict[State, Callable[[str, int, TokenState], State]] = {
    State.START: handle_start,
    State.SCANNING: handle_scanning,
    State.SCANNING_COMMENT: handle_scanning_comment,
    State.SCANNING_ID: handle_scanning_id,
    State.SCANNING_CLASS: handle_scanning_class,
    State.SCANNING_KEY: handle_scanning_key,
    State.SCANNING_VALUE: handle_scanning_value,
    State.SCANNING_BARE_VALUE: handle_scanning_bare_value,
    State.SCANNING_QUOTED_VALUE: handle_scanning_quoted_value,
    State.SCANNING_ESCAPED: handle_scanning_escaped,
}

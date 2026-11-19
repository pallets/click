from __future__ import annotations

import collections.abc as cabc
import textwrap
from contextlib import contextmanager

from ._compat import term_len


class TextWrapper(textwrap.TextWrapper):
    """``textwrap.TextWrapper`` variant that measures widths by visible
    character count.

    ANSI escape sequences embedded in chunks or indents are excluded from the
    width budget. Without this, styled help text (a styled ``Usage:`` prefix,
    a colorized option name, ...) would be wrapped earlier than its visible
    length warrants.
    """

    def _wrap_chunks(self, chunks: list[str]) -> list[str]:
        """Wrap chunks counting widths in visible characters.

        Mirrors the algorithm of :meth:`textwrap.TextWrapper._wrap_chunks`
        with every width measurement routed through
        :func:`click._compat.term_len` instead of :func:`len`, so ANSI escape
        bytes in chunks or indents do not inflate the count. ``max_lines`` is
        not supported, because :func:`~click.formatting.wrap_text` never sets
        it.

        .. seealso::
            :class:`textwrap.TextWrapper` in the Python standard library documentation:
            https://docs.python.org/3/library/textwrap.html#textwrap.TextWrapper

            Reference implementation in CPython:
            https://github.com/python/cpython/blob/main/Lib/textwrap.py
        """
        lines: list[str] = []
        if self.width <= 0:
            raise ValueError(f"invalid width {self.width!r} (must be > 0)")

        chunks.reverse()

        while chunks:
            cur_line: list[str] = []
            cur_len = 0

            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            width = self.width - term_len(indent)

            if self.drop_whitespace and chunks[-1].strip() == "" and lines:
                del chunks[-1]

            while chunks:
                n = term_len(chunks[-1])

                if cur_len + n <= width:
                    cur_line.append(chunks.pop())
                    cur_len += n

                else:
                    break

            if chunks and term_len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)

            if self.drop_whitespace and cur_line and cur_line[-1].strip() == "":
                del cur_line[-1]

            if cur_line:
                lines.append(indent + "".join(cur_line))

        return lines

    @contextmanager
    def extra_indent(self, indent: str) -> cabc.Iterator[None]:
        old_initial_indent = self.initial_indent
        old_subsequent_indent = self.subsequent_indent
        self.initial_indent += indent
        self.subsequent_indent += indent

        try:
            yield
        finally:
            self.initial_indent = old_initial_indent
            self.subsequent_indent = old_subsequent_indent

    def indent_only(self, text: str) -> str:
        rv = []

        for idx, line in enumerate(text.splitlines()):
            indent = self.initial_indent

            if idx > 0:
                indent = self.subsequent_indent

            rv.append(f"{indent}{line}")

        return "\n".join(rv)

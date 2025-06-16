"""Builds task/todo lists out of markdown lists with items starting with [ ] or [x]"""

# Ported by Wolmar Nyberg Åkerström from https://github.com/revin/markdown-it-task-lists
# ISC License
# Copyright (c) 2016, Revin Guillen
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
from __future__ import annotations

import re
from uuid import uuid4

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

# Regex string to match a whitespace character, as specified in
# https://github.github.com/gfm/#whitespace-character
# (spec version 0.29-gfm (2019-04-06))
_GFM_WHITESPACE_RE = r"[ \t\n\v\f\r]"


def tasklists_plugin(
    md: MarkdownIt,
    enabled: bool = False,
    label: bool = False,
    label_after: bool = False,
) -> None:
    """Plugin for building task/todo lists out of markdown lists with items starting with [ ] or [x]
    .. Nothing else

    For example::
       - [ ] An item that needs doing
       - [x] An item that is complete

    The rendered HTML checkboxes are disabled; to change this, pass a truthy value into the enabled
    property of the plugin options.

    :param enabled: True enables the rendered checkboxes
    :param label: True wraps the rendered list items in a <label> element for UX purposes,
    :param label_after: True adds the <label> element after the checkbox.
    """
    disable_checkboxes = not enabled
    use_label_wrapper = label
    use_label_after = label_after

    def fcn(state: StateCore) -> None:
        tokens = state.tokens
        for i in range(2, len(tokens) - 1):
            if is_todo_item(tokens, i):
                todoify(tokens[i])
                tokens[i - 2].attrSet(
                    "class",
                    "task-list-item" + (" enabled" if not disable_checkboxes else ""),
                )
                tokens[parent_token(tokens, i - 2)].attrSet(
                    "class", "contains-task-list"
                )

    md.core.ruler.after("inline", "github-tasklists", fcn)

    def parent_token(tokens: list[Token], index: int) -> int:
        target_level = tokens[index].level - 1
        for i in range(1, index + 1):
            if tokens[index - i].level == target_level:
                return index - i
        return -1

    def is_todo_item(tokens: list[Token], index: int) -> bool:
        return (
            is_inline(tokens[index])
            and is_paragraph(tokens[index - 1])
            and is_list_item(tokens[index - 2])
            and starts_with_todo_markdown(tokens[index])
        )

    def todoify(token: Token) -> None:
        assert token.children is not None
        token.children.insert(0, make_checkbox(token))
        token.children[1].content = token.children[1].content[3:]
        token.content = token.content[3:]

        if use_label_wrapper:
            if use_label_after:
                token.children.pop()

                # Replaced number generator from original plugin with uuid.
                checklist_id = f"task-item-{uuid4()}"
                token.children[0].content = (
                    token.children[0].content[0:-1] + f' id="{checklist_id}">'
                )
                token.children.append(after_label(token.content, checklist_id))
            else:
                token.children.insert(0, begin_label())
                token.children.append(end_label())

    def make_checkbox(token: Token) -> Token:
        checkbox = Token("html_inline", "", 0)
        disabled_attr = 'disabled="disabled"' if disable_checkboxes else ""
        if token.content.startswith("[ ] "):
            checkbox.content = (
                '<input class="task-list-item-checkbox" '
                f'{disabled_attr} type="checkbox">'
            )
        elif token.content.startswith("[x] ") or token.content.startswith("[X] "):
            checkbox.content = (
                '<input class="task-list-item-checkbox" checked="checked" '
                f'{disabled_attr} type="checkbox">'
            )
        return checkbox

    def begin_label() -> Token:
        token = Token("html_inline", "", 0)
        token.content = "<label>"
        return token

    def end_label() -> Token:
        token = Token("html_inline", "", 0)
        token.content = "</label>"
        return token

    def after_label(content: str, checkbox_id: str) -> Token:
        token = Token("html_inline", "", 0)
        token.content = (
            f'<label class="task-list-item-label" for="{checkbox_id}">{content}</label>'
        )
        token.attrs = {"for": checkbox_id}
        return token

    def is_inline(token: Token) -> bool:
        return token.type == "inline"

    def is_paragraph(token: Token) -> bool:
        return token.type == "paragraph_open"

    def is_list_item(token: Token) -> bool:
        return token.type == "list_item_open"

    def starts_with_todo_markdown(token: Token) -> bool:
        # leading whitespace in a list item is already trimmed off by markdown-it
        return re.match(rf"\[[ xX]]{_GFM_WHITESPACE_RE}+", token.content) is not None

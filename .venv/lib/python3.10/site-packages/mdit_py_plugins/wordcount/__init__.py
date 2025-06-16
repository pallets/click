import string
from typing import Callable, List

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore


def basic_count(text: str) -> int:
    """Split the string and ignore punctuation only elements."""
    return sum([el.strip(string.punctuation).isalpha() for el in text.split()])


def wordcount_plugin(
    md: MarkdownIt,
    *,
    per_minute: int = 200,
    count_func: Callable[[str], int] = basic_count,
    store_text: bool = False,
) -> None:
    """Plugin for computing and storing the word count.

    Stores in the ``env`` e.g.::

        env["wordcount"] = {
          "words": 200
          "minutes": 1,
        }

    If "wordcount" is already in the env, it will update it.

    :param per_minute: Words per minute reading speed
    :param store_text: store all text under a "text" key, as a list of strings
    """

    def _word_count_rule(state: StateCore) -> None:
        text: List[str] = []
        words = 0
        for token in state.tokens:
            if token.type == "text":
                words += count_func(token.content)
                if store_text:
                    text.append(token.content)
            elif token.type == "inline":
                for child in token.children or ():
                    if child.type == "text":
                        words += count_func(child.content)
                        if store_text:
                            text.append(child.content)

        data = state.env.setdefault("wordcount", {})
        if store_text:
            data.setdefault("text", [])
            data["text"] += text
        data.setdefault("words", 0)
        data["words"] += words
        data["minutes"] = int(round(data["words"] / per_minute))

    md.core.ruler.push("wordcount", _word_count_rule)

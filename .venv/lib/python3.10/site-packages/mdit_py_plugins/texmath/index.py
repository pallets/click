from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable, Match, Sequence, TypedDict

from markdown_it import MarkdownIt
from markdown_it.common.utils import charCodeAt

if TYPE_CHECKING:
    from markdown_it.renderer import RendererProtocol
    from markdown_it.rules_block import StateBlock
    from markdown_it.rules_inline import StateInline
    from markdown_it.token import Token
    from markdown_it.utils import EnvType, OptionsDict


def texmath_plugin(
    md: MarkdownIt, delimiters: str = "dollars", macros: Any = None
) -> None:
    """Plugin ported from
    `markdown-it-texmath <https://github.com/goessner/markdown-it-texmath>`__.

    It parses TeX math equations set inside opening and closing delimiters:

    .. code-block:: md

        $\\alpha = \\frac{1}{2}$

    :param delimiters: one of: brackets, dollars, gitlab, julia, kramdown

    """
    macros = macros or {}

    if delimiters in rules:
        for rule_inline in rules[delimiters]["inline"]:
            md.inline.ruler.before(
                "escape", rule_inline["name"], make_inline_func(rule_inline)
            )

            def render_math_inline(
                self: RendererProtocol,
                tokens: Sequence[Token],
                idx: int,
                options: OptionsDict,
                env: EnvType,
            ) -> str:
                return rule_inline["tmpl"].format(  # noqa: B023
                    render(tokens[idx].content, False, macros)
                )

            md.add_render_rule(rule_inline["name"], render_math_inline)

        for rule_block in rules[delimiters]["block"]:
            md.block.ruler.before(
                "fence", rule_block["name"], make_block_func(rule_block)
            )

            def render_math_block(
                self: RendererProtocol,
                tokens: Sequence[Token],
                idx: int,
                options: OptionsDict,
                env: EnvType,
            ) -> str:
                return rule_block["tmpl"].format(  # noqa: B023
                    render(tokens[idx].content, True, macros), tokens[idx].info
                )

            md.add_render_rule(rule_block["name"], render_math_block)


class _RuleDictReqType(TypedDict):
    name: str
    rex: re.Pattern[str]
    tmpl: str
    tag: str


class RuleDictType(_RuleDictReqType, total=False):
    # Note in Python 3.10+ could use Req annotation
    pre: Any
    post: Any


def applyRule(
    rule: RuleDictType, string: str, begin: int, inBlockquote: bool
) -> None | Match[str]:
    if not (
        string.startswith(rule["tag"], begin)
        and (rule["pre"](string, begin) if "pre" in rule else True)
    ):
        return None

    match = rule["rex"].match(string[begin:])

    if not match or match.start() != 0:
        return None

    lastIndex = match.end() + begin - 1
    if "post" in rule and not (
        rule["post"](string, lastIndex)  # valid post-condition
        # remove evil blockquote bug (https:#github.com/goessner/mdmath/issues/50)
        and (not inBlockquote or "\n" not in match.group(1))
    ):
        return None
    return match


def make_inline_func(rule: RuleDictType) -> Callable[[StateInline, bool], bool]:
    def _func(state: StateInline, silent: bool) -> bool:
        res = applyRule(rule, state.src, state.pos, False)
        if res:
            if not silent:
                token = state.push(rule["name"], "math", 0)
                token.content = res[1]  # group 1 from regex ..
                token.markup = rule["tag"]

            state.pos += res.end()

        return bool(res)

    return _func


def make_block_func(rule: RuleDictType) -> Callable[[StateBlock, int, int, bool], bool]:
    def _func(state: StateBlock, begLine: int, endLine: int, silent: bool) -> bool:
        begin = state.bMarks[begLine] + state.tShift[begLine]
        res = applyRule(rule, state.src, begin, state.parentType == "blockquote")
        if res:
            if not silent:
                token = state.push(rule["name"], "math", 0)
                token.block = True
                token.content = res[1]
                token.info = res[len(res.groups())]
                token.markup = rule["tag"]

            line = begLine
            endpos = begin + res.end() - 1

            while line < endLine:
                if endpos >= state.bMarks[line] and endpos <= state.eMarks[line]:
                    # line for end of block math found ...
                    state.line = line + 1
                    break
                line += 1

        return bool(res)

    return _func


def dollar_pre(src: str, beg: int) -> bool:
    prv = charCodeAt(src[beg - 1], 0) if beg > 0 else False
    return (
        (not prv) or prv != 0x5C and (prv < 0x30 or prv > 0x39)  # no backslash,
    )  # no decimal digit .. before opening '$'


def dollar_post(src: str, end: int) -> bool:
    try:
        nxt = src[end + 1] and charCodeAt(src[end + 1], 0)
    except IndexError:
        return True
    return (
        (not nxt) or (nxt < 0x30) or (nxt > 0x39)
    )  # no decimal digit .. after closing '$'


def render(tex: str, displayMode: bool, macros: Any) -> str:
    return tex
    # TODO better HTML renderer port for math
    # try:
    #     res = katex.renderToString(tex,{throwOnError:False,displayMode,macros})
    # except:
    #     res = tex+": "+err.message.replace("<","&lt;")
    # return res


# def use(katex):  # math renderer used ...
#     texmath.katex = katex;       # ... katex solely at current ...
#     return texmath;
# }


# All regexes areg global (g) and sticky (y), see:
# https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/sticky


rules: dict[str, dict[str, list[RuleDictType]]] = {
    "brackets": {
        "inline": [
            {
                "name": "math_inline",
                "rex": re.compile(r"^\\\((.+?)\\\)", re.DOTALL),
                "tmpl": "<eq>{0}</eq>",
                "tag": "\\(",
            }
        ],
        "block": [
            {
                "name": "math_block_eqno",
                "rex": re.compile(
                    r"^\\\[(((?!\\\]|\\\[)[\s\S])+?)\\\]\s*?\(([^)$\r\n]+?)\)", re.M
                ),
                "tmpl": '<section class="eqno"><eqn>{0}</eqn><span>({1})</span></section>',
                "tag": "\\[",
            },
            {
                "name": "math_block",
                "rex": re.compile(r"^\\\[([\s\S]+?)\\\]", re.M),
                "tmpl": "<section>\n<eqn>{0}</eqn>\n</section>\n",
                "tag": "\\[",
            },
        ],
    },
    "gitlab": {
        "inline": [
            {
                "name": "math_inline",
                "rex": re.compile(r"^\$`(.+?)`\$"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$`",
            }
        ],
        "block": [
            {
                "name": "math_block_eqno",
                "rex": re.compile(
                    r"^`{3}math\s+?([^`]+?)\s+?`{3}\s*?\(([^)$\r\n]+?)\)", re.M
                ),
                "tmpl": '<section class="eqno">\n<eqn>{0}</eqn><span>({1})</span>\n</section>\n',
                "tag": "```math",
            },
            {
                "name": "math_block",
                "rex": re.compile(r"^`{3}math\s+?([^`]+?)\s+?`{3}", re.M),
                "tmpl": "<section>\n<eqn>{0}</eqn>\n</section>\n",
                "tag": "```math",
            },
        ],
    },
    "julia": {
        "inline": [
            {
                "name": "math_inline",
                "rex": re.compile(r"^`{2}([^`]+?)`{2}"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "``",
            },
            {
                "name": "math_inline",
                "rex": re.compile(r"^\$(\S[^$\r\n]*?[^\s\\]{1}?)\$"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$",
                "pre": dollar_pre,
                "post": dollar_post,
            },
            {
                "name": "math_single",
                "rex": re.compile(r"^\$([^$\s\\]{1}?)\$"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$",
                "pre": dollar_pre,
                "post": dollar_post,
            },
        ],
        "block": [
            {
                "name": "math_block_eqno",
                "rex": re.compile(
                    r"^`{3}math\s+?([^`]+?)\s+?`{3}\s*?\(([^)$\r\n]+?)\)", re.M
                ),
                "tmpl": '<section class="eqno"><eqn>{0}</eqn><span>({1})</span></section>',
                "tag": "```math",
            },
            {
                "name": "math_block",
                "rex": re.compile(r"^`{3}math\s+?([^`]+?)\s+?`{3}", re.M),
                "tmpl": "<section><eqn>{0}</eqn></section>",
                "tag": "```math",
            },
        ],
    },
    "kramdown": {
        "inline": [
            {
                "name": "math_inline",
                "rex": re.compile(r"^\${2}([^$\r\n]*?)\${2}"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$$",
            }
        ],
        "block": [
            {
                "name": "math_block_eqno",
                "rex": re.compile(r"^\${2}([^$]*?)\${2}\s*?\(([^)$\r\n]+?)\)", re.M),
                "tmpl": '<section class="eqno"><eqn>{0}</eqn><span>({1})</span></section>',
                "tag": "$$",
            },
            {
                "name": "math_block",
                "rex": re.compile(r"^\${2}([^$]*?)\${2}", re.M),
                "tmpl": "<section><eqn>{0}</eqn></section>",
                "tag": "$$",
            },
        ],
    },
    "dollars": {
        "inline": [
            {
                "name": "math_inline",
                "rex": re.compile(r"^\$(\S[^$]*?[^\s\\]{1}?)\$"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$",
                "pre": dollar_pre,
                "post": dollar_post,
            },
            {
                "name": "math_single",
                "rex": re.compile(r"^\$([^$\s\\]{1}?)\$"),
                "tmpl": "<eq>{0}</eq>",
                "tag": "$",
                "pre": dollar_pre,
                "post": dollar_post,
            },
        ],
        "block": [
            {
                "name": "math_block_eqno",
                "rex": re.compile(r"^\${2}([^$]*?)\${2}\s*?\(([^)$\r\n]+?)\)", re.M),
                "tmpl": '<section class="eqno">\n<eqn>{0}</eqn><span>({1})</span>\n</section>\n',
                "tag": "$$",
            },
            {
                "name": "math_block",
                "rex": re.compile(r"^\${2}([^$]*?)\${2}", re.M),
                "tmpl": "<section>\n<eqn>{0}</eqn>\n</section>\n",
                "tag": "$$",
            },
        ],
    },
}

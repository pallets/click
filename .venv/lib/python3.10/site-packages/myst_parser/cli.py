import argparse
import sys

from markdown_it.renderer import RendererHTML
from markdown_it.rules_core import StateCore
from mdit_py_plugins.anchors import anchors_plugin

from myst_parser.config.main import MdParserConfig
from myst_parser.parsers.mdit import create_md_parser


def print_anchors(args=None):
    """ """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "input",
        nargs="?",
        type=argparse.FileType("r", encoding="utf8"),
        default=sys.stdin,
        help="Input file (default stdin)",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w", encoding="utf8"),
        default=sys.stdout,
        help="Output file (default stdout)",
    )
    arg_parser.add_argument(
        "-l", "--level", type=int, default=2, help="Maximum heading level."
    )
    args = arg_parser.parse_args(args)
    parser = create_md_parser(MdParserConfig(), RendererHTML)
    parser.use(anchors_plugin, max_level=args.level)

    def _filter_plugin(state: StateCore) -> None:
        state.tokens = [
            t
            for t in state.tokens
            if t.type.startswith("heading_") and int(t.tag[1]) <= args.level
        ]

    parser.use(lambda p: p.core.ruler.push("filter", _filter_plugin))
    text = parser.render(args.input.read())
    args.output.write(text)

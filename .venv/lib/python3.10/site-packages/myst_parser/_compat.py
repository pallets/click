"""Helpers for cross compatibility across dependency versions."""

from collections.abc import Callable, Iterable

from docutils.nodes import Element


def findall(node: Element) -> Callable[..., Iterable[Element]]:
    """Iterate through"""
    # findall replaces traverse in docutils v0.18
    # note a difference is that findall is an iterator
    return getattr(node, "findall", node.traverse)

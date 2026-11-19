# Private utilities that must not import anything else from the package. Keeping
# them dependency-free lets any module use them without creating circular imports.
from __future__ import annotations


def _split_opt(opt: str) -> tuple[str, str]:
    """Splits an option into a prefix and a value."""
    first = opt[:1]
    if first.isalnum():
        return "", opt
    if opt[1:2] == first:
        return opt[:2], opt[2:]
    return first, opt[1:]

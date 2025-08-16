from __future__ import annotations

import enum
import typing as t


class Sentinel(enum.Enum):
    """Enum used to define sentinel values.

    .. seealso::

        `PEP 661 - Sentinel Values <https://peps.python.org/pep-0661/>`_.
    """

    UNSET = object()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


UNSET = Sentinel.UNSET
"""A sentinel object used to indicate that a value is not set."""

T_UNSET = t.Literal[UNSET]  # type: ignore[valid-type]
"""Type hint for the :data:`UNSET` sentinel value."""

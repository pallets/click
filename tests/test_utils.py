from __future__ import annotations

import pytest

from click._utils import FLAG_NEEDS_VALUE, Sentinel, UNSET


class TestSentinel:
    def test_repr_unset(self) -> None:
        assert repr(Sentinel.UNSET) == "Sentinel.UNSET"

    def test_repr_flag_needs_value(self) -> None:
        assert repr(Sentinel.FLAG_NEEDS_VALUE) == "Sentinel.FLAG_NEEDS_VALUE"

    def test_str_equals_repr(self) -> None:
        assert str(Sentinel.UNSET) == repr(Sentinel.UNSET)
        assert str(Sentinel.FLAG_NEEDS_VALUE) == repr(Sentinel.FLAG_NEEDS_VALUE)

    def test_repr_stable(self) -> None:
        assert repr(Sentinel.UNSET) == repr(Sentinel.UNSET)
        assert repr(Sentinel.FLAG_NEEDS_VALUE) == repr(Sentinel.FLAG_NEEDS_VALUE)

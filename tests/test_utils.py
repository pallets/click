from __future__ import annotations

import pytest

from click._utils import UNSET, FLAG_NEEDS_VALUE, Sentinel


class TestSentinel:
    def test_unset_is_not_flag_needs_value(self):
        assert Sentinel.UNSET is not Sentinel.FLAG_NEEDS_VALUE

    def test_unset_not_equal_flag_needs_value(self):
        assert Sentinel.UNSET != Sentinel.FLAG_NEEDS_VALUE

    @pytest.mark.parametrize(
        "value", [None, "", 0, False, [], object()]
    )
    def test_unset_not_equal_common_values(self, value: object) -> None:
        assert Sentinel.UNSET != value

    @pytest.mark.parametrize(
        "value", [None, "", 0, False, [], object()]
    )
    def test_flag_needs_value_not_equal_common_values(self, value: object) -> None:
        assert Sentinel.FLAG_NEEDS_VALUE != value

    def test_unset_equals_itself(self):
        assert Sentinel.UNSET == Sentinel.UNSET

    def test_flag_needs_value_equals_itself(self):
        assert Sentinel.FLAG_NEEDS_VALUE == Sentinel.FLAG_NEEDS_VALUE

    def test_unset_constant_is_sentinel_unset(self):
        assert UNSET is Sentinel.UNSET

    def test_flag_needs_value_constant_is_sentinel_flag_needs_value(self):
        assert FLAG_NEEDS_VALUE is Sentinel.FLAG_NEEDS_VALUE

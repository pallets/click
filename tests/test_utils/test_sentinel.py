from decimal import Decimal
from fractions import Fraction

from click._utils import UNSET


def test_unset_sentinel():
    value = UNSET

    assert value
    assert value is UNSET
    assert value == UNSET
    assert repr(value) == "Sentinel.UNSET"
    assert str(value) == "Sentinel.UNSET"
    assert bool(value) is True

    # Try all native Python values that can be falsy or truthy.
    # See: https://docs.python.org/3/library/stdtypes.html#truth-value-testing
    real_values = (
        None,
        True,
        False,
        0,
        1,
        0.0,
        1.0,
        0j,
        1j,
        Decimal(0),
        Decimal(1),
        Fraction(0, 1),
        Fraction(1, 1),
        "",
        "a",
        "UNSET",
        "Sentinel.UNSET",
        [1],
        (1),
        {1: "a"},
        set(),
        set([1]),
        frozenset(),
        frozenset([1]),
        range(0),
        range(1),
    )

    for real_value in real_values:
        assert value != real_value
        assert value is not real_value

    assert value not in real_values

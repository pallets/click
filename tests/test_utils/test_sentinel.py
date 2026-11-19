import copy
import pickle
from decimal import Decimal
from fractions import Fraction

import pytest

import click
from click._utils import Sentinel
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


@pytest.mark.parametrize("sentinel", tuple(Sentinel))
def test_sentinel_value_is_a_bare_object(sentinel):
    """A sentinel's ``value`` must never look like data."""
    assert type(sentinel.value) is object


@pytest.mark.parametrize("sentinel", tuple(Sentinel))
@pytest.mark.parametrize(
    "duplicate",
    (
        copy.copy,
        copy.deepcopy,
        lambda value: pickle.loads(pickle.dumps(value)),
    ),
    ids=("copy", "deepcopy", "pickle"),
)
def test_sentinel_duplication_preserves_identity(sentinel, duplicate):
    """Sentinels are singletons: copying or pickling one returns the member.

    Pickling by value cannot rebuild a bare ``object()``: it unpickles as a new object,
    which ``Sentinel()`` rejects. ``Sentinel`` pickles its members by name.
    """
    assert duplicate(sentinel) is sentinel


@pytest.mark.parametrize(
    "duplicate",
    (
        copy.copy,
        copy.deepcopy,
        lambda value: pickle.loads(pickle.dumps(value)),
    ),
    ids=("copy", "deepcopy", "pickle"),
)
def test_parameter_duplication(duplicate):
    """Every ``Parameter`` holds ``UNSET`` in ``default`` unless one is given."""
    option = click.Option(["--name"])
    assert option.default is UNSET

    duplicated = duplicate(option)
    assert duplicated.default is UNSET
    assert duplicated.name == "name"

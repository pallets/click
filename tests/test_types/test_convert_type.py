import datetime
import uuid

import pytest

import click


@pytest.mark.parametrize(
    "default",
    [
        # Empty sequences fall back to STRING because ``_guess_type`` returns None.
        [],
        (),
        # Container types are guessed from the default but are not natively
        # supported, so they reach STRING through a different code path.
        set(),
        {1, 2},
        frozenset(),
        frozenset(["git"]),
        {},
        {"a": 1},
    ],
)
def test_convert_type_from_container_default(default):
    """Container defaults are not natively supported and fall back to STRING.

    Refs: https://github.com/pallets/click/issues/3036
    """
    assert click.types._convert_type(None, default) is click.STRING


@pytest.mark.parametrize(
    ("container_type", "value", "expected"),
    [
        (set, "a,b,c", {"a", ",", "b", "c"}),
        (frozenset, "abc", frozenset({"a", "b", "c"})),
    ],
)
def test_explicit_container_type_splits_string(container_type, value, expected):
    """An explicit ``set`` or ``frozenset`` type wraps the builtin in a
    ``_FuncParamType``, which splits CLI strings character-wise.

    Refs: https://github.com/pallets/click/issues/3036
    """
    param_type = click.types._convert_type(container_type)
    assert isinstance(param_type, click.types._FuncParamType)
    assert param_type.convert(value, None, None) == expected


@pytest.mark.parametrize(
    ("default", "expected"),
    [
        # Recognized scalars.
        (None, click.STRING),
        ("git", click.STRING),
        (5, click.INT),
        (1.5, click.FLOAT),
        (True, click.BOOL),
        # An empty sequence gives no item to read.
        ([], click.STRING),
        ((), click.STRING),
        # A sequence gives the type of its first item only.
        ([1, 2], click.INT),
        ((1, 2), click.INT),
        ([1.5, 2.5], click.FLOAT),
        ([1, "git"], click.INT),
        # Everything else falls back to STRING, including types Click ships.
        ({1, 2}, click.STRING),
        (frozenset({1, 2}), click.STRING),
        ({"a": 1}, click.STRING),
        (uuid.UUID(int=0), click.STRING),
        (datetime.datetime(2026, 1, 1), click.STRING),
        (b"git", click.STRING),
        (object(), click.STRING),
    ],
)
def test_type_inferred_from_default(default, expected):
    """Every row of the type-inference table in ``docs/parameter-types.md``.

    Keep the two in step: a change here is a change to documented behavior.

    Refs: https://github.com/pallets/click/issues/3036
    """
    assert click.types._convert_type(None, default) is expected


def test_type_inferred_from_nested_sequence_default():
    """A sequence of sequences gives a composite ``Tuple`` of the inner types.

    This is the one table row that is not a singleton ``ParamType``.

    Refs: https://github.com/pallets/click/issues/3036
    """
    param_type = click.types._convert_type(None, [(1, "git")])
    assert isinstance(param_type, click.Tuple)
    assert param_type.types == [click.INT, click.STRING]


def test_explicit_dict_type_rejects_string():
    """An explicit ``dict`` type cannot convert a plain CLI string at all.

    Refs: https://github.com/pallets/click/issues/3036
    """
    param_type = click.types._convert_type(dict)
    assert isinstance(param_type, click.types._FuncParamType)
    with pytest.raises(click.BadParameter):
        param_type.convert("abc", None, None)

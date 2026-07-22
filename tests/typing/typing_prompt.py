from typing_extensions import assert_type

import click

# Without ``type``, ``value_proc``, or a non-``str`` ``default``, the raw
# string input is returned.
assert_type(click.prompt("Name"), str)
assert_type(click.prompt("Name", default="bob"), str)

# The return type is narrowed by the ``type`` argument, whether it is a
# ParamType instance or a plain class, independently of the default's type.
assert_type(click.prompt("Age", type=click.INT), int)
assert_type(click.prompt("Age", type=click.IntRange(0, 130), default=18), int)
assert_type(click.prompt("Age", type=int), int)
assert_type(click.prompt("Age", type=int, default="100"), int)

# The return type is narrowed by the ``value_proc`` argument.


def to_float(value: str) -> float:
    return float(value)


assert_type(click.prompt("Ratio", value_proc=to_float), float)

# The return type is narrowed by the ``default`` argument alone.
assert_type(click.prompt("Age", default=18), int)


# A custom type may declare both its converted value and accepted input
# types. Omitting the input type parameter defaults it to ``Any``.
class DoublingType(click.ParamType[int, str]):
    name = "doubling"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> int:
        return int(value) * 2


assert_type(click.prompt("Num", type=DoublingType()), int)
assert_type(DoublingType()("21"), int)
assert_type(DoublingType()(None), None)


class SimpleType(click.ParamType[int]):
    name = "simple"


assert_type(SimpleType()("21"), int)

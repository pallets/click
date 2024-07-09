from typing_extensions import assert_type

from click import progressbar
from click._termui_impl import ProgressBar


def test_length_is_int() -> None:
    with progressbar(length=5) as bar:
        assert_type(bar, ProgressBar[int])
        for i in bar:
            assert_type(i, int)


def it() -> tuple[str, ...]:
    return ("hello", "world")


def test_generic_on_iterable() -> None:
    with progressbar(it()) as bar:
        assert_type(bar, ProgressBar[str])
        for s in bar:
            assert_type(s, str)

import pytest

from click.utils import make_default_short_help


@pytest.mark.parametrize(
    ("value", "max_length", "expect"),
    [
        pytest.param("", 10, "", id="empty"),
        pytest.param("123 567 90", 10, "123 567 90", id="equal length, no dot"),
        pytest.param("123 567 9. aaaa bbb", 10, "123 567 9.", id="sentence < max"),
        pytest.param("123 567\n\n 9. aaaa bbb", 10, "123 567", id="paragraph < max"),
        pytest.param("123 567 90123.", 10, "123 567...", id="truncate"),
        pytest.param("123 5678 xxxxxx", 10, "123...", id="length includes suffix"),
        pytest.param(
            "token in ~/.netrc ciao ciao",
            20,
            "token in ~/.netrc...",
            id="ignore dot in word",
        ),
    ],
)
@pytest.mark.parametrize(
    "alter",
    [
        pytest.param(None, id=""),
        pytest.param(
            lambda text: "\n\b\n" + "  ".join(text.split(" ")) + "\n", id="no-wrap mark"
        ),
    ],
)
def test_make_default_short_help(value, max_length, alter, expect):
    assert len(expect) <= max_length

    if alter:
        value = alter(value)

    out = make_default_short_help(value, max_length)
    assert out == expect

import pytest

import click


@pytest.mark.parametrize(
    ("value", "max_length", "expect"),
    [
        pytest.param("", 10, "", id="empty"),
        pytest.param("123 567 90", 10, "123 567 90", id="equal length, no dot"),
        pytest.param("123 567 9. Aaaa bbb", 10, "123 567 9.", id="sentence < max"),
        pytest.param("123 567 9.", 10, "123 567 9.", id="dot ends text"),
        pytest.param("123 567\n\n 9. aaaa bbb", 10, "123 567", id="paragraph < max"),
        pytest.param("123 567 90123.", 10, "123 567...", id="truncate"),
        pytest.param("123 5678 xxxxxx", 10, "123...", id="length includes suffix"),
        pytest.param(
            "token in ~/.netrc ciao ciao",
            20,
            "token in ~/.netrc...",
            id="ignore dot in word",
        ),
        pytest.param(
            "Weigh apples vs. pears.",
            30,
            "Weigh apples vs. pears.",
            id="abbreviation inside sentence",
        ),
        pytest.param(
            "Weigh apples vs. pears and plums.",
            20,
            "Weigh apples vs....",
            id="abbreviation inside truncated sentence",
        ),
        pytest.param("123 567 9. aaaa bbb", 10, "123 567...", id="lowercase after dot"),
        pytest.param(
            "Pick a fruit. 3 remain.", 20, "Pick a fruit.", id="digit after dot"
        ),
        pytest.param("well-behaved.", 8, "...", id="never split a hyphenated word"),
        pytest.param("supercalifragilistic", 10, "...", id="never split a long word"),
        pytest.param("ab cd", 3, "...", id="width fits the suffix only"),
        pytest.param("ab cd", 2, "...", id="width below the suffix"),
        pytest.param("ab", 2, "ab", id="text shorter than the suffix"),
        pytest.param("ab cd", -1, "...", id="negative width"),
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
    # A width too narrow for the suffix still returns the whole suffix.
    assert len(expect) <= max(max_length, len("..."))

    if alter:
        value = alter(value)

    out = click.utils._make_default_short_help(value, max_length)
    assert out == expect

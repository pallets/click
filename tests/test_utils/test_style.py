import pytest

import click


@pytest.mark.parametrize(
    "text",
    [
        "x y",
        "",
        # Text that looks like the tail of a style code.
        "38;5;91m",
        "[1mx y",
        "pêche 🍑",
        "x\ny",
    ],
)
@pytest.mark.parametrize(
    ("styles", "codes"),
    [
        ({}, ""),
        ({"fg": "black"}, "\x1b[30m"),
        ({"fg": "red"}, "\x1b[31m"),
        ({"fg": "green"}, "\x1b[32m"),
        ({"fg": "yellow"}, "\x1b[33m"),
        ({"fg": "blue"}, "\x1b[34m"),
        ({"fg": "magenta"}, "\x1b[35m"),
        ({"fg": "cyan"}, "\x1b[36m"),
        ({"fg": "white"}, "\x1b[37m"),
        ({"fg": "bright_black"}, "\x1b[90m"),
        ({"fg": "bright_red"}, "\x1b[91m"),
        ({"fg": "bright_green"}, "\x1b[92m"),
        ({"fg": "bright_yellow"}, "\x1b[93m"),
        ({"fg": "bright_blue"}, "\x1b[94m"),
        ({"fg": "bright_magenta"}, "\x1b[95m"),
        ({"fg": "bright_cyan"}, "\x1b[96m"),
        ({"fg": "bright_white"}, "\x1b[97m"),
        ({"fg": "reset"}, "\x1b[39m"),
        ({"bg": "black"}, "\x1b[40m"),
        ({"bg": "red"}, "\x1b[41m"),
        ({"bg": "green"}, "\x1b[42m"),
        ({"bg": "yellow"}, "\x1b[43m"),
        ({"bg": "blue"}, "\x1b[44m"),
        ({"bg": "magenta"}, "\x1b[45m"),
        ({"bg": "cyan"}, "\x1b[46m"),
        ({"bg": "white"}, "\x1b[47m"),
        ({"bg": "bright_black"}, "\x1b[100m"),
        ({"bg": "bright_red"}, "\x1b[101m"),
        ({"bg": "bright_green"}, "\x1b[102m"),
        ({"bg": "bright_yellow"}, "\x1b[103m"),
        ({"bg": "bright_blue"}, "\x1b[104m"),
        ({"bg": "bright_magenta"}, "\x1b[105m"),
        ({"bg": "bright_cyan"}, "\x1b[106m"),
        ({"bg": "bright_white"}, "\x1b[107m"),
        ({"bg": "reset"}, "\x1b[49m"),
        ({"fg": 91}, "\x1b[38;5;91m"),
        ({"bg": 91}, "\x1b[48;5;91m"),
        ({"fg": 255}, "\x1b[38;5;255m"),
        ({"bg": 255}, "\x1b[48;5;255m"),
        ({"fg": (135, 0, 175)}, "\x1b[38;2;135;0;175m"),
        ({"bg": (135, 0, 175)}, "\x1b[48;2;135;0;175m"),
        ({"bg": [135, 0, 175]}, "\x1b[48;2;135;0;175m"),
        ({"fg": (0, 0, 0)}, "\x1b[38;2;0;0;0m"),
        ({"fg": (255, 255, 255)}, "\x1b[38;2;255;255;255m"),
        # 256-color index 0 (black) is valid and must not be dropped by a
        # truthiness check on fg/bg.
        ({"fg": 0}, "\x1b[38;5;0m"),
        ({"bg": 0}, "\x1b[48;5;0m"),
        ({"bold": True}, "\x1b[1m"),
        ({"dim": True}, "\x1b[2m"),
        ({"underline": True}, "\x1b[4m"),
        ({"overline": True}, "\x1b[53m"),
        ({"italic": True}, "\x1b[3m"),
        ({"blink": True}, "\x1b[5m"),
        ({"reverse": True}, "\x1b[7m"),
        ({"strikethrough": True}, "\x1b[9m"),
        ({"bold": False}, "\x1b[22m"),
        ({"dim": False}, "\x1b[22m"),
        ({"underline": False}, "\x1b[24m"),
        ({"overline": False}, "\x1b[55m"),
        ({"italic": False}, "\x1b[23m"),
        ({"blink": False}, "\x1b[25m"),
        ({"reverse": False}, "\x1b[27m"),
        ({"strikethrough": False}, "\x1b[29m"),
        ({"fg": "black", "reset": False}, "\x1b[30m"),
        # Every option at once.
        (
            {
                "fg": (135, 0, 175),
                "bg": 91,
                "bold": True,
                "dim": True,
                "underline": True,
                "overline": True,
                "italic": True,
                "blink": True,
                "reverse": True,
                "strikethrough": True,
            },
            "\x1b[38;2;135;0;175m\x1b[48;5;91m\x1b[1m\x1b[2m\x1b[4m"
            "\x1b[53m\x1b[3m\x1b[5m\x1b[7m\x1b[9m",
        ),
    ],
)
def test_styling(styles, codes, text):
    reset = "" if styles.get("reset") is False else "\x1b[0m"
    styled = click.style(text, **styles)
    assert styled == f"{codes}{text}{reset}"
    assert click.unstyle(styled) == text


@pytest.mark.parametrize("param", ["fg", "bg"])
@pytest.mark.parametrize(
    "value",
    [
        "",
        "banana",
        "BLACK",
        b"red",
        True,
        False,
        -1,
        256,
        0.0,
        (),
        [],
        (0, 0),
        (0, 0, 0, 0),
        ("0", "0", "0"),
        (True, False, True),
        (-1, 0, 0),
        (0, 256, 0),
        (0.0, 0.0, 0.0),
    ],
)
def test_styling_invalid_color(param, value):
    with pytest.raises(ValueError, match="Unknown color"):
        click.style("x y", **{param: value})


def test_unstyle_exception_message():
    """A styled exception message reads back as plain text.

    https://github.com/pallets/click/issues/2419
    """
    exception = click.ClickException(click.style("red", fg="red") + " text")
    assert click.unstyle(str(exception)) == "red text"


@pytest.mark.parametrize(
    ("text", "expect"),
    [
        ("\x1b[?25lx y\x1b[?25h", "x y"),
        # Colon-delimited true-color SGR (ISO 8613-6).
        ("\x1b[38:2:255:0:0mx y\x1b[0m", "x y"),
        # 256-color with colon sub-parameters.
        ("\x1b[38:5:200mx y\x1b[0m", "x y"),
        # SGR mouse reporting.
        ("\x1b[<0;1;1Mx y\x1b[<0;1;1m", "x y"),
        # Intermediate byte before the final byte.
        ("\x1b[0 qx y", "x y"),
        # Non-letter final byte.
        ("x\x1b[3~y", "xy"),
    ],
)
def test_unstyle_other_ansi(text, expect):
    assert click.unstyle(text) == expect

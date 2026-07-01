import pytest

import click


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({}, "x y\x1b[0m"),
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"fg": "bright_black"}, "\x1b[90mx y\x1b[0m"),
        ({"fg": "bright_red"}, "\x1b[91mx y\x1b[0m"),
        ({"fg": "bright_green"}, "\x1b[92mx y\x1b[0m"),
        ({"fg": "bright_yellow"}, "\x1b[93mx y\x1b[0m"),
        ({"fg": "bright_blue"}, "\x1b[94mx y\x1b[0m"),
        ({"fg": "bright_magenta"}, "\x1b[95mx y\x1b[0m"),
        ({"fg": "bright_cyan"}, "\x1b[96mx y\x1b[0m"),
        ({"fg": "bright_white"}, "\x1b[97mx y\x1b[0m"),
        ({"fg": "reset"}, "\x1b[39mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"bg": "bright_black"}, "\x1b[100mx y\x1b[0m"),
        ({"bg": "bright_red"}, "\x1b[101mx y\x1b[0m"),
        ({"bg": "bright_green"}, "\x1b[102mx y\x1b[0m"),
        ({"bg": "bright_yellow"}, "\x1b[103mx y\x1b[0m"),
        ({"bg": "bright_blue"}, "\x1b[104mx y\x1b[0m"),
        ({"bg": "bright_magenta"}, "\x1b[105mx y\x1b[0m"),
        ({"bg": "bright_cyan"}, "\x1b[106mx y\x1b[0m"),
        ({"bg": "bright_white"}, "\x1b[107mx y\x1b[0m"),
        ({"bg": "reset"}, "\x1b[49mx y\x1b[0m"),
        ({"fg": 91}, "\x1b[38;5;91mx y\x1b[0m"),
        ({"bg": 91}, "\x1b[48;5;91mx y\x1b[0m"),
        ({"fg": 255}, "\x1b[38;5;255mx y\x1b[0m"),
        ({"bg": 255}, "\x1b[48;5;255mx y\x1b[0m"),
        ({"fg": (135, 0, 175)}, "\x1b[38;2;135;0;175mx y\x1b[0m"),
        ({"bg": (135, 0, 175)}, "\x1b[48;2;135;0;175mx y\x1b[0m"),
        ({"bg": [135, 0, 175]}, "\x1b[48;2;135;0;175mx y\x1b[0m"),
        ({"fg": (0, 0, 0)}, "\x1b[38;2;0;0;0mx y\x1b[0m"),
        ({"fg": (255, 255, 255)}, "\x1b[38;2;255;255;255mx y\x1b[0m"),
        # 256-color index 0 (black) is valid and must not be dropped by a
        # truthiness check on fg/bg.
        ({"fg": 0}, "\x1b[38;5;0mx y\x1b[0m"),
        ({"bg": 0}, "\x1b[48;5;0mx y\x1b[0m"),
        ({"bold": True}, "\x1b[1mx y\x1b[0m"),
        ({"dim": True}, "\x1b[2mx y\x1b[0m"),
        ({"underline": True}, "\x1b[4mx y\x1b[0m"),
        ({"overline": True}, "\x1b[53mx y\x1b[0m"),
        ({"italic": True}, "\x1b[3mx y\x1b[0m"),
        ({"blink": True}, "\x1b[5mx y\x1b[0m"),
        ({"reverse": True}, "\x1b[7mx y\x1b[0m"),
        ({"strikethrough": True}, "\x1b[9mx y\x1b[0m"),
        ({"bold": False}, "\x1b[22mx y\x1b[0m"),
        ({"dim": False}, "\x1b[22mx y\x1b[0m"),
        ({"underline": False}, "\x1b[24mx y\x1b[0m"),
        ({"overline": False}, "\x1b[55mx y\x1b[0m"),
        ({"italic": False}, "\x1b[23mx y\x1b[0m"),
        ({"blink": False}, "\x1b[25mx y\x1b[0m"),
        ({"reverse": False}, "\x1b[27mx y\x1b[0m"),
        ({"strikethrough": False}, "\x1b[29mx y\x1b[0m"),
        ({"fg": "black", "reset": False}, "\x1b[30mx y"),
    ],
)
def test_styling(styles, ref):
    assert click.style("x y", **styles) == ref
    assert click.unstyle(ref) == "x y"


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

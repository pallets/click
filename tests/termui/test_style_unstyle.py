import pytest

from click import style
from click import unstyle


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"bg": 91}, "\x1b[48;5;91mx y\x1b[0m"),
        ({"bg": (135, 0, 175)}, "\x1b[48;2;135;0;175mx y\x1b[0m"),
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
    assert style("x y", **styles) == ref
    assert unstyle(ref) == "x y"


@pytest.mark.parametrize(("text", "expect"), [("\x1b[?25lx y\x1b[?25h", "x y")])
def test_unstyle_other_ansi(text, expect):
    assert unstyle(text) == expect

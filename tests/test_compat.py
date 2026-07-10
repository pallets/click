from __future__ import annotations

import re
import sys

import pytest

import click
from click._compat import _ansi_re
from click._compat import strip_ansi
from click._compat import term_len
from click._textwrap import _truncate_visible

ESC = "\033"

# Inventory of every escape sequence Click itself emits. ``strip_ansi`` must
# keep removing all of them.
CLICK_EMITTED = [
    # SGR foreground/background, the basic 16 colors.
    f"{ESC}[30m",
    f"{ESC}[37m",
    f"{ESC}[40m",
    f"{ESC}[47m",
    # SGR 256-color and true-color (Click renders these with semicolons).
    f"{ESC}[38;5;200m",
    f"{ESC}[48;5;91m",
    f"{ESC}[38;2;255;12;128m",
    f"{ESC}[48;2;135;0;175m",
    # SGR attributes and their resets.
    f"{ESC}[1m",
    f"{ESC}[22m",
    f"{ESC}[4m",
    f"{ESC}[24m",
    f"{ESC}[53m",
    f"{ESC}[55m",
    f"{ESC}[9m",
    f"{ESC}[29m",
    # Reset-all appended by style().
    f"{ESC}[0m",
    # Screen clear and cursor home from click.clear().
    f"{ESC}[2J",
    f"{ESC}[1;1H",
    # Cursor hide/show around the progress bar.
    f"{ESC}[?25l",
    f"{ESC}[?25h",
]

# CSI sequences Click never emits but may receive from other tooling.
CSI_FOREIGN = [
    # Colon-delimited (ISO 8613-6) true-color and 256-color SGR.
    f"{ESC}[38:2:255:0:0m",
    f"{ESC}[38:5:200m",
    f"{ESC}[1;38:2::255:0:0m",  # empty colon field is a valid parameter
    # SGR mouse reporting (the ``<`` parameter byte is 0x3C).
    f"{ESC}[<0;30;40M",
    f"{ESC}[<0;30;40m",
    # Private-mode set/reset with a multi-digit parameter.
    f"{ESC}[?1049h",
    f"{ESC}[?1049l",
    # Cursor-shape select: an intermediate byte (space, 0x20) before final ``q``.
    f"{ESC}[0 q",
    f"{ESC}[2 q",
    # Set scrolling region: a non-``m`` letter final byte.
    f"{ESC}[1;24r",
    # Function-key / bracketed-paste codes ending in ``~`` (0x7E).
    f"{ESC}[3~",
    f"{ESC}[200~",
    # Empty parameter list (``ESC [ m`` is a valid reset).
    f"{ESC}[m",
]

# The previous pattern, kept here to prove the new one is a superset.
_LEGACY_ANSI_RE = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert click._compat._is_jupyter_kernel_output(stream=JupyterKernelFakeStream())


@pytest.mark.parametrize(
    "stream",
    [None, sys.stdin, sys.stderr, sys.stdout],
)
@pytest.mark.parametrize(
    ("color", "expected_override"),
    [
        (True, False),
        (False, True),
        (None, None),
    ],
)
@pytest.mark.parametrize(
    ("isatty", "is_jupyter", "expected"),
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
    ],
)
def test_should_strip_ansi(
    monkeypatch,
    stream,
    color: bool | None,
    expected_override: bool | None,
    isatty: bool,
    is_jupyter: bool,
    expected: bool,
) -> None:
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: is_jupyter
    )

    if expected_override is not None:
        expected = expected_override
    assert click._compat.should_strip_ansi(stream=stream, color=color) == expected


@pytest.mark.parametrize("seq", CLICK_EMITTED + CSI_FOREIGN)
def test_strip_ansi_removes_full_sequence(seq):
    """Every complete CSI sequence is stripped, alone or wrapped in text."""
    assert strip_ansi(seq) == ""
    assert strip_ansi(f"a{seq}b") == "ab"
    assert term_len(f"a{seq}b") == 2


@pytest.mark.parametrize("final", ["m", "H", "J", "A", "z"])
@pytest.mark.parametrize("params", ["", "0", "1;2", ";", "?25", "0;0;0"])
def test_strip_ansi_is_superset_of_legacy(params, final):
    """Everything the legacy pattern stripped, the CSI grammar still strips."""
    seq = f"{ESC}[{params}{final}"
    assert _LEGACY_ANSI_RE.fullmatch(seq) is not None
    assert strip_ansi(seq) == ""
    assert strip_ansi(f"a{seq}b") == "ab"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"{ESC}[31mred{ESC}[0m", "red"),
        (f"a{ESC}[38:2:1:2:3mb{ESC}[0mc", "abc"),
        (f"{ESC}[?25l{ESC}[2Jhidden{ESC}[?25h", "hidden"),
        (f"{ESC}[<0;1;1Mclick{ESC}[<0;1;1m", "click"),
        # Several adjacent sequences around each visible character.
        (f"{ESC}[1m{ESC}[31mA{ESC}[0m {ESC}[32mB{ESC}[0m", "A B"),
        # Real terminal captures ported from the boltons strip_ansi tests.
        # ANSI art fragment (its doctest example).
        (f"{ESC}[0m{ESC}[1;36mart{ESC}[46;34m\xdc", "art\xdc"),
        # `ls` color output, ending on a dangling SGR with no text after it.
        (
            f"ls\r\n{ESC}[00m{ESC}[01;31mfile.zip{ESC}[00m\r\n{ESC}[01;31m",
            "ls\r\nfile.zip\r\n",
        ),
        # Tab-separated colorized fields.
        (f"\t{ESC}[0;35mIP{ESC}[0m\t{ESC}[0;36m192.1.0.2{ESC}[0m", "\tIP\t192.1.0.2"),
        # A styled cell inside a box-drawing table.
        (
            f"╒══════╕\n│ {ESC}[1mCell{ESC}[0m │\n╘══════╛",
            "╒══════╕\n│ Cell │\n╘══════╛",
        ),
        # Kaomoji with a bolded run.
        (f"(╯°□°)╯︵ {ESC}[1m┻━┻{ESC}[0m", "(╯°□°)╯︵ ┻━┻"),
    ],
)
def test_strip_ansi_mixed_content(text, expected):
    assert strip_ansi(text) == expected
    assert term_len(text) == len(expected)


def test_strip_ansi_stops_at_final_byte():
    """The match ends at the first final byte."""
    assert strip_ansi(f"{ESC}[31mX{ESC}[0mY") == "XY"
    assert strip_ansi(f"{ESC}[1m{ESC}[31mZ") == "Z"
    # The final ``m`` ends the sequence; the following ``;1m`` is plain text.
    assert strip_ansi(f"{ESC}[m;1m") == ";1m"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "plain text",
        "100% [done]",
        "array[0] = 1",
        "a;b;c",
        # Looks like SGR parameters but lacks the ESC introducer.
        "[38;5;200m not an escape",
        "[0m",
    ],
)
def test_strip_ansi_leaves_plain_text(text):
    """Text that merely resembles an escape sequence is never stripped."""
    assert strip_ansi(text) == text
    assert term_len(text) == len(text)


@pytest.mark.parametrize(
    "text",
    [
        f"{ESC}",  # lone ESC
        f"{ESC}[",  # CSI introducer with no final byte
        f"{ESC}[31",  # parameters but no final byte
        f"{ESC}[38:2:1",  # colon parameters, truncated
        f"{ESC}[0 ",  # intermediate byte but no final byte
    ],
)
def test_strip_ansi_leaves_incomplete_sequences(text):
    """An unterminated sequence (missing its final byte) is left untouched."""
    assert strip_ansi(text) == text


def test_strip_ansi_is_idempotent():
    text = f"{ESC}[38:2:1:2:3mhi{ESC}[0m {ESC}[<0;1;1mthere{ESC}[?25h"
    once = strip_ansi(text)
    assert once == "hi there"
    assert strip_ansi(once) == once


@pytest.mark.parametrize(
    ("text", "visible"),
    [
        ("", 0),
        ("plain", 5),
        (f"{ESC}[31mred{ESC}[0m", 3),
        (f"{ESC}[38;2;1;2;3mrgb{ESC}[0m", 3),
        (f"{ESC}[38:2:1:2:3mrgb{ESC}[0m", 3),
        (f"{ESC}[<0;1;1Mx{ESC}[<0;1;1m", 1),
        (f"{ESC}[0 qq", 1),
        (f"{ESC}[?25lvisible{ESC}[?25h", 7),
        (f"{ESC}[1m{ESC}[4m{ESC}[31mhello{ESC}[0m", 5),
    ],
)
def test_term_len(text, visible):
    assert term_len(text) == visible


@pytest.mark.parametrize("seq", CLICK_EMITTED + CSI_FOREIGN)
def test_ansi_re_matches_whole_sequence(seq):
    """``_ansi_re`` matches a complete sequence end to end as one token."""
    m = _ansi_re.match(seq)
    assert m is not None
    assert m.start() == 0
    assert m.end() == len(seq)


@pytest.mark.parametrize(
    ("text", "n", "expected"),
    [
        # No escapes: behaves like a plain prefix slice.
        ("abcdef", 3, "abc"),
        ("abc", 10, "abc"),
        ("abc", 0, ""),
        ("abc", -1, ""),
        # A leading escape is kept and does not count toward the budget.
        (f"{ESC}[31mabcdef{ESC}[0m", 3, f"{ESC}[31mabc"),
        # A colon true-color escape stays intact; the cut lands after 3 chars.
        (f"{ESC}[38:2:1:2:3mabcdef", 3, f"{ESC}[38:2:1:2:3mabc"),
        # A trailing escape past the cut is not pulled in.
        (f"{ESC}[31mabc{ESC}[0m", 3, f"{ESC}[31mabc"),
    ],
)
def test_truncate_visible(text, n, expected):
    out = _truncate_visible(text, n)
    assert out == expected
    assert term_len(out) <= max(n, 0)

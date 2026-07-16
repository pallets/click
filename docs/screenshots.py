"""Generate annotated terminal screenshots for Click documentation.

Renders terminal text output as PNG images with colored annotation boxes,
using Pillow. All dependencies are pip-installable. Images are rendered at
2x scale for crisp display on high-DPI screens.

Usage::

    # Generate all screenshots (default output: docs/_static/)
    python docs/screenshots.py

    # Specify output directory
    python docs/screenshots.py --output /path/to/dir

    # List available screenshots
    python docs/screenshots.py --list
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Annotation:
    """A labeled box highlighting a section of terminal output.

    The box spans from the line that starts with *start_text* to the line
    immediately before the next section header (a non-indented, non-empty
    line that appears after the start).
    """

    label: str
    start_text: str
    color: str
    end_text: str | None = None


@dataclass(frozen=True)
class Screenshot:
    """Specification for a single terminal screenshot."""

    filename: str
    text: str
    title: str = ""
    annotations: list[Annotation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Font detection
# ---------------------------------------------------------------------------

_MONOSPACE_PATHS = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    # macOS
    "/System/Library/Frameworks/CoreFoundation.framework"
    "/Resources/BundledFonts/Menlo.ttc",
    "/Library/Fonts/Menlo.ttc",
    # Windows
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
]


def _find_monospace_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return a monospace font, searching common system paths."""
    for path in _MONOSPACE_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    # Pillow >= 10.1 accepts a *size* keyword for the built-in font.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

# Color palette
_BG = "#1e1e2e"
_TITLEBAR = "#313244"
_TITLEBAR_DOT_R = "#f38ba8"
_TITLEBAR_DOT_Y = "#f9e2af"
_TITLEBAR_DOT_G = "#a6e3a1"
_TEXT = "#cdd6f4"
_MUTED = "#6c7086"
_BORDER = "#45475a"


def _split_hex(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def render_screenshot(
    text: str,
    *,
    title: str = "",
    annotations: list[Annotation] | None = None,
    width: int = 720,
    scale: int = 2,
    font_path: str | None = None,
) -> Image.Image:
    """Render *text* as a terminal-style image.

    Parameters
    ----------
    text : str
        The terminal text to render (trailing newline is stripped).
    title : str
        Optional title shown in the title bar.
    annotations : list[Annotation] | None
        Colored boxes to draw over the text.
    width : int
        Logical (CSS) pixel width of the output image.
    scale : int
        Scale factor for high-DPI rendering.  The actual image width is
        ``width * scale``.
    font_path : str | None
        Explicit path to a TrueType font file.  When *None* a system
        monospace font is auto-detected.
    """
    annotations = annotations or []

    # -- font ---------------------------------------------------------------
    font_size = 13 * scale
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = _find_monospace_font(font_size)

    # -- measure character cell ---------------------------------------------
    tmp = Image.new("RGB", (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    char_w = tmp_draw.textlength("M", font=font)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + int(3 * scale)

    # -- layout constants ---------------------------------------------------
    pad_x = 16 * scale
    pad_y = 12 * scale
    titlebar_h = 32 * scale
    corner_r = 8 * scale

    lines = text.rstrip("\n").split("\n")
    max_line_len = max((len(line) for line in lines), default=0)
    text_area_w = max(int(max_line_len * char_w) + pad_x * 2, width * scale - pad_x * 2)
    img_w = text_area_w + pad_x * 2
    text_area_h = len(lines) * line_h + pad_y * 2
    img_h = titlebar_h + text_area_h + pad_y * 2

    # -- create image -------------------------------------------------------
    img = Image.new("RGB", (img_w, img_h), _split_hex(_BG))
    draw = ImageDraw.Draw(img)

    # rounded rectangle background
    draw.rounded_rectangle(
        [(0, 0), (img_w - 1, img_h - 1)],
        radius=corner_r,
        fill=_split_hex(_BG),
        outline=_split_hex(_BORDER),
        width=max(1, scale),
    )

    # title bar
    draw.rounded_rectangle(
        [(0, 0), (img_w - 1, titlebar_h)],
        radius=corner_r,
        fill=_split_hex(_TITLEBAR),
    )
    # square off bottom corners of title bar
    draw.rectangle(
        [(0, titlebar_h - corner_r), (img_w - 1, titlebar_h)],
        fill=_split_hex(_TITLEBAR),
    )

    # traffic-light dots
    dot_y = titlebar_h // 2
    dot_r = int(5 * scale)
    dot_spacing = int(18 * scale)
    dot_start_x = pad_x + dot_r
    for cx, color in [
        (dot_start_x, _TITLEBAR_DOT_R),
        (dot_start_x + dot_spacing, _TITLEBAR_DOT_Y),
        (dot_start_x + dot_spacing * 2, _TITLEBAR_DOT_G),
    ]:
        draw.ellipse(
            [(cx - dot_r, dot_y - dot_r), (cx + dot_r, dot_y + dot_r)],
            fill=_split_hex(color),
        )

    # title text
    if title:
        title_font_size = int(12 * scale)
        try:
            title_font = _find_monospace_font(title_font_size)
        except Exception:
            title_font = font
        bbox = draw.textbbox((0, 0), title, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(
            ((img_w - tw) / 2, (titlebar_h - (bbox[3] - bbox[1])) / 2),
            title,
            fill=_split_hex(_MUTED),
            font=title_font,
        )

    # -- annotation geometry ------------------------------------------------
    text_origin_x = pad_x
    text_origin_y = titlebar_h + pad_y

    # Build line-index lookup for each annotation.
    annotation_rects: list[tuple[int, int, int, int, tuple[int, int, int], str]] = []
    for ann in annotations:
        start_idx: int | None = None
        end_idx: int | None = None
        for i, line in enumerate(lines):
            if start_idx is None and line.startswith(ann.start_text):
                start_idx = i
            elif start_idx is not None:
                if ann.end_text is not None:
                    if line.startswith(ann.end_text):
                        end_idx = i
                        break
                else:
                    # Section ends at the next non-indented, non-empty line.
                    if line and not line[0].isspace():
                        end_idx = i
                        break
        if start_idx is not None and end_idx is None:
            end_idx = len(lines)
        if start_idx is not None:
            box_x = text_origin_x - int(4 * scale)
            box_y = text_origin_y + start_idx * line_h - int(2 * scale)
            box_w = text_area_w - pad_x + int(8 * scale)
            box_h = (end_idx - start_idx) * line_h + int(4 * scale)
            annotation_rects.append(
                (box_x, box_y, box_w, box_h, _split_hex(ann.color), ann.label)
            )

    # Draw annotation boxes (behind text).
    for bx, by, bw, bh, bcolor, blabel in annotation_rects:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            [(bx, by), (bx + bw, by + bh)],
            radius=int(4 * scale),
            fill=(*bcolor, 40),
            outline=(*bcolor, 180),
            width=max(1, 2 * scale),
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # label pill
        label_font_size = int(10 * scale)
        try:
            label_font = _find_monospace_font(label_font_size)
        except Exception:
            label_font = font
        lbbox = draw.textbbox((0, 0), blabel, font=label_font)
        lw = lbbox[2] - lbbox[0]
        lh = lbbox[3] - lbbox[1]
        pill_pad_x = int(6 * scale)
        pill_pad_y = int(2 * scale)
        pill_x = bx + int(8 * scale)
        pill_y = by - lh - pill_pad_y * 2 - int(2 * scale)
        if pill_y < titlebar_h:
            pill_y = by + bh + int(4 * scale)
        draw.rounded_rectangle(
            [
                (pill_x - pill_pad_x, pill_y - pill_pad_y),
                (pill_x + lw + pill_pad_x, pill_y + lh + pill_pad_y),
            ],
            radius=int(3 * scale),
            fill=(*bcolor, 220),
        )
        draw.text((pill_x, pill_y), blabel, fill=(255, 255, 255), font=label_font)

    # -- render text --------------------------------------------------------
    for i, line in enumerate(lines):
        y = text_origin_y + i * line_h
        draw.text((text_origin_x, y), line, fill=_split_hex(_TEXT), font=font)

    return img


# ---------------------------------------------------------------------------
# Example Click applications (used to generate screenshots)
# ---------------------------------------------------------------------------


def _build_repo_cli():
    """Build a repo-style CLI matching examples/repo/repo.py."""
    import click

    @click.group()
    @click.option(
        "--repo-home",
        envvar="REPO_HOME",
        default=".repo",
        metavar="PATH",
        help="Changes the repository folder location.",
    )
    @click.option(
        "--config",
        nargs=2,
        multiple=True,
        metavar="KEY VALUE",
        help="Overrides a config key/value pair.",
    )
    @click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
    @click.version_option("1.0")
    @click.pass_context
    def cli(ctx, repo_home, config, verbose):
        """Repo is a command line tool that showcases how to build complex
        command line interfaces with Click.

        This tool is supposed to look like a distributed version control
        system to show how something like this can be structured.
        """
        pass  # pragma: no cover

    @cli.command()
    @click.argument("src")
    @click.argument("dest", required=False)
    @click.option(
        "--shallow/--deep",
        default=False,
        help="Makes a checkout shallow or deep.  Deep by default.",
    )
    @click.option(
        "--rev", "-r", default="HEAD", help="Clone a specific revision instead of HEAD."
    )
    def clone(src, dest, shallow, rev):
        """Clones a repository.

        This will clone the repository at SRC into the folder DEST.  If DEST
        is not provided this will automatically use the last path component
        of SRC and create that folder.
        """

    @cli.command()
    @click.option(
        "--message",
        "-m",
        multiple=True,
        help="The commit message.  If provided multiple times each"
        " argument gets converted into a new line.",
    )
    @click.argument("files", nargs=-1, type=click.Path())
    def commit(message, files):
        """Commits outstanding changes.

        Commit changes to the given files into the repository.
        """

    @cli.command(short_help="Copies files.")
    @click.option(
        "--force", is_flag=True, help="forcibly copy over an existing managed file"
    )
    @click.argument("src", nargs=-1, type=click.Path())
    @click.argument("dst", type=click.Path())
    def copy(force, src, dst):
        """Copies one or multiple files to a new location."""

    @cli.command()
    @click.confirmation_option()
    def delete():
        """Deletes a repository.

        This will throw away the current repository.
        """

    @cli.command()
    @click.option("--username", prompt=True, help="The developer's shown username.")
    @click.option("--email", prompt="E-Mail", help="The developer's email address")
    @click.password_option(help="The login password.")
    def setuser(username, email, password):
        """Sets the user credentials.

        This will override the current user config.
        """

    return cli


def _get_help_text(cli, args: list[str] | None = None) -> str:
    """Invoke a Click command with --help and return the output."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, args=args or ["--help"])
    return result.output


# ---------------------------------------------------------------------------
# Screenshot definitions
# ---------------------------------------------------------------------------


def _make_screenshots() -> list[Screenshot]:
    """Build the list of screenshots to generate."""
    cli = _build_repo_cli()
    help_text = _get_help_text(cli)

    return [
        Screenshot(
            filename="cli-help-annotated.png",
            text=help_text,
            title="repo --help",
            annotations=[
                Annotation(
                    label="Usage",
                    start_text="Usage:",
                    color="#89b4fa",
                    end_text="Repo is",
                ),
                Annotation(
                    label="Description",
                    start_text="Repo is",
                    color="#a6e3a1",
                    end_text="Options:",
                ),
                Annotation(
                    label="Options",
                    start_text="Options:",
                    color="#f9e2af",
                    end_text="Commands:",
                ),
                Annotation(
                    label="Commands",
                    start_text="Commands:",
                    color="#f38ba8",
                ),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate annotated terminal screenshots for Click docs.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).parent / "_static",
        help="Output directory (default: docs/_static/)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available screenshots and exit.",
    )
    parser.add_argument(
        "--font",
        type=str,
        default=None,
        help="Path to a TrueType font file.",
    )
    args = parser.parse_args(argv)

    screenshots = _make_screenshots()

    if args.list:
        for s in screenshots:
            ann_count = len(s.annotations)
            print(f"  {s.filename}  ({ann_count} annotation(s))")
        return

    args.output.mkdir(parents=True, exist_ok=True)

    for s in screenshots:
        img = render_screenshot(
            s.text,
            title=s.title,
            annotations=s.annotations,
            font_path=args.font,
        )
        out_path = args.output / s.filename
        img.save(str(out_path))
        print(f"  {out_path}  ({img.width}x{img.height})")


if __name__ == "__main__":
    main()

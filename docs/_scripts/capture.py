"""
Screenshot capture script for Click documentation.

Uses Playwright to capture crisp terminal screenshots, including highlighting boxes.

Usage:
    python -m docs._scripts.capture --output docs/_static/screenshots
    python -m docs._scripts.capture --app "examples/simple.py --help"
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Playwright imports
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright is required. Install with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)


def run_click_command(cmd: str, timeout: int = 10) -> str:
    """Run a click command in a subprocess and return the output."""
    result = subprocess.run(
        cmd if isinstance(cmd, list) else cmd.split(),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent.parent,
    )
    return result.stdout + result.stderr


def apply_annotations(html: str, boxes: list[dict]) -> str:
    """Inject CSS boxes into HTML for annotation overlay."""
    style = """
    <style>
        .screenshot-annotation {{
            position: absolute;
            border: 2px solid #0066cc;
            background: rgba(0, 102, 204, 0.1);
            border-radius: 4px;
            pointer-events: none;
        }}
        .screenshot-annotation span {{
            position: absolute;
            top: -1.5em;
            left: 0;
            background: #0066cc;
            color: white;
            padding: 2px 6px;
            font-size: 12px;
            font-family: monospace;
            border-radius: 3px 3px 0 0;
            white-space: nowrap;
        }}
    </style>
    """
    boxes_html = ""
    for i, box in enumerate(boxes):
        boxes_html += f"""
        <div class="screenshot-annotation" style="
            left: {box.get('left', 'auto')};
            top: {box.get('top', 'auto')};
            width: {box.get('width', 'auto')};
            height: {box.get('height', 'auto')};
            right: {box.get('right', 'auto')};
            bottom: {box.get('bottom', 'auto')};
        ">
            {f'<span>{box.get("label", "")}</span>' if 'label' in box else ''}
        </div>"""
    
    return html.replace("</body>", f"{style}{boxes_html}</body>")


def capture_terminal(
    command: str,
    width: int = 900,
    height: int = 400,
    font_size: int = 14,
    font_family: str = "JetBrains Mono, Fira Code, Consolas, monospace",
    boxes: list | None = None,
) -> bytes:
    """Capture a terminal screenshot of a command's output."""
    with sync_playwright() as p:
        # Use webkit for consistent rendering
        browser = p.chromium.launch(headless=True)
        
        # Create HTML page with terminal styling
        terminal_output = run_click_command(command)
        escaped_output = (
            terminal_output
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{
                background: #1e1e1e;
                margin: 20px;
                padding: 20px;
            }}
            pre {{
                font-family: {font_family};
                font-size: {font_size}px;
                line-height: 1.5;
                color: #d4d4d4;
                background: #1e1e1e;
                padding: 20px;
                border-radius: 8px;
                overflow: auto;
                white-space: pre;
            }}
            .prompt {{ color: #569cd6; }}
            .command {{ color: #9cdcfe; }}
            .output {{ color: #d4d4d4; }}
        </style></head>
        <body>
        <pre>{escaped_output}</pre>
        </body>
        </html>
        """
        
        if boxes:
            html_content = apply_annotations(html_content, boxes)
        
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html_content)
        screenshot = page.screenshot(type="png", full_page=True)
        browser.close()
        return screenshot


def main():
    parser = argparse.ArgumentParser(description="Capture terminal screenshots for Click docs")
    parser.add_argument("--output", "-o", default="docs/_static/screenshots",
                        help="Output directory")
    parser.add_argument("--command", "-c", 
                        help="Click command to capture (e.g., 'python examples/simple.py --help')")
    parser.add_argument("--width", "-w", type=int, default=900)
    parser.add_argument("--height", "-H", type=int, default=400)
    parser.add_argument("--font-size", "-fs", type=int, default=14)
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.command:
        name = args.command.replace(" ", "_").replace("/", "_").replace(".", "_")
        output_path = output_dir / f"{name}.png"
        screenshot = capture_terminal(
            args.command,
            width=args.width,
            height=args.height,
            font_size=args.font_size,
        )
        output_path.write_bytes(screenshot)
        print(f"Captured: {output_path}")
    else:
        # Demo: capture the issue example command
        demo_command = "python -m click --help"
        screenshot = capture_terminal(demo_command, width=700, height=300)
        demo_path = output_dir / "demo.png"
        demo_path.write_bytes(screenshot)
        print(f"Demo captured: {demo_path}")


if __name__ == "__main__":
    main()

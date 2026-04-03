"""Click enhanced utilities - additional helpful functions for Click."""

import os
import sys
from typing import Optional

import click


def prompt_for_confirmation(
    message: str,
    default: bool = False,
    abort: bool = False,
    prompt_suffix: str = ": ",
) -> bool:
    """
    Prompt the user for confirmation with custom message.

    Args:
        message: The confirmation message to display
        default: Default value if user just presses enter
        abort: If True, abort the program on 'no'
        prompt_suffix: Suffix to add after the prompt

    Returns:
        True if confirmed, False otherwise
    """
    return click.confirm(
        message + prompt_suffix,
        default=default,
        abort=abort,
    )


def prompt_for_value(
    message: str,
    default: Optional[str] = None,
    hide_input: bool = False,
    confirmation_prompt: bool = False,
    type: Optional[click.ParamType] = None,
) -> str:
    """
    Prompt the user for a value with custom options.

    Args:
        message: The prompt message
        default: Default value if user presses enter
        hide_input: Whether to hide the input
        confirmation_prompt: Ask for confirmation (for passwords)
        type: Click type for validation

    Returns:
        The value entered by the user
    """
    return click.prompt(
        message,
        default=default,
        hide_input=hide_input,
        confirmation_prompt=confirmation_prompt,
        type=type or click.STRING,
    )


def select_from_options(
    message: str,
    options: list,
    default: Optional[int] = None,
    allow_multiple: bool = False,
) -> Optional[any]:
    """
    Present a selection menu to the user.

    Args:
        message: The selection prompt message
        options: List of available options
        default: Default option index (0-based)
        allow_multiple: Allow selecting multiple options

    Returns:
        Selected option(s)
    """
    if allow_multiple:
        return click.prompt(
            message,
            type=click.Choice(options),
            prompt_suffix=f" (select multiple, comma-separated, default: {options[default or 0] if default is not None else 'none'})",
        )
    else:
        return click.prompt(
            message,
            type=click.Choice(options),
            default=options[default] if default is not None else None,
        )


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""

    def __init__(self, label: str = "Processing", total: Optional[int] = None):
        self.label = label
        self.total = total
        self.current = 0

    def __enter__(self):
        self.bar = click.progressbar(
            label=self.label,
            length=self.total,
            show_pos=True,
        )
        self.bar.__enter__()
        return self

    def __exit__(self, *args):
        self.bar.__exit__(*args)

    def update(self, n: int = 1):
        """Update progress by n steps."""
        self.current += n
        self.bar.update(n)

    def set_current(self, value: int):
        """Set current progress to a specific value."""
        delta = value - self.current
        if delta > 0:
            self.update(delta)


def spinner(duration: float = 3.0, label: str = "Working..."):
    """
    Display a spinner while running a short operation.

    Args:
        duration: How long to show the spinner (seconds)
        label: Label to display next to spinner

    Usage:
        with spinner("Loading..."):
            time.sleep(2)
    """
    import time
    import threading

    stop_event = threading.Event()

    def spin():
        chars = "|/-\\"
        i = 0
        while not stop_event.is_set():
            click.echo(f"\r{label} {chars[i % len(chars)]}", nl=False)
            time.sleep(0.1)
            i += 1
        click.echo("\r" + " " * (len(label) + 3), nl=False)

    thread = threading.Thread(target=spin)
    thread.start()

    try:
        time.sleep(duration)
    finally:
        stop_event.set()
        thread.join()
        click.echo("\r" + " " * (len(label) + 3), nl=False)


def print_table(data: list, headers: list, title: Optional[str] = None):
    """
    Print data in a formatted table.

    Args:
        data: List of rows (each row is a list of values)
        headers: List of column headers
        title: Optional table title

    Usage:
        data = [["Alice", "25"], ["Bob", "30"]]
        print_table(data, ["Name", "Age"], "Users")
    """
    if not data:
        click.echo("No data to display")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Print title if provided
    if title:
        click.echo(click.style(title, bold=True))
        click.echo("=" * len(title))

    # Print headers
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    click.echo(click.style(header_row, bold=True))
    click.echo("-" * len(header_row))

    # Print data rows
    for row in data:
        data_row = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        click.echo(data_row)
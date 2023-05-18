"""
Module: click_markdown
======================

This module extends the functionality of the Click library by adding a Markdown feature. It provides a `markdown` function that takes a Markdown content string and renders it using rich console output.

The `markdown` function utilizes the `rich.markdown.Markdown` class to convert Markdown content to rich console output, allowing for syntax highlighting using the specified code theme.

Usage:
------

To use this module, import it and call the `markdown` function:

from click_markdown import markdown

content = "# Header\n\nThis is some text."
markdown(content, code_theme="monokai")

"""
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def markdown(content: str, code_theme: str = "monokai"):
    """
    Convert Markdown content to rich console output.

    Parameters:
    -----------
    content (str): The Markdown content string to be rendered.
    code_theme (str, optional): The code theme to use for syntax highlighting. Defaults to "monokai".

    Returns:
    --------
    None

    Example:
    --------
    >>> content = "# Header\n\nThis is some **bold** text."
    >>> markdown(content, code_theme="monokai")
    Renders the Markdown content with syntax highlighting using the "monokai" code theme.
    """
    md = Markdown(markup=content, code_theme=code_theme)
    console.log(md)

"""
Interactive Command Line Wizard Example for Click

This example demonstrates the interactive features added to Click:
1. Interactive commands and groups
2. Conditional prompting
3. Interactive menus
4. Web API integration
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import click
from click import interactive_command
from click import interactive_group
from click import interactive_option


@interactive_command()
@click.option("--name", prompt="What is your name?", help="Your name")
@click.option("--age", type=int, prompt="How old are you?", help="Your age")
@click.option("--city", prompt="Where do you live?", help="Your city")
def simple_greet(name: str, age: int, city: str) -> None:
    """A simple interactive greeting command."""
    click.echo(f"\nHello {name}!")
    click.echo(f"You are {age} years old and live in {city}.")


@interactive_command(interactive_all=True)
@click.option("--username", help="Username for login")
@click.option("--password", hide_input=True, help="Password for login")
@click.option("--remember-me", is_flag=True, help="Remember login")
def login(username: str, password: str, remember_me: bool) -> None:
    """Login command with interactive mode for all parameters."""
    click.echo(f"\nLogging in as {username}...")
    if remember_me:
        click.echo("Will remember your login.")
    click.echo("Login successful!")


@interactive_command()
@click.option("--name", prompt="Project name?", help="Name of the project")
@click.option("--project-type", type=click.Choice(["python", "javascript", "rust"]),
              prompt="Project type?", help="Type of project")
@interactive_option(
    "--use-docker",
    is_flag=True,
    interactive_help="Docker helps with containerization and deployment",
    prompt="Use Docker?",
)
@interactive_option(
    "--python-version",
    type=click.Choice(["3.8", "3.9", "3.10", "3.11", "3.12"]),
    interactive_after="project_type",
    interactive_condition=lambda params: params.get("project_type") == "python",
    prompt="Python version?",
)
@interactive_option(
    "--node-version",
    type=click.Choice(["16", "18", "20", "21"]),
    interactive_after="project_type",
    interactive_condition=lambda params: params.get("project_type") == "javascript",
    prompt="Node.js version?",
)
@interactive_option(
    "--rust-edition",
    type=click.Choice(["2018", "2021"]),
    interactive_after="project_type",
    interactive_condition=lambda params: params.get("project_type") == "rust",
    prompt="Rust edition?",
)
def create_project(
    name: str,
    project_type: str,
    use_docker: bool,
    python_version: str | None,
    node_version: str | None,
    rust_edition: str | None,
) -> None:
    """Create a new project with conditional options."""
    click.echo(f"\nCreating {project_type} project: {name}")
    click.echo(f"Use Docker: {'Yes' if use_docker else 'No'}")

    if python_version:
        click.echo(f"Python version: {python_version}")
    if node_version:
        click.echo(f"Node.js version: {node_version}")
    if rust_edition:
        click.echo(f"Rust edition: {rust_edition}")

    click.echo("\nProject created successfully!")


@interactive_group()
def cli() -> None:
    """Interactive CLI Demo - A demonstration of Click's interactive features."""
    pass


@cli.command()
@click.option("--message", prompt="Message to echo?", help="Message to display")
@click.option("--count", type=int, default=1, help="Number of times to echo")
def echo_cmd(message: str, count: int) -> None:
    """Echo a message multiple times."""
    for i in range(count):
        click.echo(f"{i + 1}: {message}")


@cli.command()
@click.option("--source", prompt="Source file?", help="Source file path")
@click.option("--destination", prompt="Destination?", help="Destination path")
@click.option("--force", is_flag=True, help="Force overwrite")
def copy(source: str, destination: str, force: bool) -> None:
    """Copy a file (simulated)."""
    click.echo(f"\nCopying {source} to {destination}...")
    if force:
        click.echo("Force mode enabled.")
    click.echo("Copy completed!")


@cli.command()
@click.option("--input-file", prompt="Input file?", help="Input file path")
@click.option("--output-format", type=click.Choice(["json", "csv", "xml"]),
              prompt="Output format?", help="Output format")
@click.option("--verbose", is_flag=True, help="Verbose output")
def process(input_file: str, output_format: str, verbose: bool) -> None:
    """Process a file (simulated)."""
    click.echo(f"\nProcessing {input_file}...")
    if verbose:
        click.echo(f"Output format: {output_format}")
        click.echo("Running in verbose mode...")
    click.echo("Processing completed!")


if __name__ == "__main__":
    cli()

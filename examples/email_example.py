#!/usr/bin/env python3
"""
Example demonstrating the EMAIL parameter type in Click.

This example shows how to use the EMAIL type to validate email addresses
in command-line applications.
"""

import click


@click.command()
@click.option(
    "--email",
    type=click.EMAIL,
    required=True,
    help="Email address to process"
)
@click.option(
    "--notify-email",
    type=click.EMAIL,
    help="Optional notification email address"
)
def send_message(email, notify_email):
    """Send a message to the specified email address."""
    click.echo(f"Sending message to: {email}")
    
    if notify_email:
        click.echo(f"Notification will be sent to: {notify_email}")
    
    # Simulate sending email
    click.echo("✅ Message sent successfully!")


if __name__ == "__main__":
    send_message()

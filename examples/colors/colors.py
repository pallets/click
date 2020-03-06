import click


all_colors = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
)


@click.command()
def cli():
    """This script prints some colors.  If colorama is installed this will
    also work on Windows.  It will also automatically remove all ANSI
    styles if data is piped into a file.

    Give it a try!
    """
    for color in all_colors:
        click.echo(click.style("I am colored %s" % color, fg=color))
    for color in all_colors:
        click.echo(click.style("I am colored %s and bold" % color, fg=color, bold=True))
    for color in all_colors:
        click.echo(
            click.style("I am reverse colored %s" % color, fg=color, reverse=True)
        )

    click.echo(click.style("I am blinking", blink=True))
    click.echo(click.style("I am underlined", underline=True))

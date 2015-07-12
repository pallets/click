"""
Core components for printer_style
"""


import click


COLORS = (
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'white',
)


@click.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.option('-c', '--color', type=click.Choice(COLORS), required=True)
def background(infile, outfile, color):

    """
    Add a background color.
    """

    for line in infile:
        click.echo(line, file=outfile, color=color)


@click.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
@click.option('-c', '--color', type=click.Choice(COLORS), required=True)
def color(infile, outfile, color):

    """
    Add color to text.
    """

    for line in infile:
        click.echo(line, color=color, file=outfile)

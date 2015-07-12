"""
Commandline interface for printer
"""


from pkg_resources import iter_entry_points

import click


@click.group(plugins=iter_entry_points('printer.plugins'))
def cli():

    """
    Format and print file contents.

    \b
    For example:
    \b
        $ cat README.rst | printer lower
    """


@cli.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
def upper(infile, outfile):

    """
    Convert to upper case.
    """

    for line in infile:
        outfile.write(line.upper())


@cli.command()
@click.argument('infile', type=click.File('r'), default='-')
@click.argument('outfile', type=click.File('w'), default='-')
def lower(infile, outfile):

    """
    Convert to lower case.
    """

    for line in infile:
        outfile.write(line.lower())

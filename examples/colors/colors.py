import click
from colorama import Fore


@click.command()
def cli():
    """This script prints some colors through colorama.  This will give
    colors on OS X, Linux and Windows but it will automatically disable
    those colors if stdout is redirected to a file.

    Give it a try!
    """
    click.echo(Fore.YELLOW + 'Hello World!' + Fore.RESET)
    click.echo(Fore.RED + 'Goodbye World!' + Fore.RESET)

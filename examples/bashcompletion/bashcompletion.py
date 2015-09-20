import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument("name", type=click.STRING, autocompletion=["John", "Simon", "Doe"])
@click.option('--debug/--no-debug', default=False)
@click.option('-f', default=False)
def cmd1():
    pass

@cli.command()
def cmd2():
    pass

@cli.command()
def cmd3():
    pass


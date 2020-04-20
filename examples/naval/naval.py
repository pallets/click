import click


@click.group()
@click.version_option()
def cli():
    """Naval Fate.

    This is the docopt example adopted to Click but with some actual
    commands implemented and not just the empty parsing which really
    is not all that interesting.
    """


@cli.group()
def ship():
    """Manages ships."""


@ship.command("new")
@click.argument("name")
def ship_new(name):
    """Creates a new ship."""
    click.echo(f"Created ship {name}")


@ship.command("move")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option("--speed", metavar="KN", default=10, help="Speed in knots.")
def ship_move(ship, x, y, speed):
    """Moves SHIP to the new location X,Y."""
    click.echo(f"Moving ship {ship} to {x},{y} with speed {speed}")


@ship.command("shoot")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
def ship_shoot(ship, x, y):
    """Makes SHIP fire to X,Y."""
    click.echo(f"Ship {ship} fires to {x},{y}")


@cli.group("mine")
def mine():
    """Manages mines."""


@mine.command("set")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option(
    "ty",
    "--moored",
    flag_value="moored",
    default=True,
    help="Moored (anchored) mine. Default.",
)
@click.option("ty", "--drifting", flag_value="drifting", help="Drifting mine.")
def mine_set(x, y, ty):
    """Sets a mine at a specific coordinate."""
    click.echo(f"Set {ty} mine at {x},{y}")


@mine.command("remove")
@click.argument("x", type=float)
@click.argument("y", type=float)
def mine_remove(x, y):
    """Removes a mine at a specific coordinate."""
    click.echo(f"Removed mine at {x},{y}")

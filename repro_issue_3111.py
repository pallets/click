import os
import sys

# Use local Click from this repo without installing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import click
from click.testing import CliRunner


@click.command()
@click.option(
    "--without-xyz",
    "enable_xyz",
    is_flag=True,
    flag_value=False,
    default=True,
)
def cli(enable_xyz: bool) -> None:
    click.echo(f"enable_xyz = {enable_xyz}")


def main() -> None:
    runner = CliRunner()

    r1 = runner.invoke(cli, [])
    assert r1.exit_code == 0, r1.output
    # Expected behavior from Click 8.2.x (and what users likely intend):
    # if the flag is not passed, the explicit default=True should be used.
    assert r1.output.strip() == "enable_xyz = True", r1.output

    r2 = runner.invoke(cli, ["--without-xyz"])
    assert r2.exit_code == 0, r2.output
    assert r2.output.strip() == "enable_xyz = False", r2.output


if __name__ == "__main__":
    main()

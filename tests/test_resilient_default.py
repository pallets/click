import click
from click.testing import CliRunner


def test_default_callback_not_called_during_resilient_parsing():
    """A default callable must not be invoked while resilient parsing is on
    (e.g. during shell completion). Resolving it can be expensive or have
    side effects, and the value is never used.

    Regression test for pallets/click#2614.
    """
    calls = []

    def expensive_default():
        calls.append(1)
        return "computed"

    @click.command()
    @click.option("--name", default=expensive_default)
    def cli(name):
        click.echo(f"name={name}")

    # Resilient parsing is what completion uses.
    with click.Context(cli, resilient_parsing=True) as ctx:
        cli.get_params(ctx)[0].get_default(ctx)

    assert calls == [], "default callback was invoked during resilient parsing"


def test_default_callback_called_normally():
    """Sanity check: the callback still runs in normal (non-resilient) mode."""
    calls = []

    def expensive_default():
        calls.append(1)
        return "computed"

    @click.command()
    @click.option("--name", default=expensive_default)
    def cli(name):
        click.echo(f"name={name}")

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert calls == [1], "default callback not invoked in normal mode"

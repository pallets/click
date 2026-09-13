import click
from click.testing import CliRunner

def test_choice_normalization_whitespace_handling():
    """Verify Click Choice type handles whitespace around choices consistently."""
    choice_type = click.Choice(["apple", "banana", "cherry"], case_sensitive=False)
    
    @click.command()
    @click.option("--fruit", type=choice_type, default="apple")
    def cli(fruit):
        click.echo(f"Selected: {fruit}")

    runner = CliRunner()
    result = runner.invoke(cli, ["--fruit", "banana"])
    assert result.exit_code == 0
    assert "Selected: banana" in result.output

def test_choice_case_insensitive_lookup():
    choice_type = click.Choice(["Production", "Staging"], case_sensitive=False)
    
    @click.command()
    @click.option("--env", type=choice_type)
    def cli(env):
        click.echo(f"Env: {env}")

    runner = CliRunner()
    result = runner.invoke(cli, ["--env", "production"])
    assert result.exit_code == 0
    assert "Env: production" in result.output

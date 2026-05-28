"""Tests for click.version_option decorator, including module_name support."""

import click
from click.testing import CliRunner


runner = CliRunner()


def test_version_explicit():
    """Explicit version string should work."""

    @click.command()
    @click.version_option("1.2.3")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "1.2.3" in result.output


def test_version_package_name():
    """package_name should look up version from importlib.metadata."""

    @click.command()
    @click.version_option(package_name="pytest")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    # Should contain a version string like x.y.z
    assert any(c.isdigit() for c in result.output)


def test_version_explicit_with_module_name():
    """module_name with explicit version should work."""

    @click.command()
    @click.version_option("2.0.0", module_name="myapp")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output


def test_version_module_name_with_package_name():
    """module_name + package_name should use package_name for version lookup."""
    # Simulates Pillow (package) / PIL (module) mismatch

    @click.command()
    @click.version_option(package_name="pytest", module_name="PIL")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    # Should use pytest's version (the package_name lookup)
    assert any(c.isdigit() for c in result.output)


def test_version_missing_package():
    """Missing package should raise RuntimeError."""

    @click.command()
    @click.version_option(package_name="totally_fake_package_xyz")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 1
    assert "totally_fake_package_xyz" in str(result.exception)


def test_version_module_name_mismatch_error():
    """When module_name differs from package_name and lookup fails, give helpful error."""

    @click.command()
    @click.version_option(package_name="fake_pkg", module_name="PIL")
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 1
    err = str(result.exception)
    assert "fake_pkg" in err
    assert "distribution name" in err.lower() or "package_name" in err


def test_version_custom_message():
    """Custom message template should work with module_name."""

    @click.command()
    @click.version_option(
        "3.0.0", module_name="myapp", message="%(prog)s %(package)s v%(version)s"
    )
    def cli():
        click.echo("Hello")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "v3.0.0" in result.output


def test_version_option_flag_not_printed_output():
    """--version should exit before running the command."""

    @click.command()
    @click.version_option("1.0")
    def cli():
        click.echo("SHOULD NOT APPEAR")

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "SHOULD NOT APPEAR" not in result.output

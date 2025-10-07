"""
Test suite for Click issue #3084: Optional value not optional anymore
These tests should FAIL in Click 8.3.0 and PASS after the fix.
"""

import click
from click.testing import CliRunner
import pytest


class TestOptionalValueBug:
    """Tests for is_flag=False with flag_value parameter bug"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_basic_optional_value(self):
        """Test basic optional value functionality from documentation"""
        @click.command()
        @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
        def hello(name):
            click.echo(f"Hello, {name}!")

        # Test with flag only (THIS FAILS IN 8.3.0)
        result = self.runner.invoke(hello, ['--name'])

        # This is the bug - it should succeed but returns error code 2
        assert result.exit_code == 0, f"Got exit code {result.exit_code}: {result.output}"
        assert result.output == "Hello, Flag!\n"


    def test_multiple_optional_values(self):
        """Test multiple options with optional values"""
        @click.command()
        @click.option("--verbose", "-v", is_flag=False, flag_value="INFO", default="WARNING")
        @click.option("--config", "-c", is_flag=False, flag_value="default.cfg", default=None)
        def cli(verbose, config):
            click.echo(f"Verbosity: {verbose}")
            click.echo(f"Config: {config}")

        # Test with flags only (THIS FAILS IN 8.3.0)
        result = self.runner.invoke(cli, ['--verbose', '--config'])
        assert result.exit_code == 0, f"Got exit code {result.exit_code}: {result.output}"
        assert "Verbosity: INFO" in result.output
        assert "Config: default.cfg" in result.output

    def test_optional_value_with_type_conversion(self):
        """Test optional value with type conversion"""
        @click.command()
        @click.option("--count", is_flag=False, flag_value="1", type=int, default=0)
        def repeat(count):
            for i in range(count):
                click.echo(f"Line {i+1}")

        # Test flag only with type conversion (THIS FAILS IN 8.3.0)
        result = self.runner.invoke(repeat, ['--count'])
        assert result.exit_code == 0, f"Got exit code {result.exit_code}: {result.output}"
        assert result.output == "Line 1\n"


def test_simple_reproduction():
    """Simplest possible test case to reproduce the bug"""
    runner = CliRunner()

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

    # This is the exact issue from the bug report
    result = runner.invoke(hello, ['--name'])

    # Current behavior in 8.3.0:
    # Exit code: 2
    # Output: "Error: Option '--name' requires an argument."

    # Expected behavior:
    # Exit code: 0
    # Output: "Hello, Flag!\n"

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    assert result.exit_code == 0, "Bug confirmed: option with flag_value requires argument"

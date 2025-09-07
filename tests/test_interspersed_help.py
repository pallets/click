"""Tests for interspersed arguments with help options.

This module tests the fix for the issue where help options don't work correctly
when interspersed arguments are enabled and the help flag appears after global options
but before the target subcommand.

Example issue:
    cli --global-option subcommand --help

Should show help for 'subcommand', not the main CLI.
"""

import click


class TestInterspersedHelp:
    """Test help functionality with interspersed arguments."""

    def test_interspersed_help_shows_subcommand_help(self, runner):
        """Help after global options should show subcommand help, not main help."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--global-flag", is_flag=True, help="Global flag")
        def cli(global_flag):
            """Main CLI application."""
            pass

        @cli.command()
        @click.option("--sub-option", help="Subcommand option")
        def subcommand(sub_option):
            """Subcommand help text."""
            click.echo(f"subcommand executed with {sub_option}")

        # Test the problematic case: global option before subcommand help
        result = runner.invoke(cli, ["--global-flag", "subcommand", "--help"])

        # Should show subcommand help, not main CLI help
        assert "Subcommand help text." in result.output
        assert "sub-option" in result.output
        assert "Main CLI application." not in result.output
        assert result.exit_code == 0

    def test_interspersed_help_shows_main_help_when_no_subcommand(self, runner):
        """Help should show main help when no subcommand is present."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--global-flag", is_flag=True, help="Global flag")
        def cli(global_flag):
            """Main CLI application."""
            pass

        @cli.command()
        def subcommand():
            """Subcommand help text."""
            pass

        # Test help without subcommand
        result = runner.invoke(cli, ["--global-flag", "--help"])

        # Should show main CLI help
        assert "Main CLI application." in result.output
        assert "global-flag" in result.output
        assert "subcommand" in result.output
        assert result.exit_code == 0

    def test_interspersed_help_works_with_multiple_global_options(self, runner):
        """Help should work correctly with multiple global options."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
        @click.option("--config", help="Config file path")
        def cli(verbose, config):
            """Main CLI application."""
            pass

        @cli.command()
        @click.option("--name", help="Name parameter")
        def profile(name):
            """Manage user profiles."""
            pass

        # Test with multiple global options
        result = runner.invoke(
            cli, ["--verbose", "--config", "config.yml", "profile", "--help"]
        )

        # Should show profile help
        assert "Manage user profiles." in result.output
        assert "name" in result.output
        assert "Name parameter" in result.output
        assert "Main CLI application." not in result.output
        assert result.exit_code == 0

    def test_interspersed_help_works_without_interspersed_args(self, runner):
        """Normal help behavior should be preserved when interspersed args
        are disabled."""

        @click.group()  # No interspersed args
        @click.option("--global-flag", is_flag=True)
        def cli(global_flag):
            """Main CLI application."""
            pass

        @cli.command()
        def subcommand():
            """Subcommand help text."""
            pass

        # This should work normally (no change in behavior)
        result = runner.invoke(cli, ["subcommand", "--help"])

        # Should show subcommand help
        assert "Subcommand help text." in result.output
        assert result.exit_code == 0

    def test_interspersed_help_with_nested_groups(self, runner):
        """Help should work correctly with nested command groups."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--global-flag", is_flag=True)
        def cli(global_flag):
            """Main CLI."""
            pass

        @cli.group()
        def user():
            """User management commands."""
            pass

        @user.command()
        @click.option("--email", help="User email")
        def create(email):
            """Create a new user."""
            pass

        # Test nested group help
        result = runner.invoke(cli, ["--global-flag", "user", "--help"])

        # Should show user group help
        assert "User management commands." in result.output
        assert "create" in result.output
        assert result.exit_code == 0

        # Test nested command help
        result = runner.invoke(cli, ["--global-flag", "user", "create", "--help"])

        # Should show create command help
        assert "Create a new user." in result.output
        assert "email" in result.output
        assert result.exit_code == 0

    def test_interspersed_help_ignores_non_existent_commands(self, runner):
        """Help should fall back to main help for non-existent commands."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--global-flag", is_flag=True)
        def cli(global_flag):
            """Main CLI application."""
            pass

        @cli.command()
        def real_command():
            """A real command."""
            pass

        # Test with non-existent command - should show main help
        result = runner.invoke(cli, ["--global-flag", "nonexistent", "--help"])

        # Should show main CLI help since 'nonexistent' is not a valid command
        assert "Main CLI application." in result.output
        assert result.exit_code == 0

    def test_interspersed_help_with_short_help_flag(self, runner):
        """Test that -h works when explicitly added as a help option."""

        @click.group(
            context_settings={
                "allow_interspersed_args": True,
                "help_option_names": ["--help", "-h"],
            }
        )
        @click.option("--global-flag", is_flag=True)
        def cli(global_flag):
            """Main CLI application."""
            pass

        @cli.command()
        def subcommand():
            """Subcommand help text."""
            pass

        # Test with -h when it's explicitly configured
        result = runner.invoke(cli, ["--global-flag", "subcommand", "-h"])

        # Should show subcommand help
        assert "Subcommand help text." in result.output
        assert result.exit_code == 0

    def test_interspersed_help_preserves_option_values(self, runner):
        """Test that option values don't interfere with help command detection."""

        @click.group(context_settings={"allow_interspersed_args": True})
        @click.option("--output-format", default="json", help="Output format")
        def cli(output_format):
            """Main CLI application."""
            pass

        @cli.command()
        @click.option("--name", help="Name parameter")
        def user(name):
            """User management."""
            pass

        # Test with option that takes a value
        result = runner.invoke(cli, ["--output-format", "xml", "user", "--help"])

        # Should show user command help
        assert "User management." in result.output
        assert "name" in result.output
        assert result.exit_code == 0

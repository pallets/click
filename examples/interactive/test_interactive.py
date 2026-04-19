"""
Test script for Click interactive features.

This script tests the basic functionality of the interactive command line wizard.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import click
from click import interactive_command
from click import interactive_group
from click import interactive_option
from click.interactive import InteractiveCommand
from click.interactive import InteractiveGroup
from click.interactive import InteractiveOption


def test_interactive_option_creation():
    """Test that InteractiveOption can be created."""
    opt = InteractiveOption(
        ["--name"],
        interactive=True,
        prompt="What is your name?",
    )
    assert opt.interactive is True
    assert opt.prompt == "What is your name?"
    print("✅ InteractiveOption creation test passed")


def test_interactive_command_creation():
    """Test that InteractiveCommand can be created."""
    
    @interactive_command()
    @click.option("--name", prompt="Name?")
    def test_cmd(name):
        return name
    
    assert isinstance(test_cmd, InteractiveCommand)
    assert test_cmd.interactive is True
    print("✅ InteractiveCommand creation test passed")


def test_interactive_group_creation():
    """Test that InteractiveGroup can be created."""
    
    @interactive_group()
    def test_grp():
        pass
    
    assert isinstance(test_grp, InteractiveGroup)
    assert test_grp.interactive is True
    assert test_grp.interactive_menu is True
    print("✅ InteractiveGroup creation test passed")


def test_conditional_interactive_option():
    """Test conditional interactive options."""
    
    def condition(params):
        return params.get("project_type") == "python"
    
    opt = InteractiveOption(
        ["--python-version"],
        interactive=True,
        interactive_after="project_type",
        interactive_condition=condition,
        prompt="Python version?",
    )
    
    assert opt.interactive_after == "project_type"
    assert opt.interactive_condition is condition
    
    assert opt.interactive_condition({"project_type": "python"}) is True
    assert opt.interactive_condition({"project_type": "javascript"}) is False
    print("✅ Conditional interactive option test passed")


def test_interactive_option_info_dict():
    """Test that InteractiveOption properly exports info dict."""
    opt = InteractiveOption(
        ["--test"],
        interactive=True,
        interactive_help="This is a test option",
    )
    
    info = opt.to_info_dict()
    assert info["interactive"] is True
    assert info["interactive_help"] == "This is a test option"
    print("✅ InteractiveOption info dict test passed")


def test_interactive_all_flag():
    """Test the interactive_all flag."""
    
    @interactive_command(interactive_all=True)
    @click.option("--name")
    @click.option("--age", type=int)
    def test_cmd(name, age):
        pass
    
    assert test_cmd.interactive_all is True
    print("✅ interactive_all flag test passed")


def test_interactive_skip():
    """Test the interactive_skip parameter."""
    
    @interactive_command(interactive_skip=["help", "version"])
    @click.option("--name", prompt="Name?")
    def test_cmd(name):
        pass
    
    assert "help" in test_cmd.interactive_skip
    assert "version" in test_cmd.interactive_skip
    print("✅ interactive_skip test passed")


def test_interactive_menu_flag():
    """Test the interactive_menu flag for groups."""
    
    @interactive_group(interactive_menu=False)
    def test_grp():
        pass
    
    assert test_grp.interactive_menu is False
    print("✅ interactive_menu flag test passed")


def test_should_interactive_prompt():
    """Test the should_interactive_prompt method."""
    from click.core import Context
    
    opt = InteractiveOption(
        ["--test"],
        interactive=True,
    )
    
    ctx = Context(click.Command("test"))
    
    assert opt.should_interactive_prompt(ctx, {}) is True
    print("✅ should_interactive_prompt test passed")


def test_should_interactive_prompt_with_condition():
    """Test should_interactive_prompt with conditions."""
    from click.core import Context
    
    opt = InteractiveOption(
        ["--python-version"],
        interactive=True,
        interactive_after="project_type",
        interactive_condition=lambda params: params.get("project_type") == "python",
    )
    
    ctx = Context(click.Command("test"))
    
    assert opt.should_interactive_prompt(ctx, {}) is False
    assert opt.should_interactive_prompt(ctx, {"project_type": "javascript"}) is False
    assert opt.should_interactive_prompt(ctx, {"project_type": "python"}) is True
    print("✅ should_interactive_prompt with condition test passed")


def test_interactive_group_subcommand():
    """Test that InteractiveGroup creates InteractiveCommand subcommands."""
    
    @interactive_group()
    def test_grp():
        pass
    
    @test_grp.command()
    @click.option("--name", prompt="Name?")
    def greet(name):
        return name
    
    assert isinstance(test_grp, InteractiveGroup)
    assert test_grp.interactive is True
    
    cmd = test_grp.get_command(click.Context(test_grp), "greet")
    assert cmd is not None
    assert isinstance(cmd, InteractiveCommand)
    assert cmd.interactive is True
    print("✅ InteractiveGroup subcommand test passed")


def test_interactive_group_with_custom_cls():
    """Test that InteractiveGroup respects custom cls parameter."""
    
    @interactive_group()
    def test_grp():
        pass
    
    @test_grp.command(cls=click.Command)
    @click.option("--name")
    def hello(name):
        return name
    
    cmd = test_grp.get_command(click.Context(test_grp), "hello")
    assert cmd is not None
    assert not isinstance(cmd, InteractiveCommand)
    print("✅ InteractiveGroup with custom cls test passed")


def test_interactive_group_non_interactive():
    """Test InteractiveGroup with interactive=False."""
    
    @interactive_group(interactive=False)
    def test_grp():
        pass
    
    @test_grp.command()
    @click.option("--name")
    def welcome(name):
        return name
    
    assert test_grp.interactive is False
    
    cmd = test_grp.get_command(click.Context(test_grp), "welcome")
    assert cmd is not None
    assert not isinstance(cmd, InteractiveCommand)
    print("✅ InteractiveGroup non-interactive test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Click Interactive Features Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_interactive_option_creation,
        test_interactive_command_creation,
        test_interactive_group_creation,
        test_conditional_interactive_option,
        test_interactive_option_info_dict,
        test_interactive_all_flag,
        test_interactive_skip,
        test_interactive_menu_flag,
        test_should_interactive_prompt,
        test_should_interactive_prompt_with_condition,
        test_interactive_group_subcommand,
        test_interactive_group_with_custom_cls,
        test_interactive_group_non_interactive,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

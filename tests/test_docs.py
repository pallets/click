from pathlib import Path

ROOT = Path(__file__).parent.parent
ALIASED_GROUP_FILES = [
    ROOT / "docs" / "extending-click.md",
    ROOT / "examples" / "aliases" / "aliases.py",
    ROOT / "tests" / "typing" / "typing_aliased_group.py",
]


def test_aliased_group_examples_handle_unknown_commands():
    for path in ALIASED_GROUP_FILES:
        text = path.read_text()

        assert "return cmd.name, cmd, args" not in text, path
        assert "return cmd.name if cmd else None, cmd, args" in text, path

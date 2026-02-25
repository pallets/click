from __future__ import annotations

import configparser
import importlib.util
from pathlib import Path

from click.testing import CliRunner


def _load_aliases_example_cli():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "examples" / "aliases" / "aliases.py"
    spec = importlib.util.spec_from_file_location("click_examples_aliases", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.cli


def test_alias_writes_config_file(tmp_path):
    cli = _load_aliases_example_cli()
    runner = CliRunner()

    config_path = tmp_path / "aliases.ini"
    config_path.write_text("", encoding="utf-8")

    result = runner.invoke(
        cli,
        ["alias", "foo", "status", "--config_file", str(config_path)],
    )
    assert result.exit_code == 0, result.output
    assert "Added 'foo' as alias for 'status'" in result.output

    parser = configparser.RawConfigParser()
    parser.read(config_path, encoding="utf-8")
    assert parser.has_section("aliases")
    assert parser.get("aliases", "foo") == "status"


def test_alias_dry_run_does_not_write_config_file(tmp_path):
    cli = _load_aliases_example_cli()
    runner = CliRunner()

    config_path = tmp_path / "aliases.ini"
    config_path.write_text("", encoding="utf-8")
    before = config_path.read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["alias", "foo", "status", "--config_file", str(config_path), "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    assert "Would add 'foo' as alias for 'status' in" in result.output

    after = config_path.read_text(encoding="utf-8")
    assert after == before


def test_alias_overwrites_existing_alias(tmp_path):
    cli = _load_aliases_example_cli()
    runner = CliRunner()

    config_path = tmp_path / "aliases.ini"
    config_path.write_text("", encoding="utf-8")

    first = runner.invoke(
        cli,
        ["alias", "foo", "status", "--config_file", str(config_path)],
    )
    assert first.exit_code == 0, first.output

    second = runner.invoke(
        cli,
        ["alias", "foo", "commit", "--config_file", str(config_path)],
    )
    assert second.exit_code == 0, second.output
    assert "Added 'foo' as alias for 'commit'" in second.output

    parser = configparser.RawConfigParser()
    parser.read(config_path, encoding="utf-8")
    assert parser.get("aliases", "foo") == "commit"

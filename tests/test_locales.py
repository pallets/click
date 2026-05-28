from textwrap import dedent

import pytest

import click
from click.locales import set_click_locale
from click.testing import CliRunner
from click.testing import ContextualizedLocale


def test_test_unrecognized_locale(runner: CliRunner) -> None:
    @click.command()
    def cli() -> None:
        pass

    with pytest.raises(NotImplementedError):
        set_click_locale("unrecognized")


def test_help_translation_to_russian(runner: CliRunner) -> None:
    @click.command()
    def cli() -> None:
        pass

    with ContextualizedLocale("ru_RU"):
        result = runner.invoke(cli, ["--help"])

    assert result.stdout == dedent("""\
        Использование: cli [OPTIONS]

        Опции:
          --help  Показать это сообщение и выйти.
    """)


def test_help_translation_to_bulgarian(runner: CliRunner) -> None:
    @click.command()
    def cli() -> None:
        pass

    with ContextualizedLocale("bg_BG"):
        result = runner.invoke(cli, ["--help"])

    assert result.stdout == dedent("""\
        Използване: cli [OPTIONS]

        Опции:
          --help  Покажи това съобщение и излез.
    """)


def test_dynamic_change_of_language(runner: CliRunner) -> None:
    @click.command()
    def cli() -> None:
        pass

    with ContextualizedLocale("en_US"):
        result = runner.invoke(cli, ["--help"])

    assert result.stdout == dedent("""\
        Usage: cli [OPTIONS]

        Options:
          --help  Show this message and exit.
    """)

    with ContextualizedLocale("ru_RU"):
        result = runner.invoke(cli, ["--help"])

    assert result.stdout == dedent("""\
        Использование: cli [OPTIONS]

        Опции:
          --help  Показать это сообщение и выйти.
    """)

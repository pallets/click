import enum

import click

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


class MyEnum(enum.Enum):
    """Dummy enum for unit tests."""

    ONE = "one"
    TWO = "two"
    THREE = "three"
    ONE_ALIAS = ONE


def test_option_normalization(runner):
    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("--foo")
    @click.option("-x")
    def cli(foo, x):
        click.echo(foo)
        click.echo(x)

    result = runner.invoke(cli, ["--FOO", "42", "-X", 23])
    assert result.output == "42\n23\n"


def test_choice_normalization(runner):
    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("--choice", type=click.Choice(["Foo", "Bar"]))
    def cli(choice):
        click.echo(choice)

    result = runner.invoke(cli, ["--CHOICE", "FOO"])
    assert result.output == "Foo\n"


def test_enum_choice_normalization(runner):
    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("--choice", type=click.EnumChoice(MyEnum))
    def cli(choice):
        click.echo(choice)

    result = runner.invoke(cli, ["--CHOICE", "ONE"])
    assert result.output == "MyEnum.ONE\n"


def test_command_normalization(runner):
    @click.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    def foo():
        click.echo("here!")

    result = runner.invoke(cli, ["FOO"])
    assert result.output == "here!\n"

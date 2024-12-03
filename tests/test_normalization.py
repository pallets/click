import click

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


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
    @click.option(
        "--method",
        type=click.Choice(
            ["SCREAMING_SNAKE_CASE", "snake_case", "PascalCase", "kebab-case"],
            case_sensitive=False,
        ),
    )
    def cli(method):
        click.echo(method)

    result = runner.invoke(cli, ["--METHOD=snake_case"])
    assert not result.exception, result.output
    assert result.output == "snake_case\n"

    # Even though it's case sensitive, the choice's original value is preserved
    result = runner.invoke(cli, ["--method=pascalcase"])
    assert not result.exception, result.output
    assert result.output == "PascalCase\n"

    result = runner.invoke(cli, ["--method=meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--method': 'meh' is not one of "
        "'screaming_snake_case', 'snake_case', 'pascalcase', 'kebab-case'."
    ) in result.output

    result = runner.invoke(cli, ["--help"])
    assert (
        "--method [screaming_snake_case|snake_case|pascalcase|kebab-case]"
        in result.output
    )


def test_command_normalization(runner):
    @click.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    def foo():
        click.echo("here!")

    result = runner.invoke(cli, ["FOO"])
    assert result.output == "here!\n"

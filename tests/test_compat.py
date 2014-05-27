import click


def test_legacy_callbacks(runner):
    def legacy_callback(ctx, value):
        return value.upper()

    @click.command()
    @click.option('--foo', callback=legacy_callback)
    def cli(foo):
        click.echo(foo)

    result = runner.invoke(cli, ['--foo', 'wat'])
    assert result.exit_code == 0
    assert 'WAT' in result.output
    assert 'Invoked legacy parameter callback' in result.output

import click


def test_progressbar_strip_regression(runner, monkeypatch):
    label = '    padded line'

    @click.command()
    def cli():
        with click.progressbar(tuple(range(10)), label=label) as progress:
            for thing in progress:
                pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    assert label in runner.invoke(cli, []).output


def test_secho(runner):
    with runner.isolation() as out:
        click.secho(None, nl=False)
        bytes = out.getvalue()
        assert bytes == b''

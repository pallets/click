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


def test_progressbar_should_not_show_in_non_tty(runner, monkeypatch):
    label = 'progress label'

    @click.command()
    def cli():
        with click.progressbar(range(3), label=label) as progress:
            for thing in progress:
                pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: False)
    output = runner.invoke(cli, []).output
    assert '' == output

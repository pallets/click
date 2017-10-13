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


def test_progressbar_length_hint(runner, monkeypatch):
    class Hinted(object):
        def __init__(self, n):
            self.items = list(range(n))

        def __length_hint__(self):
            return len(self.items)

        def __iter__(self):
            return self

        def __next__(self):
            if self.items:
                return self.items.pop()
            else:
                raise StopIteration

        next = __next__

    @click.command()
    def cli():
        with click.progressbar(Hinted(10), label='test') as progress:
            for thing in progress:
                pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


def test_choices_list_in_prompt(runner, monkeypatch):
    @click.command()
    @click.option('-g', type=click.Choice(['none', 'day', 'week', 'month']),
                  prompt=True)
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option('-g', type=click.Choice(['none', 'day', 'week', 'month']),
                  prompt=True, show_choices=False)
    def cli_without_choices(g):
        pass

    result = runner.invoke(cli_with_choices, [], input='none')
    assert '(none, day, week, month)' in result.output

    result = runner.invoke(cli_without_choices, [], input='none')
    assert '(none, day, week, month)' not in result.output


def test_secho(runner):
    with runner.isolation() as outstreams:
        click.secho(None, nl=False)
        bytes = outstreams[0].getvalue()
        assert bytes == b''

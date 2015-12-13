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

    @click.command()
    def cli():
        with click.progressbar(Hinted(10), label='test') as progress:
            for thing in progress:
                pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None

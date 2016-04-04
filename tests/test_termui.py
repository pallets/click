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


def test_show_default(runner, monkeypatch):
    @click.option('-t', default='hello', prompt=True, show_default=True)
    @click.command()
    def cli():
        pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    assert '[hello]' in runner.invoke(cli, [], input='none').output


def test_do_not_show_default(runner, monkeypatch):
    @click.option('-t', default='hello', prompt=True, show_default=False)
    @click.command()
    def cli():
        pass

    monkeypatch.setattr(click._termui_impl, 'isatty', lambda _: True)
    assert '[hello]' not in runner.invoke(cli, [], input='none').output

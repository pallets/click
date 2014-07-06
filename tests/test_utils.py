import os
import sys
import click
import click._termui_impl


def test_echo(runner):
    with runner.isolation() as out:
        click.echo(u'\N{SNOWMAN}')
        click.echo(b'\x44\x44')
        click.echo(42, nl=False)
        click.echo(b'a', nl=False)
        click.echo('\x1b[31mx\x1b[39m', nl=False)
        bytes = out.getvalue()
        assert bytes == b'\xe2\x98\x83\nDD\n42ax'

    # If we are in Python 2, we expect that writing bytes into a string io
    # does not do anything crazy.  In Python 3
    if sys.version_info[0] == 2:
        import StringIO
        sys.stdout = x = StringIO.StringIO()
        try:
            click.echo('\xf6')
        finally:
            sys.stdout = sys.__stdout__
        assert x.getvalue() == '\xf6\n'

    # And in any case, if wrapped, we expect bytes to survive.
    @click.command()
    def cli():
        click.echo(b'\xf6')
    result = runner.invoke(cli, [])
    assert result.output_bytes == b'\xf6\n'

    # Ensure we do not strip for bytes.
    with runner.isolation() as out:
        click.echo(bytearray(b'\x1b[31mx\x1b[39m'), nl=False)
        assert out.getvalue() == b'\x1b[31mx\x1b[39m'


def test_styling():
    examples = [
        ('x', dict(fg='black'), '\x1b[30mx\x1b[0m'),
        ('x', dict(fg='red'), '\x1b[31mx\x1b[0m'),
        ('x', dict(fg='green'), '\x1b[32mx\x1b[0m'),
        ('x', dict(fg='yellow'), '\x1b[33mx\x1b[0m'),
        ('x', dict(fg='blue'), '\x1b[34mx\x1b[0m'),
        ('x', dict(fg='magenta'), '\x1b[35mx\x1b[0m'),
        ('x', dict(fg='cyan'), '\x1b[36mx\x1b[0m'),
        ('x', dict(fg='white'), '\x1b[37mx\x1b[0m'),
        ('x', dict(bg='black'), '\x1b[40mx\x1b[0m'),
        ('x', dict(bg='red'), '\x1b[41mx\x1b[0m'),
        ('x', dict(bg='green'), '\x1b[42mx\x1b[0m'),
        ('x', dict(bg='yellow'), '\x1b[43mx\x1b[0m'),
        ('x', dict(bg='blue'), '\x1b[44mx\x1b[0m'),
        ('x', dict(bg='magenta'), '\x1b[45mx\x1b[0m'),
        ('x', dict(bg='cyan'), '\x1b[46mx\x1b[0m'),
        ('x', dict(bg='white'), '\x1b[47mx\x1b[0m'),
        ('foo bar', dict(blink=True), '\x1b[5mfoo bar\x1b[0m'),
        ('foo bar', dict(underline=True), '\x1b[4mfoo bar\x1b[0m'),
        ('foo bar', dict(bold=True), '\x1b[1mfoo bar\x1b[0m'),
        ('foo bar', dict(dim=True), '\x1b[2mfoo bar\x1b[0m'),
    ]
    for text, styles, ref in examples:
        assert click.style(text, **styles) == ref
        assert click.unstyle(ref) == text


def test_echo_via_pager(monkeypatch, capfd):
    monkeypatch.setitem(os.environ, 'PAGER', 'cat')
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda x: True)
    click.echo_via_pager('haha')
    out, err = capfd.readouterr()
    assert out == 'haha\n'


def test_filename_formatting():
    assert click.format_filename(b'foo.txt') == 'foo.txt'
    assert click.format_filename(b'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt', shorten=True) == 'foo.txt'
    assert click.format_filename(b'/x/foo\xff.txt', shorten=True) \
        == u'foo\ufffd.txt'


def test_prompts(runner):
    @click.command()
    def test():
        if click.confirm('Foo'):
            click.echo('yes!')
        else:
            click.echo('no :(')

    result = runner.invoke(test, input='y\n')
    assert not result.exception
    assert result.output == 'Foo [y/N]: y\nyes!\n'

    result = runner.invoke(test, input='\n')
    assert not result.exception
    assert result.output == 'Foo [y/N]: \nno :(\n'

    result = runner.invoke(test, input='n\n')
    assert not result.exception
    assert result.output == 'Foo [y/N]: n\nno :(\n'

    @click.command()
    def test_no():
        if click.confirm('Foo', default=True):
            click.echo('yes!')
        else:
            click.echo('no :(')

    result = runner.invoke(test_no, input='y\n')
    assert not result.exception
    assert result.output == 'Foo [Y/n]: y\nyes!\n'

    result = runner.invoke(test_no, input='\n')
    assert not result.exception
    assert result.output == 'Foo [Y/n]: \nyes!\n'

    result = runner.invoke(test_no, input='n\n')
    assert not result.exception
    assert result.output == 'Foo [Y/n]: n\nno :(\n'

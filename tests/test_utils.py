import click


def test_echo(runner):
    with runner.isolation() as out:
        click.echo(u'\N{SNOWMAN}')
        click.echo(b'\x44\x44')
        click.echo(42, nl=False)
        click.echo(b'a', nl=False)
        click.echo('\x1b[31mx\x1b[39m', nl=False)
        bytes = out.getvalue()
        assert bytes == b'\xe2\x98\x83\nDD\n42ax'


def test_filename_formatting():
    assert click.format_filename(b'foo.txt') == 'foo.txt'
    assert click.format_filename(b'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt', shorten=True) == 'foo.txt'
    assert click.format_filename(b'/x/foo\xff.txt', shorten=True) \
        == u'foo\ufffd.txt'

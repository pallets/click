import sys
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

    # If we are on python 2 we expect that writing bytes into a string io
    # does not do anything crazy.  On Python 3
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
        assert out.getvalue() == '\x1b[31mx\x1b[39m'


def test_filename_formatting():
    assert click.format_filename(b'foo.txt') == 'foo.txt'
    assert click.format_filename(b'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt', shorten=True) == 'foo.txt'
    assert click.format_filename(b'/x/foo\xff.txt', shorten=True) \
        == u'foo\ufffd.txt'

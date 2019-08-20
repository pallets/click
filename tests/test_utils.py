import os
import sys

import pytest

import click
import click.utils
import click._termui_impl
from click._compat import WIN, PY2


def test_echo(runner):
    with runner.isolation() as outstreams:
        click.echo(u'\N{SNOWMAN}')
        click.echo(b'\x44\x44')
        click.echo(42, nl=False)
        click.echo(b'a', nl=False)
        click.echo('\x1b[31mx\x1b[39m', nl=False)
        bytes = outstreams[0].getvalue().replace(b'\r\n', b'\n')
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
    assert result.stdout_bytes == b'\xf6\n'

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        click.echo(bytearray(b'\x1b[31mx\x1b[39m'), nl=False)
        assert outstreams[0].getvalue() == b'\x1b[31mx\x1b[39m'


def test_echo_custom_file():
    import io
    f = io.StringIO()
    click.echo(u'hello', file=f)
    assert f.getvalue() == u'hello\n'


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


def test_filename_formatting():
    assert click.format_filename(b'foo.txt') == 'foo.txt'
    assert click.format_filename(b'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt', shorten=True) == 'foo.txt'

    # filesystem encoding on windows permits this.
    if not WIN:
        assert click.format_filename(b'/x/foo\xff.txt', shorten=True) \
            == u'foo\ufffd.txt'


def test_prompts(runner, monkeypatch):
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

    @click.command()
    @click.argument("arg1", required=True)
    def test_args_confirm(arg1):
        if click.confirm('Foo', default=True):
            click.echo(arg1)
        else:
            click.echo('no :(')

    result = runner.invoke(test_args_confirm, input='y\n', args=["test_age"])
    assert not result.exception
    assert result.output == 'Foo [Y/n]: y\ntest_age\n'

    result = runner.invoke(test_args_confirm, input='\n', args=["test_age"])
    assert not result.exception
    assert result.output == 'Foo [Y/n]: \ntest_age\n'

    result = runner.invoke(test_args_confirm, input='n\n', args=["test_age"])
    assert not result.exception
    assert result.output == 'Foo [Y/n]: n\nno :(\n'

    @click.command()
    @click.argument("arg1", required=True)
    def test_args_pipe_confirm(arg1):
        if click.confirm('Foo', default=True):
            click.echo(arg1)
        else:
            click.echo('no :(')

    class MockedStream(object):
        def __init__(self, *args, **kwargs):
            pass

        @staticmethod
        def read(*args, **kwargs):
            return MockedStream.stdin

        @staticmethod
        def prompt(*args, **kwargs):
            click.echo(MockedStream.user_prompt, nl=False)
            return MockedStream.user_prompt

    MockedStream.stdin = "test_age"
    MockedStream.user_prompt = "y\n"
    monkeypatch.setattr('stat.S_ISFIFO', lambda x: True)
    monkeypatch.setattr("click.core.get_text_stream", MockedStream)

    result = runner.invoke(test_args_confirm, prompt_func=MockedStream.prompt)
    assert not result.exception
    assert result.output == 'Foo [Y/n]: y\ntest_age\n'

    MockedStream.user_prompt = "n\n"
    result = runner.invoke(test_args_confirm, prompt_func=MockedStream.prompt)
    assert not result.exception
    assert result.output == 'Foo [Y/n]: n\nno :(\n'


@pytest.mark.skipif(WIN, reason='Different behavior on windows.')
def test_prompts_abort(monkeypatch, capsys):
    def f(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr('click.termui.hidden_prompt_func', f)

    try:
        click.prompt('Password', hide_input=True)
    except click.Abort:
        click.echo('Screw you.')

    out, err = capsys.readouterr()
    assert out == 'Password: \nScrew you.\n'


def _test_gen_func():
    yield 'a'
    yield 'b'
    yield 'c'
    yield 'abc'


@pytest.mark.skipif(WIN, reason='Different behavior on windows.')
@pytest.mark.parametrize('cat', ['cat', 'cat ', 'cat '])
@pytest.mark.parametrize('test', [
    # We need lambda here, because pytest will
    # reuse the parameters, and then the generators
    # are already used and will not yield anymore
    ('just text\n', lambda: 'just text'),
    ('iterable\n', lambda: ["itera", "ble"]),
    ('abcabc\n', lambda: _test_gen_func),
    ('abcabc\n', lambda: _test_gen_func()),
    ('012345\n', lambda: (c for c in range(6))),
])
def test_echo_via_pager(monkeypatch, capfd, cat, test):
    monkeypatch.setitem(os.environ, 'PAGER', cat)
    monkeypatch.setattr(click._termui_impl, 'isatty', lambda x: True)

    expected_output = test[0]
    test_input = test[1]()

    click.echo_via_pager(test_input)

    out, err = capfd.readouterr()
    assert out == expected_output


@pytest.mark.skipif(WIN, reason='Test does not make sense on Windows.')
def test_echo_color_flag(monkeypatch, capfd):
    isatty = True
    monkeypatch.setattr(click._compat, 'isatty', lambda x: isatty)

    text = 'foo'
    styled_text = click.style(text, fg='red')
    assert styled_text == '\x1b[31mfoo\x1b[0m'

    click.echo(styled_text, color=False)
    out, err = capfd.readouterr()
    assert out == text + '\n'

    click.echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == styled_text + '\n'

    isatty = True
    click.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == styled_text + '\n'

    isatty = False
    click.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == text + '\n'


@pytest.mark.skipif(WIN, reason='Test too complex to make work windows.')
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        if sys.version_info[0] == 2:
            from StringIO import StringIO
        else:
            from io import StringIO
        monkeypatch.setattr(sys, 'stdin', StringIO(text))

    click.echo('Echo to standard output')
    out, err = capfd.readouterr()
    assert out == 'Echo to standard output\n'
    assert err == ''

    click.echo('Echo to standard error', err=True)
    out, err = capfd.readouterr()
    assert out == ''
    assert err == 'Echo to standard error\n'

    emulate_input('asdlkj\n')
    click.prompt('Prompt to stdin')
    out, err = capfd.readouterr()
    assert out == 'Prompt to stdin: '
    assert err == ''

    emulate_input('asdlkj\n')
    click.prompt('Prompt to stderr', err=True)
    out, err = capfd.readouterr()
    assert out == ''
    assert err == 'Prompt to stderr: '

    emulate_input('y\n')
    click.confirm('Prompt to stdin')
    out, err = capfd.readouterr()
    assert out == 'Prompt to stdin [y/N]: '
    assert err == ''

    emulate_input('y\n')
    click.confirm('Prompt to stderr', err=True)
    out, err = capfd.readouterr()
    assert out == ''
    assert err == 'Prompt to stderr [y/N]: '

    monkeypatch.setattr(click.termui, 'isatty', lambda x: True)
    monkeypatch.setattr(click.termui, 'getchar', lambda: ' ')

    click.pause('Pause to stdout')
    out, err = capfd.readouterr()
    assert out == 'Pause to stdout\n'
    assert err == ''

    click.pause('Pause to stderr', err=True)
    out, err = capfd.readouterr()
    assert out == ''
    assert err == 'Pause to stderr\n'


def test_open_file(runner):
    with runner.isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Cool stuff')

        @click.command()
        @click.argument('filename')
        def cli(filename):
            with click.open_file(filename) as f:
                click.echo(f.read())
            click.echo('meep')

        result = runner.invoke(cli, ['hello.txt'])
        assert result.exception is None
        assert result.output == 'Cool stuff\nmeep\n'

        result = runner.invoke(cli, ['-'], input='foobar')
        assert result.exception is None
        assert result.output == 'foobar\nmeep\n'


@pytest.mark.xfail(WIN and not PY2, reason='God knows ...')
def test_iter_keepopenfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir('testdir').join('testfile')
    p.write(os.linesep.join(expected))
    with p.open() as f:
        for e_line, a_line in zip(expected, click.utils.KeepOpenFile(f)):
            assert e_line == a_line.strip()


@pytest.mark.xfail(WIN and not PY2, reason='God knows ...')
def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir('testdir').join('testfile')
    p.write(os.linesep.join(expected))
    with p.open() as f:
        with click.utils.LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf):
                assert e_line == a_line.strip()

import os
import stat
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


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"blink": True}, "\x1b[5mx y\x1b[0m"),
        ({"underline": True}, "\x1b[4mx y\x1b[0m"),
        ({"bold": True}, "\x1b[1mx y\x1b[0m"),
        ({"dim": True}, "\x1b[2mx y\x1b[0m"),
    ],
)
def test_styling(styles, ref):
    assert click.style("x y", **styles) == ref
    assert click.unstyle(ref) == "x y"


@pytest.mark.parametrize(
    ("text", "expect"),
    [
        ("\x1b[?25lx y\x1b[?25h", "x y"),
    ]
)
def test_unstyle_other_ansi(text, expect):
    assert click.unstyle(text) == expect



def test_filename_formatting():
    assert click.format_filename(b'foo.txt') == 'foo.txt'
    assert click.format_filename(b'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt') == '/x/foo.txt'
    assert click.format_filename(u'/x/foo.txt', shorten=True) == 'foo.txt'

    # filesystem encoding on windows permits this.
    if not WIN:
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

        @click.command()
        @click.argument('filename')
        def cli_ignore_errors(filename):
            with click.open_file(filename, errors="ignore") as f:
                click.echo(f.read())
            click.echo('meep')

        result = runner.invoke(cli, ['hello.txt'])
        assert result.exception is None
        assert result.output == 'Cool stuff\nmeep\n'

        result = runner.invoke(cli, ['-'], input='foobar')
        assert result.exception is None
        assert result.output == 'foobar\nmeep\n'

        # Test that invalid unicode does not throw an exception when we ignore errors,
        # but does throw an exception when we don't
        random_input = os.urandom(64)
        result = runner.invoke(cli_ignore_errors, ['-'], input=random_input)
        assert result.exception is None

        result = runner.invoke(cli, ['-'], input=random_input)
        assert isinstance(result.exception, UnicodeDecodeError)


def test_click_open_file_respects_ignore(runner):
    file_name = "hello_world.txt"

    with runner.isolated_filesystem():
        with open(file_name, "w") as f:
            f.write("Hello world!")

        click_wrapper = click.utils.open_file(file_name, encoding="UTF-8", errors="ignore")
        assert click_wrapper.errors == "ignore"


@pytest.mark.parametrize("ignore", [
    True,
    False
])
def test_click_open_file_ignore_invalid_utf8(ignore, runner):
    file_name = "invalid_utf8.txt"

    with runner.isolated_filesystem():
        with open(file_name, "wb") as f:
            f.write(b'\xe2\x28\xa1')

        open_kwargs = {"encoding": "UTF-8"}

        if ignore:
            # Here we ignore invalid UTF-8, so we should not throw an exception
            open_kwargs["errors"] = "ignore"
            click.utils.open_file(file_name, **open_kwargs).read()
        else:
            # Here we are not ignoring invalid UTF-8, so we expect a UnicodeDecodeError
            with pytest.raises(UnicodeDecodeError):
                click.utils.open_file(file_name, **open_kwargs).read()


def test_click_open_file_ignore_no_encoding_provided(runner):
    file_name = "random_input.bin"

    with runner.isolated_filesystem():
        with open(file_name, "wb") as f:
            f.write(os.urandom(64))

        click.utils.open_file(file_name, errors="ignore").read()


@pytest.mark.skipif(WIN, reason='os.chmod() is not fully supported on Windows.')
@pytest.mark.parametrize('permissions', [
    0o400,
    0o444,
    0o600,
    0o644,
 ])
def test_open_file_atomic_permissions_existing_file(runner, permissions):
    with runner.isolated_filesystem():
        with open('existing.txt', 'w') as f:
            f.write('content')
        os.chmod('existing.txt', permissions)

        @click.command()
        @click.argument('filename')
        def cli(filename):
           click.open_file(filename, 'w', atomic=True).close()

        result = runner.invoke(cli, ['existing.txt'])
        assert result.exception is None
        assert stat.S_IMODE(os.stat('existing.txt').st_mode) == permissions


@pytest.mark.skipif(WIN, reason='os.stat() is not fully supported on Windows.')
def test_open_file_atomic_permissions_new_file(runner):
    with runner.isolated_filesystem():
        @click.command()
        @click.argument('filename')
        def cli(filename):
            click.open_file(filename, 'w', atomic=True).close()

        # Create a test file to get the expected permissions for new files
        # according to the current umask.
        with open('test.txt', 'w'):
            pass
        permissions = stat.S_IMODE(os.stat('test.txt').st_mode)

        result = runner.invoke(cli, ['new.txt'])
        assert result.exception is None
        assert stat.S_IMODE(os.stat('new.txt').st_mode) == permissions


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

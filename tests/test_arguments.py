# -*- coding: utf-8 -*-
import click


def test_nargs_star(runner):
    @click.command()
    @click.argument('src', nargs=-1)
    @click.argument('dst')
    def copy(src, dst):
        click.echo('src=%s' % '|'.join(src))
        click.echo('dst=%s' % dst)

    result = runner.invoke(copy, ['foo.txt', 'bar.txt', 'dir'])
    assert not result.exception
    assert result.output.splitlines() == [
        'src=foo.txt|bar.txt',
        'dst=dir',
    ]


def test_nargs_tup(runner):
    @click.command()
    @click.argument('name', nargs=1)
    @click.argument('point', nargs=2, type=click.INT)
    def copy(name, point):
        click.echo('name=%s' % name)
        click.echo('point=%d/%d' % point)

    result = runner.invoke(copy, ['peter', '1', '2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'name=peter',
        'point=1/2',
    ]


def test_nargs_err(runner):
    @click.command()
    @click.argument('x')
    def copy(x):
        click.echo(x)

    result = runner.invoke(copy, ['foo'])
    assert not result.exception
    assert result.output == 'foo\n'

    result = runner.invoke(copy, ['foo', 'bar'])
    assert result.exit_code == 2
    assert 'Got unexpected extra argument (bar)' in result.output


def test_file_args(runner):
    @click.command()
    @click.argument('input', type=click.File('rb'))
    @click.argument('output', type=click.File('wb'))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

    with runner.isolated_filesystem():
        result = runner.invoke(inout, ['-', 'hello.txt'], input='Hey!')
        assert result.output == ''
        assert result.exit_code == 0
        with open('hello.txt', 'rb') as f:
            assert f.read() == b'Hey!'

        result = runner.invoke(inout, ['hello.txt', '-'])
        assert result.output == 'Hey!'
        assert result.exit_code == 0


def test_stdout_default(runner):
    @click.command()
    @click.argument('output', type=click.File('w'), default='-')
    def inout(output):
        output.write('Foo bar baz\n')
        output.flush()

    result = runner.invoke(inout, [])
    assert not result.exception
    assert result.output == 'Foo bar baz\n'


def test_nargs_envvar(runner):
    @click.command()
    @click.option('--arg', nargs=-1)
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], auto_envvar_prefix='TEST',
                           env={'TEST_ARG': 'foo bar'})
    assert not result.exception
    assert result.output == 'foo|bar\n'

    @click.command()
    @click.option('--arg', envvar='X', nargs=-1)
    def cmd(arg):
        click.echo('|'.join(arg))

    result = runner.invoke(cmd, [], env={'X': 'foo bar'})
    assert not result.exception
    assert result.output == 'foo|bar\n'

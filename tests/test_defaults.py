import click


def test_basic_defaults(runner):
    @click.command()
    @click.option("--foo", default=42, type=click.FLOAT)
    def cli(foo):
        assert isinstance(foo, float)
        click.echo(f"FOO:[{foo}]")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "FOO:[42.0]" in result.output


def test_multiple_defaults(runner):
    @click.command()
    @click.option("--foo", default=[23, 42], type=click.FLOAT, multiple=True)
    def cli(foo):
        for item in foo:
            assert isinstance(item, float)
            click.echo(item)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["23.0", "42.0"]


def test_nargs_plus_multiple(runner):
    @click.command()
    @click.option(
        "--arg", default=((1, 2), (3, 4)), nargs=2, multiple=True, type=click.INT
    )
    def cli(arg):
        for a, b in arg:
            click.echo(f"<{a:d}|{b:d}>")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["<1|2>", "<3|4>"]


def test_multiple_flag_default(runner):
    """Default default for flags when multiple=True should be empty tuple."""

    @click.command
    # flag due to secondary token
    @click.option("-y/-n", multiple=True)
    # flag due to is_flag
    @click.option("-f", is_flag=True, multiple=True)
    # flag due to flag_value
    @click.option("-v", "v", flag_value=1, multiple=True)
    @click.option("-q", "v", flag_value=-1, multiple=True)
    def cli(y, f, v):
        return y, f, v

    result = runner.invoke(cli, standalone_mode=False)
    assert result.return_value == ((), (), ())

    result = runner.invoke(cli, ["-y", "-n", "-f", "-v", "-q"], standalone_mode=False)
    assert result.return_value == ((True, False), (True,), (1, -1))


def test_flag_default_map(runner):
    """test flag with default map"""

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name/--no-name", is_flag=True, show_default=True, help="name flag")
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ["foo"])
    assert "False" in result.output

    result = runner.invoke(cli, ["foo", "--help"])
    assert "default: no-name" in result.output

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": True}})
    assert "True" in result.output

    result = runner.invoke(cli, ["foo", "--help"], default_map={"foo": {"name": True}})
    assert "default: name" in result.output


def test_shared_param_prefers_first_default(runner):
    """test that the first default is chosen when multiple flags share a param name"""

    @click.command
    @click.option("--red", "color", flag_value="red")
    @click.option("--green", "color", flag_value="green", default=True)
    def prefers_green(color):
        click.echo(color)

    @click.command
    @click.option("--red", "color", flag_value="red", default=True)
    @click.option("--green", "color", flag_value="green")
    def prefers_red(color):
        click.echo(color)

    result = runner.invoke(prefers_green, [])
    assert "green" in result.output
    result = runner.invoke(prefers_green, ["--red"])
    assert "red" in result.output

    result = runner.invoke(prefers_red, [])
    assert "red" in result.output
    result = runner.invoke(prefers_red, ["--green"])
    assert "green" in result.output


def test_lookup_default_returns_none_not_sentinel(runner):
    """Test that lookup_default returns None when parameter not in default_map.

    Regression test for issue #3145.
    """

    @click.command()
    @click.option("--email")
    @click.pass_context
    def cmd(ctx, email):
        # When key not in default_map, lookup_default should return None
        result = ctx.lookup_default("nonexistent")
        assert result is None, f"Expected None, got {result!r}"
        click.echo("OK")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "OK" in result.output


def test_lookup_default_returns_none_with_empty_default_map(runner):
    """Test that lookup_default returns None even when default_map exists but key missing."""

    @click.command()
    @click.option("--name", default="test")
    @click.pass_context
    def cmd(ctx, name):
        # Set default_map but query for nonexistent key
        ctx.default_map = {"other_param": "value"}
        result = ctx.lookup_default("missing_key")
        assert result is None, f"Expected None, got {result!r}"
        click.echo("OK")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "OK" in result.output


def test_lookup_default_still_returns_actual_defaults(runner):
    """Test that lookup_default still returns actual values from default_map."""

    @click.command()
    @click.option("--name")
    @click.pass_context
    def cmd(ctx, name):
        ctx.default_map = {"email": "test@example.com"}
        # Should return the actual default when present
        result = ctx.lookup_default("email")
        assert result == "test@example.com"
        click.echo("OK")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "OK" in result.output

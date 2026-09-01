import itertools
import sys
import unicodedata
from unittest import mock

import pytest

import click
from click._utils import UNSET

# See the note beside the same constant in `test_options.py`: `os.environ`
# upper-cases its keys on Windows, so a variable answers to every spelling of
# its name there and to exactly one everywhere else.
ENV_NAMES_ARE_CASE_INSENSITIVE = sys.platform == "win32"


def test_nargs_star(runner):
    @click.command()
    @click.argument("src", nargs=-1)
    @click.argument("dst")
    def copy(src, dst):
        click.echo(f"src={'|'.join(src)}")
        click.echo(f"dst={dst}")

    result = runner.invoke(copy, ["foo.txt", "bar.txt", "dir"])
    assert not result.exception
    assert result.output.splitlines() == ["src=foo.txt|bar.txt", "dst=dir"]


def test_nargs_tup(runner):
    @click.command()
    @click.argument("name", nargs=1)
    @click.argument("point", nargs=2, type=click.INT)
    def copy(name, point):
        click.echo(f"name={name}")
        x, y = point
        click.echo(f"point={x}/{y}")

    result = runner.invoke(copy, ["peter", "1", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter", "point=1/2"]


@pytest.mark.parametrize(
    "opts",
    [
        dict(type=(str, int)),
        dict(type=click.Tuple([str, int])),
        dict(nargs=2, type=click.Tuple([str, int])),
        dict(nargs=2, type=(str, int)),
    ],
)
def test_nargs_tup_composite(runner, opts):
    @click.command()
    @click.argument("item", **opts)
    def copy(item):
        name, id = item
        click.echo(f"name={name} id={id:d}")

    result = runner.invoke(copy, ["peter", "1"])
    assert result.exception is None
    assert result.output.splitlines() == ["name=peter id=1"]


def test_nargs_mismatch_with_tuple_type():
    with pytest.raises(ValueError, match="nargs.*must be 2.*but it was 3"):

        @click.command()
        @click.argument("test", type=(str, int), nargs=3)
        def cli(_):
            pass


def test_nargs_err(runner):
    @click.command()
    @click.argument("x")
    def copy(x):
        click.echo(x)

    result = runner.invoke(copy, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(copy, ["foo", "bar"])
    assert result.exit_code == 2
    assert "Got unexpected extra argument (bar)" in result.output


@pytest.mark.parametrize(
    ("decl", "expect"),
    [
        ("src", "src"),
        ("foo-bar", "foo_bar"),
        ("FOO-BAR", "foo_bar"),
        ("Foo_Bar", "foo_bar"),
        ("foo__bar", "foo__bar"),
        ("_foo", "_foo"),
        ("__foo", "__foo"),
    ],
)
def test_argument_names(runner, decl, expect):
    @click.command()
    @click.argument(decl)
    def cmd(**kwargs):
        click.echo(kwargs[expect])

    assert cmd.params[0].name == expect

    result = runner.invoke(cmd, ["value"])
    assert not result.exception
    assert result.output == "value\n"


def test_argument_normalizes_an_identifier_decl():
    """An argument declaration is normalized even when already an identifier.

    This is the one way the two kinds still differ. An option takes several
    declarations, so one of them that is already an identifier is read as an
    explicit name and kept verbatim. An argument takes exactly one, which has
    to serve as both the metavar source and the name, so it is always
    transformed.
    """
    assert click.Argument(["Foo_Bar"]).name == "foo_bar"
    assert click.Option(["--x", "Foo_Bar"]).name == "Foo_Bar"


# Each kind, paired with the shape its declaration takes. An option carries the
# ``--`` prefix that its transform strips; an argument takes its declaration
# whole. A test parametrized over this asserts one rule for both kinds.
PARAM_KINDS = [
    pytest.param(click.Argument, "{decl}", id="argument"),
    pytest.param(click.Option, "--{decl}", id="option"),
]

# Declarations that between them cover every shape the naming transform has to
# settle: empty, bare prefixes, a leading digit, a dot, a space, and the two
# forms that do name something.
NAME_SWEEP_DECLS = [
    "",
    "-",
    "--",
    "---",
    "0",
    "--0",
    "0-file",
    "--0-file",
    "foo.bar",
    "--foo.bar",
    "foo bar",
    "x",
    "--x",
    "X_Y",
    "--X-Y",
]


@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize("expose_value", [True, False])
def test_parameter_name_is_always_an_identifier(count, expose_value):
    """No declaration builds a parameter whose name is not a Python identifier.

    ``_resolve_name`` is the one place a name is settled, and it refuses
    everything else, so every reader downstream may treat ``Parameter.name`` as
    a usable identifier.
    """
    built = 0

    for decls in itertools.product(NAME_SWEEP_DECLS, repeat=count):
        for cls in (click.Option, click.Argument):
            try:
                param = cls(list(decls), expose_value=expose_value)
            except (TypeError, ValueError):
                continue

            built += 1
            assert param.name.isidentifier(), (
                f"{cls.__name__}({list(decls)!r}, expose_value={expose_value})"
                f" named its parameter {param.name!r}"
            )

    assert built, "the sweep built no parameter, so it proves nothing"


def test_argument_requires_its_one_declaration():
    """An argument with no declaration is refused, whatever ``expose_value`` says.

    It used to build a required positional named ``""``: nothing rendered for it
    in the usage line, a missing value was reported as ``Missing argument ''``,
    and a second one tripped the duplicate-name warning in
    :meth:`Command.get_params`.
    """
    with pytest.raises(TypeError, match="exactly one parameter declaration"):
        click.Argument([])

    with pytest.raises(TypeError, match="exactly one parameter declaration"):
        click.Argument([], expose_value=False)


def test_argument_name_check_applies_when_not_exposed():
    """An unexposed argument is held to the check too.

    The name is also the key the parser stores the value under, so an argument
    that gave it up would share that key with the next one. The option half is
    ``test_option_name_check_applies_when_not_exposed``.
    """
    with pytest.raises(TypeError, match="Could not determine name"):
        click.Argument(["0foo"], expose_value=False)


def test_argument_metavar_renders_what_a_declaration_may_not(runner):
    """``metavar`` carries a display the declaration is no longer allowed to.

    An argument takes exactly one declaration and has no explicit-name channel,
    so a display such as ``0FOO`` is reached by naming the parameter separately
    and passing the display as ``metavar``.
    """
    seen = []

    def record(ctx, param, value):
        seen.append(value)

    @click.command()
    @click.argument("zero_foo", expose_value=False, callback=record, metavar="0FOO")
    def cmd(**kwargs):
        click.echo(repr(kwargs))

    assert cmd.params[0].name == "zero_foo"

    result = runner.invoke(cmd, ["value"])
    assert not result.exception
    assert result.output == "{}\n"
    assert seen == ["value"]

    result = runner.invoke(cmd, ["--help"])
    assert "0FOO" in result.output


@pytest.mark.parametrize(("cls", "form"), PARAM_KINDS)
@pytest.mark.parametrize(
    ("decl", "expect"),
    [
        # Greek capital omega transforms to its lowercase form.
        pytest.param("Ω", "ω", id="omega"),
        # Latin capital I with dot above transforms to two code points: the
        # transform grows the name.
        pytest.param("İ", "i\N{COMBINING DOT ABOVE}", id="dotted-capital-i"),
        # A trailing sigma transforms to its context-sensitive final form.
        pytest.param("ΟΔΟΣ", "οδος", id="final-sigma"),
        # Capital sharp s transforms to the letter whose upper case is "SS".
        pytest.param("ẞ", "ß", id="capital-sharp-s"),
        # The Kelvin sign transforms to a plain ASCII k.
        pytest.param("\N{KELVIN SIGN}", "k", id="kelvin-sign"),
        # A digit outside ASCII is kept wherever it sits but the leading one.
        pytest.param("foo-٣", "foo_٣", id="arabic-indic-digit"),
    ],
)
def test_parameter_name_unicode_case_transform(cls, form, decl, expect):
    """``str.lower()`` is neither one-to-one nor length-preserving.

    Both kinds run the same transform, so every row holds for either.
    """
    assert cls([form.format(decl=decl)]).name == expect


@pytest.mark.parametrize(("cls", "form"), PARAM_KINDS)
@pytest.mark.parametrize(
    "decl",
    [
        pytest.param("0foo", id="leading-digit"),
        pytest.param("0", id="digit-only"),
        pytest.param("foo.bar", id="dot"),
        pytest.param("foo bar", id="space"),
        pytest.param("\u0663foo", id="leading-arabic-indic-digit"),
        # Separators that read as a hyphen but are not the one replaced.
        pytest.param("foo\N{NON-BREAKING HYPHEN}bar", id="non-breaking-hyphen"),
        pytest.param("foo\u2013bar", id="en-dash"),
        pytest.param("foo\u2212bar", id="minus-sign"),
        # Characters that occupy no width at all.
        pytest.param("a\N{ZERO WIDTH SPACE}b", id="zero-width-space"),
        pytest.param("a\N{SOFT HYPHEN}b", id="soft-hyphen"),
        pytest.param("a\N{RIGHT-TO-LEFT OVERRIDE}b", id="right-to-left-override"),
        # Even nothing at all, which reaches an option as a bare ``--``.
        pytest.param("", id="empty"),
    ],
)
def test_parameter_name_must_be_an_identifier(cls, form, decl):
    """Neither kind accepts a declaration that names no Python identifier.

    Both derive a name the same way and hold it to the same check, so a
    declaration is refused whichever one it is written as. The one refused
    shape an argument has no equivalent of is in
    ``test_option_name_must_be_an_identifier``.
    """
    with pytest.raises(TypeError, match="Could not determine name"):
        cls([form.format(decl=decl)])


@pytest.mark.parametrize(("cls", "form"), PARAM_KINDS)
@pytest.mark.parametrize(
    "char",
    [
        pytest.param("\N{ZERO WIDTH JOINER}", id="zero-width-joiner"),
        pytest.param("\N{ZERO WIDTH NON-JOINER}", id="zero-width-non-joiner"),
    ],
)
def test_parameter_name_identifier_check_follows_the_unicode_table(cls, form, char):
    """Two zero-width characters answer this check differently per Python.

    Unicode 15.1 added the joiner and the non-joiner to the characters an
    identifier may continue with, and Python 3.13 is the first release to carry
    that table. So one declaration is refused up to Python 3.12 and names a
    parameter from 3.13 on, with nothing on screen to separate it from ``ab``.
    """
    name = f"a{char}b"
    assert name.isidentifier() == (sys.version_info >= (3, 13))
    decl = form.format(decl=name)

    if not name.isidentifier():
        with pytest.raises(TypeError, match="Could not determine name"):
            cls([decl])
        return

    assert cls([decl]).name == name


@pytest.mark.parametrize(
    ("decorator", "decl", "argv"),
    [
        pytest.param(click.argument, "ﬁ", ["value"], id="argument"),
        pytest.param(click.option, "--ﬁ", ["--ﬁ", "value"], id="option"),
    ],
)
def test_parameter_name_is_not_nfkc_normalized(runner, decorator, decl, argv):
    """``str.isidentifier()`` is not the test for "can be a parameter name".

    Python normalizes an identifier written in source to NFKC, so the ligature
    "fi" compiles to the two letters. ``_parse_decls`` runs no normalization,
    so the name keeps the ligature and only ``**kwargs`` can carry it.
    """

    @click.command()
    @decorator(decl)
    def cmd(**kwargs):
        click.echo(repr(kwargs))

    name = cmd.params[0].name
    assert name == "ﬁ"
    assert name.isidentifier()
    assert unicodedata.normalize("NFKC", name) == "fi"

    result = runner.invoke(cmd, argv)
    assert not result.exception
    assert result.output == "{'ﬁ': 'value'}\n"


def test_argument_name_keeps_its_normalization_form(runner):
    """A composed and a decomposed declaration are two distinct arguments.

    Both render as ``café`` and both are valid identifiers, so the pair
    coexists on one command with nothing on screen to tell them apart.
    """
    decomposed = "cafe\N{COMBINING ACUTE ACCENT}"
    composed = unicodedata.normalize("NFC", decomposed)

    @click.command()
    @click.argument(composed)
    @click.argument(decomposed)
    def cmd(**kwargs):
        click.echo(repr(sorted(kwargs)))

    assert [p.name for p in cmd.params] == [composed, decomposed]

    result = runner.invoke(cmd, ["one", "two"])
    assert not result.exception
    assert result.output == f"['{decomposed}', '{composed}']\n"


def test_argument_name_case_transform_can_collide(runner):
    """Two declarations that differ can transform to one name, and that warns.

    An option pair transforming to one name stays silent, since options may share a
    name on purpose to form a feature switch group. An argument sharing a name
    only ever overwrites, so the check in ``Command.get_params`` fires.
    """

    @click.command()
    @click.argument("Foo-Bar")
    @click.argument("foo_bar")
    def cmd(**kwargs):
        click.echo(repr(kwargs))

    with pytest.warns(UserWarning, match="is used by an argument"):
        result = runner.invoke(cmd, ["one", "two"], catch_exceptions=False)

    assert result.output == "{'foo_bar': 'two'}\n"


def test_argument_name_can_collide_with_an_option(runner):
    """An argument transforming onto an option's name overwrites it, and warns.

    The argument is what the warning names, and the argument is what wins:
    the option's value never reaches the callback.
    """

    @click.command()
    @click.option("--foo-bar")
    @click.argument("Foo-Bar", required=False)
    def cmd(**kwargs):
        click.echo(repr(kwargs))

    assert [p.name for p in cmd.params] == ["foo_bar", "foo_bar"]

    with pytest.warns(UserWarning, match="is used by an argument"):
        result = runner.invoke(
            cmd, ["--foo-bar", "from-option", "from-argument"], catch_exceptions=False
        )

    assert result.output == "{'foo_bar': 'from-argument'}\n"


def test_argument_has_no_auto_envvar(runner):
    """An argument reads only the envvars it names, never a derived one."""

    @click.command()
    @click.argument("Foo-Bar", required=False)
    def cmd(**kwargs):
        click.echo(repr(kwargs))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_FOO_BAR": "foo"}
    )
    assert not result.exception
    assert result.output == "{'foo_bar': None}\n"


@pytest.mark.parametrize(
    ("env", "expect"),
    [
        pytest.param({"ArG": "foo"}, "'foo'", id="exact"),
        pytest.param({"ARG": "foo"}, "None", id="upper"),
        pytest.param({"arg": "foo"}, "None", id="lower"),
    ],
)
def test_argument_explicit_envvar_case_sensitivity(runner, env, expect):
    """An argument matches its named envvar exactly, like an option does.

    And loses the distinction on Windows, like an option does.
    """

    @click.command()
    @click.argument("arg", envvar="ArG", required=False)
    def cmd(arg):
        click.echo(repr(arg))

    result = runner.invoke(cmd, [], env=env)
    assert not result.exception
    if ENV_NAMES_ARE_CASE_INSENSITIVE:
        expect = "'foo'"
    assert result.output == f"{expect}\n"


def test_bytes_args(runner, monkeypatch):
    @click.command()
    @click.argument("arg")
    def from_bytes(arg):
        assert isinstance(arg, str), (
            "UTF-8 encoded argument should be implicitly converted to Unicode"
        )

    # Simulate empty locale environment variables
    monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "utf-8")
    monkeypatch.setattr(sys, "getdefaultencoding", lambda: "utf-8")
    # sys.stdin.encoding is readonly, needs some extra effort to patch.
    stdin = mock.Mock(wraps=sys.stdin)
    stdin.encoding = "utf-8"
    monkeypatch.setattr(sys, "stdin", stdin)

    runner.invoke(
        from_bytes,
        ["Something outside of ASCII range: 林".encode()],
        catch_exceptions=False,
    )


def test_file_args(runner, tmp_path):
    @click.command()
    @click.argument("input", type=click.File("rb"))
    @click.argument("output", type=click.File("wb"))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

    hello = tmp_path / "hello.txt"
    result = runner.invoke(inout, ["-", str(hello)], input="Hey!")
    assert result.output == ""
    assert result.exit_code == 0
    assert hello.read_bytes() == b"Hey!"

    result = runner.invoke(inout, [str(hello), "-"])
    assert result.output == "Hey!"
    assert result.exit_code == 0


def test_path_allow_dash(runner):
    @click.command()
    @click.argument("input", type=click.Path(allow_dash=True))
    def foo(input):
        click.echo(input)

    result = runner.invoke(foo, ["-"])
    assert result.output == "-\n"
    assert result.exit_code == 0


def test_file_atomics(runner, tmp_path):
    @click.command()
    @click.argument("output", type=click.File("wb", atomic=True))
    def inout(output):
        output.write(b"Foo bar baz\n")
        output.flush()
        with open(output.name, "rb") as f:
            old_content = f.read()
            assert old_content == b"OLD\n"

    foo = tmp_path / "foo.txt"
    foo.write_bytes(b"OLD\n")
    result = runner.invoke(inout, [str(foo)], input="Hey!", catch_exceptions=False)
    assert result.output == ""
    assert result.exit_code == 0
    assert foo.read_bytes() == b"Foo bar baz\n"


def test_stdout_default(runner):
    @click.command()
    @click.argument("output", type=click.File("w"), default="-")
    def inout(output):
        output.write("Foo bar baz\n")
        output.flush()

    result = runner.invoke(inout, [])
    assert not result.exception
    assert result.output == "Foo bar baz\n"
    assert result.stdout == "Foo bar baz\n"
    assert not result.stderr


@pytest.mark.parametrize(
    ("nargs", "value", "expect"),
    [
        (2, "", None),
        (2, "a", "Takes 2 values but 1 was given."),
        (2, "a b", ("a", "b")),
        (2, "a b c", "Takes 2 values but 3 were given."),
        (-1, "a b c", ("a", "b", "c")),
        (-1, "", ()),
    ],
)
def test_nargs_envvar(runner, nargs, value, expect):
    if nargs == -1:
        param = click.argument("arg", envvar="X", nargs=nargs)
    else:
        param = click.option("--arg", envvar="X", nargs=nargs)

    @click.command()
    @param
    def cmd(arg):
        return arg

    result = runner.invoke(cmd, env={"X": value}, standalone_mode=False)

    if isinstance(expect, str):
        assert isinstance(result.exception, click.BadParameter)
        assert expect in result.exception.format_message()
    else:
        assert result.return_value == expect


def test_nargs_envvar_only_if_values_empty(runner):
    @click.command()
    @click.argument("arg", envvar="X", nargs=-1)
    def cli(arg):
        return arg

    result = runner.invoke(cli, ["a", "b"], standalone_mode=False)
    assert result.return_value == ("a", "b")

    result = runner.invoke(cli, env={"X": "a"}, standalone_mode=False)
    assert result.return_value == ("a",)


def test_empty_nargs(runner):
    @click.command()
    @click.argument("arg", nargs=-1)
    def cmd(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert result.output == "arg:\n"

    @click.command()
    @click.argument("arg", nargs=-1, required=True)
    def cmd2(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd2, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG...'" in result.output


def test_missing_arg(runner):
    @click.command()
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'." in result.output


@pytest.mark.parametrize(
    ("value", "expect_missing", "processed_value"),
    [
        # Unspecified type of the argument fallback to string, so everything is
        # processed the click.STRING type.
        ("", False, ""),
        ("  ", False, "  "),
        ("foo", False, "foo"),
        ("12", False, "12"),
        (12, False, "12"),
        (12.1, False, "12.1"),
        (list(), False, "[]"),
        (tuple(), False, "()"),
        (set(), False, "set()"),
        (frozenset(), False, "frozenset()"),
        (dict(), False, "{}"),
        # None is a value that is allowed to be processed by a required argument
        # because at this stage, the process_value method happens after the default is
        # applied.
        (None, False, None),
        # An UNSET required argument will raise MissingParameter.
        (UNSET, True, None),
    ],
)
def test_required_argument(value, expect_missing, processed_value):
    """Test how a required argument is processing the provided values."""
    ctx = click.Context(click.Command(""))
    argument = click.Argument(["a"], required=True)

    if expect_missing:
        with pytest.raises(click.MissingParameter) as excinfo:
            argument.process_value(ctx, value)
        assert str(excinfo.value) == "Missing parameter: a"

    else:
        value = argument.process_value(ctx, value)
        assert value == processed_value


def test_implicit_non_required(runner):
    @click.command()
    @click.argument("f", default="test")
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "test\n"


def test_argument_help(runner):
    @click.command()
    @click.argument("name", help="The name to print")
    @click.option("--count", default=1, help="number of greetings")
    def cli(name, count):
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "Positional arguments:" in result.output
    assert "NAME" in result.output
    assert "The name to print" in result.output
    assert "Options:" in result.output
    assert "number of greetings" in result.output
    assert result.output.index("Positional arguments:") < result.output.index(
        "Options:"
    )


def test_argument_help_options_only_no_arguments_section(runner):
    @click.command()
    @click.option("--count", default=1, help="number of greetings")
    def cli(count):
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "Positional arguments:" not in result.output
    assert "Options:" in result.output
    assert "number of greetings" in result.output


def test_argument_help_optional_metavar(runner):
    @click.command()
    @click.argument("name", required=False, default="", help="The name to print")
    def cli(name):
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "[NAME]" in result.output
    assert "The name to print" in result.output


def test_deprecated_usage(runner):
    @click.command()
    @click.argument("f", required=False, deprecated=True)
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "[F!]" in result.output


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, "FOO"),
        ({"required": True}, "FOO"),
        ({"required": False}, "[FOO]"),
        ({"default": "x"}, "[FOO]"),
        ({"nargs": -1}, "[FOO]..."),
        ({"nargs": -1, "required": True}, "FOO..."),
        ({"nargs": 2}, "FOO..."),
        ({"nargs": 2, "required": False}, "[FOO]..."),
    ],
)
def test_argument_metavar_marks_optional(runner, kwargs, expected):
    """An argument is bracketed in the usage line only when it is optional."""

    @click.command()
    @click.argument("foo", **kwargs)
    def cli(foo):
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == f"Usage: cli [OPTIONS] {expected}"


@pytest.mark.parametrize(
    ("deprecated", "expected_label"),
    [(True, "(DEPRECATED)"), ("use g instead", "(DEPRECATED: use g instead)")],
)
def test_deprecated_usage_help_record(runner, deprecated, expected_label):
    @click.command()
    @click.argument("f", required=False, deprecated=deprecated, help="path to the file")
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "Positional arguments:" in result.output
    assert "[F!]" in result.output
    assert f"path to the file {expected_label}" in result.output


def test_deprecated_usage_help_record_without_help(runner):
    @click.command()
    @click.argument("f", required=False, deprecated=True)
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    # Deprecation alone produces a help row with just the deprecation label.
    assert "Positional arguments:" in result.output
    assert "(DEPRECATED)" in result.output


@pytest.mark.parametrize(
    ("deprecated", "expected"),
    [(True, "(DEPRECATED)"), ("USE B INSTEAD", "(DEPRECATED: USE B INSTEAD)")],
)
@pytest.mark.parametrize("help_text", ["", None])
def test_deprecated_empty_help_no_leading_space(help_text, deprecated, expected):
    """An argument with empty or missing help text must not gain a stray leading
    space before the deprecation label.
    """
    arg = click.Argument(["foo"], required=False, help=help_text, deprecated=deprecated)
    ctx = click.Context(click.Command("cli"))
    assert arg.get_help_record(ctx)[1] == expected


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_warning(runner, deprecated):
    @click.command()
    @click.argument(
        "my-argument", required=False, deprecated=deprecated, default="default argument"
    )
    def cli(my_argument: str):
        click.echo(f"{my_argument}")

    # defaults should not give a deprecated warning
    result = runner.invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "is deprecated" not in result.output

    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0, result.output
    assert "argument 'MY_ARGUMENT' is deprecated" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_deprecated_required(runner):
    with pytest.raises(ValueError, match="is deprecated and still required"):
        click.Argument(["a"], required=True, deprecated=True)


def test_eat_options(runner):
    @click.command()
    @click.option("-f")
    @click.argument("files", nargs=-1)
    def cmd(f, files):
        for filename in files:
            click.echo(filename)
        click.echo(f)

    result = runner.invoke(cmd, ["--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", ""]

    result = runner.invoke(cmd, ["-f", "-x", "--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", "-x"]


def test_nargs_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c")
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c"])
    assert result.output.splitlines() == ["('a',)", "b", "c"]


def test_nargs_specified_plus_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c", nargs=2)
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c", "d", "e", "f"])
    assert result.output.splitlines() == ["('a', 'b', 'c')", "d", "('e', 'f')"]


@pytest.mark.parametrize(
    ("argument_params", "args", "expected"),
    [
        # Any iterable with the same number of arguments as nargs is valid.
        [{"nargs": 2, "default": (1, 2)}, [], (1, 2)],
        [{"nargs": 2, "default": (1.1, 2.2)}, [], (1, 2)],
        [{"nargs": 2, "default": ("1", "2")}, [], (1, 2)],
        [{"nargs": 2, "default": (None, None)}, [], (None, None)],
        [{"nargs": 2, "default": [1, 2]}, [], (1, 2)],
        [{"nargs": 2, "default": {1, 2}}, [], (1, 2)],
        [{"nargs": 2, "default": frozenset([1, 2])}, [], (1, 2)],
        [{"nargs": 2, "default": {1: "a", 2: "b"}}, [], (1, 2)],
        # Empty iterable is valid if default is None.
        [{"nargs": 2, "default": None}, [], None],
        # Arguments overrides the default.
        [{"nargs": 2, "default": (1, 2)}, ["3", "4"], (3, 4)],
        # Unbounded arguments are allowed to have a default.
        # See: https://github.com/pallets/click/issues/2164
        [{"nargs": -1, "default": [42]}, [], (42,)],
        [{"nargs": -1, "default": None}, [], ()],
        [{"nargs": -1, "default": {1, 2, 3, 4, 5}}, [], (1, 2, 3, 4, 5)],
    ],
)
def test_good_defaults_for_nargs(runner, argument_params, args, expected):
    """Comprehensive check of default-value processing for arguments with
    ``nargs``.

    .. hint::
        An option-specific equivalent is available in
        ``test_options.py::test_good_defaults_for_multiple``.

        A smoke test covering a single basic case is in
        ``test_defaults.py::test_nargs_plus_multiple``.
    """

    @click.command()
    @click.argument("a", type=int, **argument_params)
    def cmd(a):
        click.echo(repr(a), nl=False)

    result = runner.invoke(cmd, args)
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("default", "message"),
    [
        # Non-iterables defaults.
        ["Yo", "Error: Invalid value for '[A]...': Value must be an iterable."],
        ["", "Error: Invalid value for '[A]...': Value must be an iterable."],
        [True, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [False, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [12, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [7.9, "Error: Invalid value for '[A]...': Value must be an iterable."],
        # Generator default.
        [(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        # Unset default.
        [UNSET, "Error: Missing argument 'A...'."],
        # Tuples defaults with wrong length.
        [
            tuple(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [(1,), "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            (1, 2, 3),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Lists defaults with wrong length.
        [list(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [[1], "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            [1, 2, 3],
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Sets defaults with wrong length.
        [set(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            set([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            set([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Frozensets defaults with wrong length.
        [
            frozenset(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [
            frozenset([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            frozenset([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Dictionaries defaults with wrong length.
        [dict(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            {1: "a"},
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            {1: "a", 2: "b", 3: "c"},
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
    ],
)
def test_bad_defaults_for_nargs(runner, default, message):
    """Some defaults are not valid when nargs is set."""

    @click.command()
    @click.argument("a", nargs=2, type=int, default=default)
    def cmd(a):
        click.echo(repr(a))

    result = runner.invoke(cmd, [])
    assert message in result.stderr


def test_multiple_param_decls_not_allowed(runner):
    with pytest.raises(TypeError):

        @click.command()
        @click.argument("x", click.Choice(["a", "b"]))
        def copy(x):
            click.echo(x)


def test_multiple_not_allowed():
    with pytest.raises(TypeError, match="multiple"):
        click.Argument(["a"], multiple=True)


def test_subcommand_help(runner):
    @click.group()
    @click.argument("name")
    @click.argument("val")
    @click.option("--opt")
    @click.pass_context
    def cli(ctx, name, val, opt):
        ctx.obj = dict(name=name, val=val)

    @cli.command()
    @click.pass_obj
    def cmd(obj):
        click.echo(f"CMD for {obj['name']} with value {obj['val']}")

    result = runner.invoke(cli, ["foo", "bar", "cmd", "--help"])
    assert not result.exception
    assert "Usage: cli NAME VAL cmd [OPTIONS]" in result.output


def test_nested_subcommand_help(runner):
    @click.group()
    @click.argument("arg1")
    @click.option("--opt1")
    def cli(arg1, opt1):
        pass

    @cli.group()
    @click.argument("arg2")
    @click.option("--opt2")
    def cmd(arg2, opt2):
        pass

    @cmd.command()
    def subcmd():
        click.echo("subcommand")

    result = runner.invoke(cli, ["arg1", "cmd", "arg2", "subcmd", "--help"])
    assert not result.exception
    assert "Usage: cli ARG1 cmd ARG2 subcmd [OPTIONS]" in result.output


def test_when_argument_decorator_is_used_multiple_times_cls_is_preserved():
    class CustomArgument(click.Argument):
        pass

    reusable_argument = click.argument("art", cls=CustomArgument)

    @click.command()
    @reusable_argument
    def foo(arg):
        pass

    @click.command()
    @reusable_argument
    def bar(arg):
        pass

    assert isinstance(foo.params[0], CustomArgument)
    assert isinstance(bar.params[0], CustomArgument)


@pytest.mark.parametrize(
    "args_one,args_two",
    [
        (
            ("aardvark",),
            ("aardvark",),
        ),
    ],
)
def test_duplicate_names_warning(runner, args_one, args_two):
    @click.command()
    @click.argument(*args_one)
    @click.argument(*args_two)
    def cli(one, two):
        pass

    with pytest.warns(UserWarning):
        runner.invoke(cli, [])


@pytest.mark.parametrize(
    ("argument_kwargs", "pass_argv"),
    (
        # there is a large potential parameter space to explore here
        # this is just a very small sample of it
        ({}, ["myvalue"]),
        ({"nargs": -1}, []),
        ({"nargs": -1}, ["myvalue"]),
        ({"default": None}, ["myvalue"]),
        ({"required": False}, []),
        ({"required": False}, ["myvalue"]),
    ),
)
def test_argument_custom_class_can_override_type_cast_value_and_never_sees_unset(
    runner, argument_kwargs, pass_argv
):
    """
    Test that overriding type_cast_value is supported

    In particular, the argument is never passed an UNSET sentinel value.
    """

    class CustomArgument(click.Argument):
        def type_cast_value(self, ctx, value):
            assert value is not UNSET
            return value

    @click.command()
    @click.argument("myarg", **argument_kwargs, cls=CustomArgument)
    def cmd(myarg):
        click.echo("ok")

    result = runner.invoke(cmd, pass_argv)
    assert not result.exception
    assert result.exit_code == 0

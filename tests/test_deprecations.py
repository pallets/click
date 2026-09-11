import importlib.metadata
import warnings

import pytest

import click
import click.core
import click.parser
import click.shell_completion
import click.utils


@pytest.mark.parametrize(
    ("module", "name", "target"),
    [
        # Stream helpers, re-exported from both `click` and `click.utils`.
        (click, "get_binary_stream", click.utils._get_binary_stream),
        (click, "get_text_stream", click.utils._get_text_stream),
        (click.utils, "get_binary_stream", click.utils._get_binary_stream),
        (click.utils, "get_text_stream", click.utils._get_text_stream),
        # Command-class aliases, re-exported from `click` and `click.core`.
        (click, "BaseCommand", click.core._BaseCommand),
        (click, "MultiCommand", click.core._MultiCommand),
        (click.core, "BaseCommand", click.core._BaseCommand),
        (click.core, "MultiCommand", click.core._MultiCommand),
        # Old parser API (moved to `optparse`); `OptionParser` is also
        # re-exported from the top-level `click` namespace.
        (click, "OptionParser", click.parser._OptionParser),
        (click.parser, "OptionParser", click.parser._OptionParser),
        (click.parser, "Argument", click.parser._Argument),
        (click.parser, "Option", click.parser._Option),
        (click.parser, "split_opt", click.parser._split_opt),
        (click.parser, "normalize_opt", click.parser._normalize_opt),
        (click.parser, "ParsingState", click.parser._ParsingState),
        (click.parser, "split_arg_string", click.shell_completion.split_arg_string),
        # Deprecated `click.utils` utilities.
        (click.utils, "LazyFile", click.utils._LazyFile),
        (click.utils, "KeepOpenFile", click.utils._KeepOpenFile),
        (click.utils, "make_default_short_help", click.utils._make_default_short_help),
        (click.utils, "PacifyFlushWrapper", click.utils._PacifyFlushWrapper),
        (click.utils, "safecall", click.utils._safecall),
        # Version metadata attribute.
        (click, "__version__", importlib.metadata.version("click")),
    ],
    ids=lambda v: getattr(v, "__name__", v),
)
def test_attr_deprecated(module, name, target):
    with pytest.warns(DeprecationWarning, match=name):
        value = getattr(module, name)

    assert value == target


@pytest.mark.parametrize(
    "module",
    [click, click.core, click.parser, click.utils],
    ids=lambda m: m.__name__,
)
def test_unknown_attribute_raises(module):
    with pytest.raises(AttributeError, match="no_such_attribute"):
        _ = module.no_such_attribute


def test_context_protected_args_deprecated():
    ctx = click.Context(click.Command("cli"))

    with pytest.warns(DeprecationWarning, match="protected_args"):
        assert ctx.protected_args == []


def test_isolated_filesystem_deprecated(runner):
    with pytest.warns(DeprecationWarning, match="isolated_filesystem"):
        with runner.isolated_filesystem():
            pass


@pytest.mark.parametrize(
    "make_param",
    [
        pytest.param(lambda: click.Argument(["0foo"]), id="argument-leading-digit"),
        pytest.param(lambda: click.Argument(["foo.bar"]), id="argument-dot"),
        pytest.param(lambda: click.Argument(["foo bar"]), id="argument-space"),
        pytest.param(lambda: click.Argument([""]), id="argument-empty-decl"),
        pytest.param(
            lambda: click.Argument(["0foo"], expose_value=False),
            id="argument-unexposed",
        ),
        pytest.param(
            lambda: click.Argument([], expose_value=False),
            id="argument-no-decl",
        ),
        pytest.param(
            lambda: click.Option(["--0foo"], expose_value=False),
            id="option-unexposed",
        ),
        pytest.param(
            lambda: click.Option([], expose_value=False),
            id="option-no-decl",
        ),
    ],
)
def test_non_identifier_name_deprecated(make_param):
    """Click 9.0 refuses a name that is not a Python identifier."""
    with pytest.warns(DeprecationWarning, match="not a valid Python identifier"):
        make_param()


@pytest.mark.parametrize(
    "make_param",
    [
        pytest.param(lambda: click.Argument(["foo-bar"]), id="argument-hyphen"),
        pytest.param(lambda: click.Argument(["Foo_Bar"]), id="argument-case"),
        pytest.param(lambda: click.Option(["--foo-bar"]), id="option-hyphen"),
        pytest.param(lambda: click.Option(["--from"]), id="option-keyword"),
        pytest.param(
            lambda: click.Option(["--0foo", "zero_foo"]), id="option-explicit-name"
        ),
    ],
)
def test_identifier_name_not_deprecated(recwarn, make_param):
    """A usable name keeps working, and says nothing."""
    make_param()
    assert [w for w in recwarn if issubclass(w.category, DeprecationWarning)] == []


def test_non_identifier_option_name_still_raises():
    """An exposed option already refuses such a name, and keeps refusing it."""
    with pytest.raises(TypeError, match="Could not determine name"):
        click.Option(["--0foo"])


@pytest.mark.parametrize(
    ("decl", "expect"),
    [
        pytest.param("Foo_Bar", "foo_bar", id="mixed-case"),
        pytest.param("X_Y", "x_y", id="upper-case"),
        pytest.param("ΟΔΟΣ", "οδος", id="final-sigma"),
        pytest.param("\N{KELVIN SIGN}", "k", id="kelvin-sign"),
    ],
)
def test_unnormalized_explicit_name_deprecated(decl, expect):
    """Click 9.0 lower cases an explicit name like any other declaration."""
    with pytest.warns(DeprecationWarning, match="lower cases an explicit name"):
        param = click.Option(["--x", decl])

    assert param.name == decl
    assert decl.lower() == expect


@pytest.mark.parametrize(
    "decls",
    [
        pytest.param(["--x", "foo_bar"], id="already-lower"),
        pytest.param(["--x", "_from"], id="leading-underscore"),
        pytest.param(["--Foo-Bar"], id="derived-not-explicit"),
        pytest.param(["--x", "café"], id="lower-case-non-ascii"),
    ],
)
def test_normalized_explicit_name_not_deprecated(recwarn, decls):
    """A name already spelled the way 9.0 spells it says nothing."""
    click.Option(decls)
    assert [w for w in recwarn if issubclass(w.category, DeprecationWarning)] == []


def test_unnormalized_name_on_a_refused_option_is_silent():
    """An option that cannot be built at all warns about nothing."""
    with pytest.raises(TypeError, match="No options defined"):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            click.Option(["Foo_Bar"])

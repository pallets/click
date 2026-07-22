import importlib.metadata

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

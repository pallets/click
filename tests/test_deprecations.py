import pytest

import click


@pytest.mark.parametrize("module", [click, click.utils], ids=["click", "click.utils"])
@pytest.mark.parametrize("name", ["get_binary_stream", "get_text_stream"])
def test_stream_helper_deprecated(module, name):
    with pytest.warns(DeprecationWarning, match=name):
        getattr(module, name)


@pytest.mark.parametrize(
    "name",
    [
        "LazyFile",
        "KeepOpenFile",
        "make_default_short_help",
        "PacifyFlushWrapper",
        "safecall",
    ],
)
def test_utilities_deprecated(name):
    with pytest.warns(DeprecationWarning, match=name):
        getattr(click.utils, name)

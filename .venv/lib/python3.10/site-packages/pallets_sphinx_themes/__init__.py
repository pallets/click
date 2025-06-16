import inspect
import os
import re
import sys
import textwrap
from collections import namedtuple
from importlib import metadata as importlib_metadata
from urllib.parse import urlsplit

from sphinx.application import Sphinx
from sphinx.builders.dirhtml import DirectoryHTMLBuilder
from sphinx.errors import ExtensionError

from .theme_check import only_pallets_theme
from .theme_check import set_is_pallets_theme


def setup(app):
    base = os.path.join(os.path.dirname(__file__), "themes")

    for name in os.listdir(base):
        path = os.path.join(base, name)

        if os.path.isdir(path):
            app.add_html_theme(name, path)

    app.add_config_value("is_pallets_theme", None, "html")
    app.add_config_value("rtd_canonical_path", "/en/stable/", "html")
    app.add_config_value("version_banner", True, "html")

    # Use the sphinx-notfound-page extension to generate a 404 page with valid
    # URLs. Only configure it if it's not already configured.
    if "notfound.extension" not in app.config.extensions:
        app.config.extensions.append("notfound.extension")
        app.config.notfound_context = {
            "title": "Page Not Found",
            "body": """<h1>Page Not Found</h1>
            <p>
              The page you requested does not exist. You may have followed a bad
              link, or the page may have been moved or removed.
            """,
        }

        if "READTHEDOCS" not in os.environ:
            # Disable the default prefix outside of Read the Docs.
            app.config.notfound_urls_prefix = None

    app.connect("builder-inited", set_is_pallets_theme)
    app.connect("builder-inited", find_base_canonical_url)
    app.connect("builder-inited", add_theme_files)
    app.connect("html-page-context", canonical_url)

    try:
        app.connect("autodoc-skip-member", skip_internal)
        app.connect("autodoc-process-docstring", cut_module_meta)
    except ExtensionError:
        pass

    from .themes import click as click_ext
    from .themes import jinja as jinja_ext

    click_ext.setup(app)
    jinja_ext.setup(app)

    own_release, _ = get_version(__name__)
    return {"version": own_release, "parallel_read_safe": True}


@only_pallets_theme()
def find_base_canonical_url(app: Sphinx) -> None:
    """When building on Read the Docs, build the base canonical URL from the
    environment variable if it's not given in the config. Replace the path with
    ``rtd_canonical_path``, which defaults to ``/en/stable/``.
    """
    if app.config.html_baseurl:
        return

    if "READTHEDOCS_CANONICAL_URL" in os.environ:
        parts = urlsplit(os.environ["READTHEDOCS_CANONICAL_URL"])
        path = app.config.rtd_canonical_path
        app.config.html_baseurl = f"{parts.scheme}://{parts.netloc}{path}"


@only_pallets_theme()
def add_theme_files(app: Sphinx) -> None:
    # Add the JavaScript for the version warning banner if ``version_banner`` is
    # enabled. On Read the Docs, don't include it for stable or PR builds.
    # Include the project and version as data attributes that the script will
    # access. The project name is assumed to be the PyPI name, and is normalized
    # to avoid a redirect.
    rtd_version = os.environ.get("READTHEDOCS_VERSION")
    rtd_version_type = os.environ.get("READTHEDOCS_VERSION_TYPE")

    if app.config.version_banner and (
        rtd_version is None  # not on read the docs
        or (rtd_version != "stable" and rtd_version_type in {"branch", "tag"})
    ):
        app.add_js_file(
            "describe_version.js",
            **{
                "data-project": re.sub(r"[-_.]+", "-", app.config.project).lower(),
                "data-version": app.config.version,
            },
        )


@only_pallets_theme()
def canonical_url(app: Sphinx, pagename, templatename, context, doctree):
    """Sphinx 1.8 builds a canonical URL if ``html_baseurl`` config is
    set. However, it builds a URL ending with ".html" when using the
    dirhtml builder, which is incorrect. Detect this and generate the
    correct URL for each page.
    """
    base = app.config.html_baseurl

    if (
        not base
        or not isinstance(app.builder, DirectoryHTMLBuilder)
        or not context["pageurl"]
        or not context["pageurl"].endswith(".html")
    ):
        return

    # Fix pageurl for dirhtml builder if this version of Sphinx still
    # generates .html URLs.
    target = app.builder.get_target_uri(pagename)
    context["pageurl"] = base + target


@only_pallets_theme()
def skip_internal(app, what, name, obj, skip, options):
    """Skip rendering autodoc when the docstring contains a line with
    only the string `:internal:`.
    """
    docstring = inspect.getdoc(obj) or ""

    if skip or re.search(r"^\s*:internal:\s*$", docstring, re.M) is not None:
        return True


@only_pallets_theme()
def cut_module_meta(app, what, name, obj, options, lines):
    """Don't render lines that start with ``:copyright:`` or
    ``:license:`` when rendering module autodoc. These lines are useful
    meta information in the source code, but are noisy in the docs.
    """
    if what != "module":
        return

    lines[:] = [
        line for line in lines if not line.startswith((":copyright:", ":license:"))
    ]


def get_version(name, version_length=2, placeholder="x"):
    """Ensures that the named package is installed and returns version
    strings to be used by Sphinx.

    Sphinx uses ``version`` to mean an abbreviated form of the full
    version string, which is called ``release``. In ``conf.py``::

        release, version = get_version("Flask")
        # release = 1.0.x, version = 1.0.3.dev0

    :param name: Name of package to get.
    :param version_length: How many values from ``release`` to use for
        ``version``.
    :param placeholder: Extra suffix to add to the version. The default
        produces versions like ``1.2.x``.
    :return: ``(release, version)`` tuple.
    """
    try:
        release = importlib_metadata.version(name)
    except ImportError:
        print(
            textwrap.fill(
                f"'{name}' must be installed to build the documentation."
                " Install from source using `pip install -e .` in a virtualenv."
            )
        )
        sys.exit(1)

    version = ".".join(release.split(".", version_length)[:version_length])

    if placeholder:
        version = f"{version}.{placeholder}"

    return release, version


#: ``(title, url)`` named tuple that will be rendered with
ProjectLink = namedtuple("ProjectLink", ("title", "url"))

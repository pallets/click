import html
import os
import warnings

import docutils.nodes
import sphinx
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.errors import ExtensionError

from . import __version__
from .utils import replace_uris


class BaseURIError(ExtensionError):
    """Exception for malformed base URI."""


# https://www.sphinx-doc.org/en/stable/extdev/appapi.html#event-html-collect-pages
def html_collect_pages(app):
    """
    Create a ``404.html`` page.

    Uses ``notfound_template`` as a template to be rendered with
    ``notfound_context`` for its context. The resulting file generated is
    ``notfound_pagename``.html.

    If the user already defined a page with pagename title
    ``notfound_pagename``, we don't generate this page.

    :param app: Sphinx Application
    :type app: sphinx.application.Sphinx
    """
    if app.builder.embedded or app.config.notfound_pagename in app.env.titles:
        # Building embedded (e.g. htmlhelp or ePub) or there is already a ``404.rst``
        # file rendered. Skip generating our default one.
        return []

    return [(
        app.config.notfound_pagename,
        app.config.notfound_context,
        app.config.notfound_template,
    )]


# https://www.sphinx-doc.org/en/stable/extdev/appapi.html#event-html-page-context
def finalize_media(app, pagename, templatename, context, doctree):
    """
    Point media files at our media server.

    Generate absolute URLs for resources (js, images, css, etc) to point to the
    right URL. For example, if a URL in the page is ``_static/js/custom.js`` it will
    be replaced by ``<notfound_urls_prefix>/_static/js/custom.js``.

    Also, all the links from the sidebar (toctree) are replaced with their
    absolute version. For example, ``../section/pagename.html`` will be replaced
    by ``/section/pagename.html``.

    It handles a special case for Read the Docs and URLs starting with ``/_/``.
    These URLs have a special meaning under Read the Docs and don't have to be changed.
    (e.g. ``/_/static/javascript/readthedocs-doc-embed.js``)

    :param app: Sphinx Application
    :type app: sphinx.application.Sphinx

    :param pagename: name of the page being rendered
    :type pagename: str

    :param templatename: template used to render the page
    :type templatename: str

    :param context: context used to render the page
    :type context: dict

    :param doctree: doctree of the page being rendered
    :type doctree: docutils.nodes.document
    """

    default_baseuri = app.config.notfound_urls_prefix or '/'

    # https://github.com/sphinx-doc/sphinx/blob/v7.2.3/sphinx/builders/html/__init__.py#L1024-L1036
    def pathto(otheruri: str, resource: bool = False, baseuri: str = default_baseuri):
        """
        Hack pathto to display absolute URL's.

        Instead of calling ``relative_url`` function, we call
        ``app.builder.get_target_uri`` to get the absolute URL.

        .. note::

            If ``otheruri`` is a external ``resource`` it does not modify it.
            If ``otheruri`` is a static file on Read the Docs it does not modify it.
        """
        READTHEDOCS = os.environ.get('READTHEDOCS', False) == 'True'

        if resource and '://' in otheruri:
            # allow non-local resources given by scheme
            return otheruri

        if READTHEDOCS and otheruri.startswith('/_/'):
            # special case on Read the Docs
            return otheruri

        if not resource:
            otheruri = app.builder.get_target_uri(otheruri)

        if not baseuri.startswith('/'):
            raise BaseURIError('"baseuri" must be absolute')

        if otheruri and not otheruri.startswith('/'):
            otheruri = f'/{otheruri}'

        if otheruri:
            if baseuri.endswith('/'):
                baseuri = baseuri[:-1]
            otheruri = baseuri + otheruri

        uri = otheruri or '#'
        return uri

    # https://github.com/sphinx-doc/sphinx/blob/v7.2.3/sphinx/builders/html/__init__.py#L1048
    def toctree(*args, **kwargs):
        collapse = kwargs.pop('collapse', False)
        includehidden = kwargs.pop('includehidden', False)

        if sphinx.version_info >= (7, 2):
            from sphinx.environment.adapters.toctree import global_toctree_for_doc
            toc = global_toctree_for_doc(
                app.env,
                app.config.notfound_pagename,
                app.builder,
                collapse=collapse,
                includehidden=includehidden,
                **kwargs,
            )
        else:
            from sphinx.environment.adapters.toctree import TocTree
            toc = TocTree(app.env).get_toctree_for(
                app.config.notfound_pagename,
                app.builder,
                collapse=collapse,
                includehidden=includehidden,
                **kwargs,
            )

        # If no TOC is found, just return ``None`` instead of failing here
        if not toc:
            return None

        replace_uris(app, toc, docutils.nodes.reference, 'refuri')
        return app.builder.render_partial(toc)['fragment']

    # Apply our custom manipulation to 404.html page only
    if pagename == app.config.notfound_pagename:
        # Override the ``pathto`` helper function from the context to use a custom one
        # https://www.sphinx-doc.org/en/master/templating.html#pathto
        context['pathto'] = pathto

        # Override the ``toctree`` helper function from context to use a custom
        # one and generate valid links on not found page.
        # https://www.sphinx-doc.org/en/master/templating.html#toctree
        # NOTE: not used on ``singlehtml`` builder for RTD Sphinx theme
        context['toctree'] = toctree


        # Sphinx 7.2 uses `css_tag` and `js_tag` functions in the HTML template from the context.
        # We have to overwrite them here to use our own `pathto` function.
        # The code is borrowed exactly from Sphinx 7.2.2, there is no changes.
        if sphinx.version_info >= (7, 2):
            from sphinx.builders.html._assets import (
                _CascadingStyleSheet,
                _file_checksum,
                _JavaScript,
            )

            outdir = app.outdir

            # https://github.com/sphinx-doc/sphinx/blob/v7.2.2/sphinx/builders/html/__init__.py#L1057C1-L1094C31
            def css_tag(css: _CascadingStyleSheet) -> str:
                attrs = []
                for key, value in css.attributes.items():
                    if value is not None:
                        attrs.append(f'{key}="{html.escape(value, quote=True)}"')
                uri = pathto(os.fspath(css.filename), resource=True)
                if checksum := _file_checksum(outdir, css.filename):
                    uri += f'?v={checksum}'
                return f'<link {" ".join(sorted(attrs))} href="{uri}" />'

            # NOTE: commented because it fails on Python 3.9
            #
            # def js_tag(js: _JavaScript | str) -> str:
            def js_tag(js: _JavaScript) -> str:
                if not isinstance(js, _JavaScript):
                    # str value (old styled)
                    return f'<script src="{pathto(js, resource=True)}"></script>'

                attrs = []
                body = js.attributes.get('body', '')
                for key, value in js.attributes.items():
                    if key == 'body':
                        continue
                    if value is not None:
                        attrs.append(f'{key}="{html.escape(value, quote=True)}"')

                if not js.filename:
                    if attrs:
                        return f'<script {" ".join(sorted(attrs))}>{body}</script>'
                    return f'<script>{body}</script>'

                uri = pathto(os.fspath(js.filename), resource=True)
                if checksum := _file_checksum(outdir, js.filename):
                    uri += f'?v={checksum}'
                if attrs:
                    return f'<script {" ".join(sorted(attrs))} src="{uri}"></script>'
                return f'<script src="{uri}"></script>'

            context['css_tag'] = css_tag
            context['js_tag'] = js_tag


# https://www.sphinx-doc.org/en/stable/extdev/appapi.html#event-doctree-resolved
def doctree_resolved(app, doctree, docname):
    """
    Generate and override URLs for ``.. image::`` Sphinx directive.

    When ``.. image::`` is used in the ``404.rst`` file, this function will
    override the URLs to point to the right place.

    :param app: Sphinx Application
    :type app: sphinx.application.Sphinx
    :param doctree: doctree representing the document
    :type doctree: docutils.nodes.document
    :param docname: name of the document
    :type docname: str
    """

    if docname == app.config.notfound_pagename:
        # Replace image ``uri`` to its absolute version
        replace_uris(app, doctree, docutils.nodes.image, 'uri')


class OrphanMetadataCollector(EnvironmentCollector):
    """
    Force the 404 page to be ``orphan``.

    This way we remove the WARNING that Sphinx raises saying the page is not
    included in any toctree.

    This collector has the same effect than ``:orphan:`` at the top of the page.
    """

    def clear_doc(self, app, env, docname):
        return None

    def process_doc(self, app, doctree):
        metadata = app.env.metadata[app.config.notfound_pagename]
        metadata.update({'orphan': True, 'nosearch': True})

    def merge_other(self, app, env, docnames, other):
        """Merge in specified data regarding docnames from a different `BuildEnvironment`
        object which coming from a subprocess in parallel builds."""
        # TODO: find an example about why this is strictly required for parallel read
        # https://github.com/readthedocs/sphinx-notfound-page/pull/112/files#r498219556
        env.metadata.update(other.metadata)


def validate_configs(app, *args, **kwargs):
    """
    Validate configs.

    Shows a warning if one of the configs is not valid.
    """
    notfound_urls_prefix = app.config.notfound_urls_prefix
    default = (
        app.config.values.get("notfound_urls_prefix").default
        if sphinx.version_info >= (7, 3)
        else app.config.values.get("notfound_urls_prefix")[0]
    )

    if (
        notfound_urls_prefix != default
        and notfound_urls_prefix
        and not (
            notfound_urls_prefix.startswith("/") and notfound_urls_prefix.endswith("/")
        )
    ):
        message = 'notfound_urls_prefix should start and end with "/" (slash)'
        warnings.warn(message, UserWarning, stacklevel=2)


def setup(app):
    default_context = {
        'title': 'Page not found',
        'body': "<h1>Page not found</h1>\n\nUnfortunately we couldn't find the content you were looking for.",
    }

    # https://github.com/sphinx-doc/sphinx/blob/master/sphinx/themes/basic/page.html
    app.add_config_value('notfound_template', 'page.html', 'html')
    app.add_config_value('notfound_context', default_context, 'html')
    app.add_config_value('notfound_pagename', '404', 'html')

    # TODO: get these values from Project's settings
    default_language = os.environ.get('READTHEDOCS_LANGUAGE', 'en')
    default_version = os.environ.get('READTHEDOCS_VERSION', 'latest')

    # This config should replace the previous three
    app.add_config_value(
        'notfound_urls_prefix',
        '/{default_language}/{default_version}/'.format(
            default_language=default_language,
            default_version=default_version,
        ),
        'html',
        types=[str, type(None)],
    )

    app.connect('config-inited', validate_configs)

    app.connect('html-collect-pages', html_collect_pages)

    # Use ``priority=400`` argument here because we want to execute our function
    # *before* Sphinx's ``setup_resource_paths`` where the ``logo_url`` and
    # ``favicon_url`` are resolved.
    # See https://github.com/readthedocs/sphinx-notfound-page/issues/180#issuecomment-959506037
    app.connect('html-page-context', finalize_media, priority=400)

    app.connect('doctree-resolved', doctree_resolved)

    app.add_env_collector(OrphanMetadataCollector)

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

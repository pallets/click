from functools import wraps

from sphinx.theming import HTMLThemeFactory


def set_is_pallets_theme(app):
    """Set the ``is_pallets_theme`` config to ``True`` if the current
    theme is a decedent of the ``pocoo`` theme.
    """
    if app.config.is_pallets_theme is not None:
        return

    theme = getattr(app.builder, "theme", None)

    if theme is None:
        app.config.is_pallets_theme = False
        return

    pocoo_dir = HTMLThemeFactory(app).create("pocoo").get_theme_dirs()[0]
    app.config.is_pallets_theme = pocoo_dir in theme.get_theme_dirs()


def only_pallets_theme(default=None):
    """Create a decorator that calls a function only if the
    ``is_pallets_theme`` config is ``True``.

    Used to prevent Sphinx event callbacks from doing anything if the
    Pallets themes are installed but not used. ::

        @only_pallets_theme()
        def inject_value(app):
            ...

        app.connect("builder-inited", inject_value)

    :param default: Value to return if a Pallets theme is not in use.
    :return: A decorator.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(app, *args, **kwargs):
            if not app.config.is_pallets_theme:
                return default

            return f(app, *args, **kwargs)

        return wrapped

    return decorator

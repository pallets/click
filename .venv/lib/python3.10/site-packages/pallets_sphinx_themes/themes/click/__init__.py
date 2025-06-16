def setup(app):
    """Load the Click extension if Click is installed."""
    try:
        from . import domain
    except ImportError:
        return

    domain.setup(app)

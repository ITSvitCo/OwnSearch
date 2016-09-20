"""Own Search routes."""

from .views import index


def setup_routes(app):
    """Route to index page."""
    app.router.add_get('/', index)

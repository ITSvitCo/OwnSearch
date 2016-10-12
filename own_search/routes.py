"""Own Search routes."""

from .views import index
from .views import query


def setup_routes(app, project_root):
    """Route to index page."""
    app.router.add_static('/static/',
                          path=str(project_root / 'static'),
                          name='static')
    app.router.add_get('/', index)
    app.router.add_post('/q', query)

"""Own Search web views."""

from aiohttp.web import json_response
import aiohttp_jinja2


@aiohttp_jinja2.template('index.html')
async def index(request):
    """Index page."""
    return {'text': 'Hello world!'}


async def query(request):
    """Query handler."""
    post = await request.post()
    search_results = request.app['text_index'].query(post['query'])
    return json_response(search_results)

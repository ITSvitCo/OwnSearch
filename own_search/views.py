"""Own Search web views."""

import asyncio
from aiohttp.web import json_response
import aiohttp_jinja2


@aiohttp_jinja2.template('index.html')
@asyncio.coroutine
def index(request):
    """Index page."""
    return {'text': 'Hello world!'}


@asyncio.coroutine
def query(request):
    """Query handler."""
    post = yield from request.post()
    search_results = request.app['text_index'].query(post['query'])
    return json_response(search_results)

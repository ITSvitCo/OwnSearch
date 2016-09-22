"""Own Search web views."""

from aiohttp.web import json_response
import aiohttp_jinja2


@aiohttp_jinja2.template('index.html')
async def index(request):
    """Index page."""
    return {'text': 'Hello world!'}


async def query(request):
    """Queries handler."""
    search_results = {'items': [{'title': 'TITLE1',
                                 'link': 'http://test.com.1',
                                 'text': 'Text1'},
                                {'title': 'TITLE2',
                                 'link': 'http://test.com.2',
                                 'text': 'Text2'},
                                {'title': 'TITLE3',
                                 'link': 'http://test.com.3',
                                 'text': 'Text3'},
                                ]}
    import asyncio
    await asyncio.sleep(1)
    return json_response(search_results)
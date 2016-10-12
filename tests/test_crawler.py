import asyncio
import json
import http.server
import socketserver
from threading import Thread

import pytest

from crawler.web_crawler import DataLinksHTMLParser, WebCrawler


class StaticServer(Thread):
    PORT = 8081

    def run(self):
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", self.PORT), Handler)
        httpd.serve_forever()


@pytest.fixture(scope="module")
def sserver():
    ss = StaticServer(daemon=True)
    ss.start()
    return ss


@pytest.yield_fixture
def loop():
    """Setup loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Clean-up
    loop.close()


def test_HTML_parser():
    """Check html parser."""
    base_url = 'http://aiohttp.readthedocs.io/en/stable/web_reference.html'
    parser = DataLinksHTMLParser(base_url)
    with open('tests/example.html', 'r') as f:
        html = f.read()
    parser.feed(html)

    with open('tests/example.data', 'r') as f2:
        expected_data = json.load(f2)

    with open('tests/example.links', 'r') as f3:
        expected_links = set(json.load(f3))

    assert parser.data == expected_data
    all_links = parser.internal_links.union(parser.external_links)
    assert all_links == expected_links


def test_parse_url(loop, sserver):
    """Test end to end crawling."""
    exp_internal = {
        'http://127.0.0.1:8081/tests/_static/pygments.css',
        'http://127.0.0.1:8081/tests/server.html',
        'http://127.0.0.1:8081/tests/changes.html',
        'http://127.0.0.1:8081/tests/tutorial.html',
        'http://127.0.0.1:8081/tests/testing.html',
        'http://127.0.0.1:8081/tests/multipart.html',
        'http://127.0.0.1:8081/tests/example.html',
        'http://127.0.0.1:8081/tests/new_router.html',
        'http://127.0.0.1:8081/tests/_modules/aiohttp/web.html',
        'http://127.0.0.1:8081/tests/glossary.html',
        'http://127.0.0.1:8081/tests/_static/alabaster.css',
        'http://127.0.0.1:8081/tests/abc.html',
        'http://127.0.0.1:8081/tests/streams.html',
        'http://127.0.0.1:8081/tests/client.html',
        'http://127.0.0.1:8081/tests/_static/aiohttp-icon.ico',
        'http://127.0.0.1:8081/tests/api.html',
        'http://127.0.0.1:8081/tests/logging.html',
        'http://127.0.0.1:8081/tests/_sources/web_reference.txt',
        'http://127.0.0.1:8081/tests/_modules/aiohttp/web_ws.html',
        'http://127.0.0.1:8081/tests/_static/custom.css',
        'http://127.0.0.1:8081/tests/_modules/aiohttp/web_reqrep.html',
        'http://127.0.0.1:8081/tests/faq.html',
        'http://127.0.0.1:8081/tests/contributing.html',
        'http://127.0.0.1:8081/tests/client_reference.html',
        'http://127.0.0.1:8081/tests/web.html',
        'http://127.0.0.1:8081/tests/_modules/aiohttp/web_urldispatcher.html',
        'http://127.0.0.1:8081/tests/index.html',
        'http://127.0.0.1:8081/tests/gunicorn.html',
    }
    exp_external = {
        'https://github.com/KeepSafe/aiohttp',
        'http://docs.python.org/3/library/http.cookies.html',
        'https://media.readthedocs.org/css/readthedocs-doc-embed.css',
        'http://disqus.com/?ref_noscript',
        'https://multidict.readthedocs.io/en/stable/multidict.html',
        'http://docs.python.org/3/library/stdtypes.html',
        'https://codecov.io/github/KeepSafe/aiohttp',
        'http://aiohttp.readthedocs.io/en/stable/web_reference.html',
        'http://docs.python.org/3/library/datetime.html',
        'http://docs.python.org/3/library/collections.abc.html',
        'http://docs.python.org/3/library/urllib.parse.html',
        'http://docs.python.org/3/library/ssl.html',
        'http://docs.python.org/3/library/logging.html',
        'https://media.readthedocs.org/css/badge_only.css',
        'http://sphinx-doc.org/',
        'http://docs.python.org/3/library/io.html',
        'http://docs.python.org/3/library/asyncio-task.html',
        'http://docs.python.org/3/library/enum.html',
        'https://tools.ietf.org/html/rfc2616.html',
        'https://github.com/bitprophet/alabaster',
        'http://disqus.com',
        'http://docs.python.org/3/library/types.html',
        'http://docs.python.org/3/library/exceptions.html',
        'http://docs.python.org/3/library/asyncio-protocol.html',
        'http://docs.python.org/3/library/json.html',
        'http://docs.python.org/3/library/asyncio-eventloop.html',
        'http://docs.python.org/3/library/pathlib.html',
        'http://docs.python.org/3/library/asyncio-eventloops.html',
        'https://travis-ci.org/KeepSafe/aiohttp',
        'http://docs.python.org/3/library/functions.html',
    }

    async def do_test():
        wc = WebCrawler(loop=loop)
        data, internal, external = await wc._parse_url(
                'http://127.0.0.1:{}/tests/example.html'.format(
                        StaticServer.PORT))

        with open('tests/example.data', 'r') as f:
            e = json.load(f)
            exp_data = ' '.join(e)

        assert data == exp_data
        assert internal == exp_internal
        assert external == exp_external

    loop.run_until_complete(do_test())

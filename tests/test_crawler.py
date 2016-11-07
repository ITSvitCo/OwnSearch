import asyncio
import json
import http.server
import socketserver
from threading import Thread

import pytest

from crawler.web_crawler import DataLinksHTMLParser, WebCrawler, InvalidURL


class StaticServer(Thread):
    PORT = 8081
    handler = http.server.SimpleHTTPRequestHandler

    def __init__(self, *args, **kwargs):
        self.httpd = None
        socketserver.TCPServer.allow_reuse_address = True
        super().__init__(*args, **kwargs)

    def run(self):
        self.httpd = socketserver.TCPServer(("", self.PORT), self.handler)
        self.httpd.serve_forever()

    def shutdown(self):
        if self.httpd is not None:
            self.httpd.shutdown()


@pytest.fixture(scope="module")
def sserver(request):
    ss = StaticServer(daemon=True)

    def tear_down():
        ss.shutdown()

    ss.start()

    request.addfinalizer(tear_down)
    return ss


@pytest.yield_fixture
def loop():
    """Setup loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Clean-up
    loop.close()


def ignore_new_line(text):
    return text.replace('\r\n', ' ').replace('\n', ' ')


def test_HTML_parser():
    """Check html parser."""
    base_url = 'http://itsvit.com/portfolio/'
    parser = DataLinksHTMLParser(base_url)
    with open('tests/example.html', 'r') as f:
        html = f.read()
    parser.feed(html)

    with open('tests/example.data', 'r') as f2:
        expected_data = json.load(f2)

    with open('tests/example.links', 'r') as f3:
        internal_links, external_links = json.load(f3)

    title = parser.title
    data = parser.data

    assert title == 'IT Svit | Our Portfolio'
    assert data == expected_data
    assert set(internal_links) == parser.internal_links
    assert set(external_links) == parser.external_links


def test_parse_url(loop, sserver):
    """Test end to end crawling."""
    exp_internal = {
        "http://itsvit.com/our-services/web-development/",
        "http://itsvit.com/our-services/documentation/",
        "http://itsvit.com/wp-content/themes/itsvit/css/fonts.css",
        "http://itsvit.com/wp-content/themes/itsvit/style.css",
        "http://itsvit.com/wp-content/plugins/recent-tweets-widget/"
        "tp_twitter_plugin.css?ver=1.0",
        "http://itsvit.com/wp-content/themes/itsvit/libs/owl.carousel/owl/"
        "owl.carousel.css",
        "http://itsvit.com/privacy-policy/",
        "http://itsvit.com/our-services/big-data-and-data-science/",
        "http://itsvit.com/partners/",
        "http://itsvit.com/wp-content/plugins/wp-paginate/"
        "wp-paginate.css?ver=1.3.1",
        "http://itsvit.com/terms-of-use/",
        "http://itsvit.com/wp-content/themes/itsvit/img/favicon/"
        "favicon_ITSvit.ico",
        "http://itsvit.com/wp-content/themes/itsvit/img/favicon/"
        "d-logo-sketch-small.png",
        "http://itsvit.com/about-it-svit/",
        "http://itsvit.com/our-services/design/",
        "http://itsvit.com/wp-content/themes/itsvit/libs/magnific/"
        "magnific-popup.css",
        "http://itsvit.com/",
        "http://itsvit.com/blog/",
        "http://itsvit.com/sitemap/",
        "http://itsvit.com/contacts/",
        "http://itsvit.com/our-services/quality-assurance-and-automation/",
        "http://itsvit.com/wp-content/themes/itsvit/libs/font-awesome/css/"
        "font-awesome.min.css",
        "http://itsvit.com/wp-content/themes/itsvit/css/media.css",
        "http://itsvit.com/portfolio/",
        "http://itsvit.com/our-services/devops/",
        "http://itsvit.com/wp-content/themes/itsvit/libs/bootstrap/css/"
        "bootstrap-grid.min.css",
        "http://itsvit.com/wp-content/themes/itsvit/img/favicon/"
        "default-favicon.png",
        "http://itsvit.com/wp-content/plugins/contact-form-7/includes/css/"
        "styles.css?ver=4.5.1",
    }
    exp_external = {
        "https://plus.google.com/+ItsvitOrg/videos",
        "https://www.linkedin.com/company/it-svit?trk=top_nav_home",
        "https://www.instagram.com/itsvit/",
        "http://fonts.googleapis.com/css?family=Indie+Flower&ver=4.5.4",
        "https://cdnjs.cloudflare.com/ajax/libs/jQuery.mmenu/5.7.4/css/"
        "jquery.mmenu.all.css",
        "https://vk.com/itsvit", "https://www.facebook.com/IT.Svit.Team",
        "https://github.com/ITSvitCo",
        "https://twitter.com/itsvit",
        "https://fonts.googleapis.com/css?family=Open+Sans:400,600|Roboto",
    }

    @asyncio.coroutine
    def do_test():
        wc = WebCrawler(loop=loop)
        title, data, internal, external = yield from wc._parse_url(
                'http://127.0.0.1:{}/tests/example.html'.format(
                        StaticServer.PORT),
                base_url='http://itsvit.com/portfolio/')

        with open('tests/example.data', 'r') as f:
            e = json.load(f)
            exp_data = ' '.join(e)

        assert title == 'IT Svit | Our Portfolio'
        assert ignore_new_line(data) == ignore_new_line(exp_data)
        assert internal == exp_internal
        assert external == exp_external

    loop.run_until_complete(do_test())


def test_parse_url_css(loop, sserver):
    """Test end to end crawling."""

    @asyncio.coroutine
    def do_test():
        with pytest.raises(InvalidURL):
            wc = WebCrawler(loop=loop)
            title, data, internal, external = yield from wc._parse_url(
                    'http://127.0.0.1:{}/tests/owl.carousel.css'.format(
                            StaticServer.PORT))

    loop.run_until_complete(do_test())

"""Recursive web crawler."""

import asyncio
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import aiohttp
import async_timeout

ALLOWED_STATUS_CODES = (200,)
ALLOWED_MIME_TYPES = ('text/plain',
                      'text/html',
                      )


class InvalidURL(RuntimeError):
    """Invalid error exception."""


class DataLinksHTMLParser(HTMLParser):
    """Handle html, store links, texts."""

    def __init__(self, base_url=None):
        """Init variables."""
        self.base_url = base_url
        self.ignore_data = []
        self.capture_title = False
        self.data = []
        self.title = ''
        self.internal_links = set()
        self.external_links = set()
        super().__init__()

    def _normalize_link(self, link):
        """Cut fragment, make url absolute."""
        fragment = link.find('#')
        if fragment != -1:
            link = link[:fragment]

        if self.base_url is not None:
            normalized = urljoin(self.base_url, link)
            return normalized
        else:
            return link

    def _is_internal(self, link):
        """Compare the link and base url netloc."""
        bnetloc = urlparse(self.base_url)[1]
        netloc = urlparse(link)[1]
        return bnetloc == netloc

    def handle_starttag(self, tag, attrs):
        """Seek for script and links tags."""
        if tag in ('script', 'style'):
            self.ignore_data.append(tag)

        elif tag == 'title':
            self.capture_title = True

        elif tag in ('a', 'link'):
            for attr, value in attrs:
                if attr == 'href' and value is not None:
                    link = self._normalize_link(value)
                    if link:
                        if self._is_internal(link):
                            self.internal_links.add(link)
                        else:
                            self.external_links.add(link)

    def handle_endtag(self, tag):
        """Seek for close script tag."""
        if tag in ('script', 'style'):
            try:
                self.ignore_data.remove(tag)
            except ValueError:
                # Already closed tag
                pass

        elif tag == 'title':
            self.capture_title = False

    def handle_data(self, data):
        """Store data."""
        if not self.ignore_data:
            data = data.strip()
            if data:
                if self.capture_title:
                    self.title = data
                else:
                    self.data.append(data)


class WebCrawler:
    """Asynchronous web crawler."""

    def __init__(self, workers=20, ignore_external=True, loop=None):
        """Init crawler."""
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self.workers = workers
        self.ignore_external = ignore_external
        self.handled_urls = set()
        self.url_queue = asyncio.Queue()
        self.text_queue = asyncio.Queue()
        self.consumer = None

    @asyncio.coroutine
    def worker(self):
        """Crawl worker."""
        while True:
            url = yield from self.url_queue.get()
            try:
                title, text, internal, external = \
                    yield from self._parse_url(url)
            except InvalidURL:
                continue

            new_internal = internal.difference(self.handled_urls)
            self.handled_urls.update(new_internal)
            for ni in new_internal:
                yield from self.url_queue.put(ni)

            if not self.ignore_external:
                new_external = external.difference(self.handled_urls)
                self.handled_urls.update(new_external)
                for ne in new_external:
                    yield from self.url_queue.put(ne)

            # print(url)
            yield from self.text_queue.put((url, title, text))

    @asyncio.coroutine
    def _parse_url(self, url, base_url=None):
        """Parse web page content for external & internal links."""
        if base_url is None:
            base_url = url
        parser = DataLinksHTMLParser(base_url=base_url)

        # TODO: add retry count
        try:
            with async_timeout.timeout(10):
                with aiohttp.ClientSession() as session:
                    resp = None
                    try:
                        resp = yield from session.get(url)

                    except (ValueError,
                            aiohttp.errors.ClientResponseError,
                            aiohttp.errors.ClientRequestError,
                            aiohttp.errors.ClientOSError,
                            aiohttp.errors.ContentEncodingError):
                        # ValueError: Host could not be detected.
                        # aiohttp.errors.ClientResponseError
                        # Can not write request body for
                        # [Errno 10060] Cannot connect to host
                        # 400, message='deflate
                        raise InvalidURL()
                    else:

                        # Verify status code
                        if resp is None \
                                or resp.status not in ALLOWED_STATUS_CODES:
                            raise InvalidURL()

                        # Verify content type
                        if resp.content_type not in ALLOWED_MIME_TYPES:
                            raise InvalidURL()

                        try:
                            resp_text = yield from resp.text()

                        except UnicodeDecodeError:
                            raise InvalidURL()

                    finally:
                        if resp is not None:
                            resp.close()

        except asyncio.TimeoutError:
            # print('Timeout', url)
            raise InvalidURL()

        parser.feed(resp_text)
        title = parser.title
        text = ' '.join(parser.data)
        internal = parser.internal_links
        external = parser.external_links

        parser.close()
        return title, text, internal, external

    @asyncio.coroutine
    def _feed_consumer(self):
        """Feed consumer."""
        while self.consumer is not None:
            url, title, text = yield from self.text_queue.get()
            self.consumer(url, title, text)

    def create_workers(self):
        """Create crawler workers."""
        for _ in range(self.workers):
            self.loop.create_task(self.worker())
        self.loop.create_task(self._feed_consumer())

    def register_consumer(self, consumer):
        """Register consumer."""
        self.consumer = consumer

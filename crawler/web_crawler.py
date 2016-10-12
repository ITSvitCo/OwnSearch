"""Recursive web crawler."""

import asyncio
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import aiohttp
import async_timeout


class InvalidURL(RuntimeError):
    """Invalid error exception."""


class DataLinksHTMLParser(HTMLParser):
    """Handle html, store links, texts."""

    def __init__(self, base_url=None):
        """Init variables."""
        self.base_url = base_url
        self.ignore_data = []
        self.data = []
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

    def handle_data(self, data):
        """Store data."""
        if not self.ignore_data:
            data = data.strip()
            if data:
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

    async def worker(self):
        """Crawl worker."""
        while True:
            url = await self.url_queue.get()
            try:
                text, internal, external = await self._parse_url(url)
            except InvalidURL:
                continue

            new_internal = internal.difference(self.handled_urls)
            self.handled_urls.update(new_internal)
            for ni in new_internal:
                await self.url_queue.put(ni)

            if not self.ignore_external:
                new_external = external.difference(self.handled_urls)
                self.handled_urls.update(new_external)
                for ne in new_external:
                    await self.url_queue.put(ne)

            # print(url)
            await self.text_queue.put((url, text))

    async def _parse_url(self, url):
        """Parse web page content for external & internal links."""
        parser = DataLinksHTMLParser(base_url=url)

        # TODO: add retry count
        try:
            with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    resp = None
                    try:
                        resp = await session.get(url)
                        # TODO: verify content type
                        # TODO: list of valid status codes

                    except (ValueError,
                            aiohttp.errors.ClientResponseError,
                            aiohttp.errors.ClientRequestError,
                            aiohttp.errors.ClientOSError,
 +                          aiohttp.errors.ContentEncodingError):
                        # ValueError: Host could not be detected.
                        # aiohttp.errors.ClientResponseError
                        # Can not write request body for
                        # [Errno 10060] Cannot connect to host
                        # 400, message='deflate
                        raise InvalidURL()
                    else:
                        if resp is None or resp.status != 200:
                            raise InvalidURL()

                        try:
                            # TODO: detect charset without chardet!!!
                            resp_text = await resp.text("utf-8")

                        except UnicodeDecodeError:
                            raise InvalidURL()

                    finally:
                        if resp is not None:
                            resp.close()

        except asyncio.TimeoutError:
            # print('Timeout', url)
            raise InvalidURL()

        parser.feed(resp_text)
        # TODO: recognize internal/external urls
        text = ' '.join(parser.data)
        internal = parser.internal_links
        external = parser.external_links

        parser.close()
        return text, internal, external

    async def _feed_consumer(self):
        """Feed consumer."""
        while self.consumer is not None:
            url, text = await self.text_queue.get()
            self.consumer(text, 'Title', url)

    def create_workers(self):
        """Create crawler workers."""
        for _ in range(self.workers):
            self.loop.create_task(self.worker())
        self.loop.create_task(self._feed_consumer())

    def register_consumer(self, consumer):
        """Register consumer."""
        self.consumer = consumer

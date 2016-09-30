"""Recursive web crawler."""

import asyncio
from html.parser import HTMLParser
from urllib.parse import urljoin

import aiohttp


class InvalidURL(RuntimeError):
    """Invalid error exception."""


class DataLinksHTMLParser(HTMLParser):
    """Handle html, store links, texts."""

    def __init__(self, base_url=None):
        """Init variables."""
        self.base_url = base_url
        self.ignore_data = []
        self.data = []
        self.links = set()
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

    def handle_starttag(self, tag, attrs):
        """Seek for script and links tags."""
        if tag in ('script', 'style'):
            self.ignore_data.append(tag)

        elif tag in ('a', 'link'):
            for attr, value in attrs:
                if attr == 'href':
                    link = self._normalize_link(value)
                    if link:
                        self.links.add(link)

    def handle_endtag(self, tag):
        """Seek for close script tag."""
        if tag in ('script', 'style'):
            self.ignore_data.remove(tag)

    def handle_data(self, data):
        """Store data."""
        if not self.ignore_data:
            data = data.strip()
            if data:
                self.data.append(data)


class WebCrawler:
    """Asynchronous web crawler."""

    def __init__(self, workers=10, ignore_external=True, loop=None):
        """Init crawler."""
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self.ignore_external = ignore_external
        self.handled_urls = set()
        self.queue = asyncio.Queue()
        self.workers = []

    async def worker(self):
        """Crawl worker."""
        while True:
            url = await self.queue.get()
            try:
                text, internal, external = await self._parse_links(url)
            except InvalidURL:
                continue

            new_internal = internal.difference(self.handled_urls)
            await self.queue.put(new_internal)

            if not self.ignore_external:
                new_external = external.difference(self.handled_urls)
                await self.queue.put(new_external)

    async def _parse_links(self, url):
        """Parse web page content for external & internal links."""
        parser = DataLinksHTMLParser(base_url=url)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, ) as resp:
                # TODO: verify content type
                # TODO: list of valid status codes
                if resp.status != 200:
                    raise InvalidURL()

                resp_text = await resp.text()
                parser.feed(resp_text)

        # TODO: recognize internal/external urls
        text = ' '.join(parser.data)
        internal = parser.links
        external = set()

        parser.close()
        return text, internal, external

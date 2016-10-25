"""Own Search application file."""

import asyncio
import logging
import pathlib

from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml

from indexer import TextIndex
from own_search.routes import setup_routes
from crawler.web_crawler import WebCrawler


PROJ_ROOT = pathlib.Path(__file__).parent


def load_config(fname):
    """Load yaml config file."""
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    return data


async def init(loop):
    """Init application."""
    # load config from yaml file in current dir
    conf = load_config(str(pathlib.Path('.') / 'config' / 'own_search.yaml'))

    # setup application and extensions
    app = web.Application(loop=loop)
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('own_search', 'templates'))

    text_index = TextIndex()
    app['text_index'] = text_index

    crawler = WebCrawler(loop=loop)
    await crawler.url_queue.put(conf['start_url'])
    crawler.create_workers()
    crawler.register_consumer(text_index.index_document)

    # setup views and routes
    setup_routes(app, PROJ_ROOT)

    host, port = conf['host'], conf['port']
    return app, host, port


def main():
    """Run web application."""
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()

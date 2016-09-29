import json
from crawler.web_crawler import DataLinksHTMLParser


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
    assert parser.links == expected_links

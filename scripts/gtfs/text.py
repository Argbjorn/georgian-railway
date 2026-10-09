"""Conversion of site texts to plain GTFS field values."""

import re
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.parts.append(' ')

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(value):
    """Strips tags (keeping link text), decodes entities and collapses whitespace.

    GTFS forbids HTML and line breaks in field values.
    """
    if not value:
        return ''
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()

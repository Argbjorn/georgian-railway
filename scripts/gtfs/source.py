"""Loading and filtering of the site data files that the GTFS feed is built from."""

import json
import os
import re

_DIRECTION_SHORTCODE = re.compile(r'{{<\s*direction\s+"([^"]+)"\s+"([^"]+)"\s*>}}')


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_direction_pages(directions_dir):
    """Maps (start station code, end station code) to the slug of the site's direction page.

    Direction pages are content/directions/<slug>/_index.md embedding the
    `{{< direction "<start>" "<end>" >}}` shortcode.
    """
    pages = {}
    for slug in sorted(os.listdir(directions_dir)):
        index_path = os.path.join(directions_dir, slug, '_index.md')
        if not os.path.isfile(index_path):
            continue
        with open(index_path, encoding='utf-8') as f:
            match = _DIRECTION_SHORTCODE.search(f.read())
        if match:
            pages[match.groups()] = slug
    return pages


def select_routes(routes):
    """Routes included in the feed: active ones with a schedule (upcoming routes included)."""
    return [route for route in routes if route.get('active') and route.get('stations')]

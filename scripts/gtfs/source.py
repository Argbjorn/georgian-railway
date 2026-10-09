"""Loading and filtering of the site data files that the GTFS feed is built from."""

import json


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def select_routes(routes):
    """Routes included in the feed: active ones with a schedule (upcoming routes included)."""
    return [route for route in routes if route.get('active') and route.get('stations')]

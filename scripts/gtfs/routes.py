"""routes.txt — lines: trains with the same terminal stations (both directions) and train type."""

from dataclasses import dataclass

from .config import LANG_URL_PREFIX, LINE_NAME_CITY_PRIORITY, SITE_URL
from .ids import stop_id

FILE_NAME = 'routes.txt'
FIELDS = [
    'route_id',
    'agency_id',
    'route_short_name',
    'route_long_name',
    'route_desc',
    'route_type',
    'route_url',
    'route_color',
    'route_text_color',
    'route_sort_order',
    'continuous_pickup',
    'continuous_drop_off',
    'network_id',
    'cemv_support',
]
# agency_id is conditionally required (multiple agencies); route_long_name is required while
# route_short_name is empty.
REQUIRED_FIELDS = {'route_id', 'agency_id', 'route_long_name', 'route_type'}

ROUTE_TYPE_RAIL = 2


@dataclass
class Line:
    route_id: str
    # Sorted by ref.
    trains: list
    # Train departing from the line's leading city (lowest ref among such trains); its direction
    # is direction_id=0 and its page is the line's URL.
    representative: dict
    # Whether the line name lists the cities in reverse order of the lowest-ref train's name.
    name_reversed: bool

    def direction_id(self, train):
        return 0 if terminals(train) == terminals(self.representative) else 1


def terminals(train):
    return train['stations'][0]['code'], train['stations'][-1]['code']


def name_cities(train, lang='en'):
    """Origin and destination as written in the train name ("Borjomi → Tbilisi")."""
    parts = [part.strip() for part in train[f'name:{lang}'].split('→')]
    if len(parts) != 2:
        raise ValueError(f'Train {train["ref"]}: name:{lang} {train[f"name:{lang}"]!r} is not "A → B"')
    return parts


def _make_line(route_id, trains):
    origin, destination = name_cities(trains[0])
    leading_city = next((city for city in LINE_NAME_CITY_PRIORITY if city in (origin, destination)), origin)
    representative = next((train for train in trains if name_cities(train)[0] == leading_city), trains[0])
    return Line(route_id, trains, representative, name_reversed=leading_city != origin)


def line_route_id(train):
    """Stable id from the terminal stations (order-independent) and the train type."""
    parts = sorted(stop_id(code) for code in terminals(train))
    if train.get('train_type'):
        parts.append(train['train_type'])
    return '-'.join(parts)


def group_lines(routes):
    """Groups trains into lines, ordered by the lowest train ref of each line.

    Grouping is done here rather than via `analogue`/`reverse` from routes.json, because those
    skip upcoming trains, which the feed includes.
    """
    trains_by_line = {}
    for train in sorted(routes, key=lambda r: r['ref']):
        trains_by_line.setdefault(line_route_id(train), []).append(train)
    lines = [_make_line(route_id, trains) for route_id, trains in trains_by_line.items()]

    for line in lines:
        operators = {train['operator'] for train in line.trains}
        if len(operators) > 1:
            refs = [train['ref'] for train in line.trains]
            raise ValueError(f'Line {line.route_id} (trains {refs}) has several operators: {sorted(operators)}')

    return lines


def line_name(line, lang='en'):
    cities = name_cities(line.trains[0], lang)
    if line.name_reversed:
        cities.reverse()
    return ' — '.join(cities)


def line_url(line, direction_pages, lang='en'):
    """The site's direction page for the representative train's direction, else the train's page."""
    slug = direction_pages.get(terminals(line.representative))
    path = f'directions/{slug}' if slug else f'routes/{line.representative["ref"]}'
    return f'{SITE_URL}{LANG_URL_PREFIX[lang]}/{path}/'


def build_routes(lines, direction_pages):
    return [{
        'route_id': line.route_id,
        'agency_id': line.representative['operator'],
        'route_long_name': line_name(line),
        'route_type': ROUTE_TYPE_RAIL,
        'route_url': line_url(line, direction_pages),
        'route_sort_order': line.trains[0]['ref'],
    } for line in lines]

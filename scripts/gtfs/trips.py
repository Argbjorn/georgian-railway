"""trips.txt — one trip per train (ref)."""

from .routes import name_cities
from .services import service_id

FILE_NAME = 'trips.txt'
FIELDS = [
    'route_id',
    'service_id',
    'trip_id',
    'trip_headsign',
    'trip_short_name',
    'direction_id',
    'block_id',
    'shape_id',
    'wheelchair_accessible',
    'bikes_allowed',
    'cars_allowed',
    'safe_duration_factor',
    'safe_duration_offset',
]
REQUIRED_FIELDS = {'route_id', 'service_id', 'trip_id'}

# wheelchair_accessible: 1 — accessible, 0 — no information.
WHEELCHAIR_ACCESSIBLE_TRAIN_TYPES = {'stadler'}
BIKES_ALLOWED = 0  # no information
CARS_ALLOWED = 2  # no cars are carried


def trip_headsign(train, lang='en'):
    return name_cities(train, lang)[1]


def build_trips(lines, shape_ids=None):
    """`shape_ids` maps train ref to shape_id; trains without a shape get no shape_id."""
    shape_ids = shape_ids or {}
    rows = []
    for line in lines:
        for train in line.trains:
            rows.append({
                'route_id': line.route_id,
                'service_id': service_id(train),
                'trip_id': str(train['ref']),
                'trip_headsign': trip_headsign(train),
                'trip_short_name': str(train['ref']),
                'direction_id': line.direction_id(train),
                'shape_id': shape_ids.get(train['ref'], ''),
                'wheelchair_accessible': 1 if train.get('train_type') in WHEELCHAIR_ACCESSIBLE_TRAIN_TYPES else 0,
                'bikes_allowed': BIKES_ALLOWED,
                'cars_allowed': CARS_ALLOWED,
            })
    return rows

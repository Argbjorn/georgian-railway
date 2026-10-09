"""stops.txt — stations served by the trains in the feed."""

from urllib.parse import quote

from .config import LANG_URL_PREFIX, SITE_URL, STOP_TIMEZONES
from .ids import stop_id
from .text import html_to_text

FILE_NAME = 'stops.txt'
FIELDS = [
    'stop_id',
    'stop_code',
    'stop_name',
    'tts_stop_name',
    'stop_desc',
    'stop_lat',
    'stop_lon',
    'zone_id',
    'stop_url',
    'location_type',
    'parent_station',
    'stop_timezone',
    'wheelchair_boarding',
    'level_id',
    'platform_code',
    'stop_access',
]
# stop_name/stop_lat/stop_lon are conditionally required — required for location_type=0.
REQUIRED_FIELDS = {'stop_id', 'stop_name', 'stop_lat', 'stop_lon'}


def station_url(station_code, lang='en'):
    return f'{SITE_URL}{LANG_URL_PREFIX[lang]}/stations/{quote(station_code)}/'


def station_description(station, lang='en'):
    return html_to_text((station.get('description') or {}).get(lang))


def used_station_codes(routes):
    return {station['code'] for route in routes for station in route['stations']}


def build_stops(routes, stations):
    """Returns stop rows for every station referenced by `routes`, sorted by stop_id."""
    codes = used_station_codes(routes)
    missing = codes - stations.keys()
    if missing:
        raise ValueError(f'Stations missing from stations.json: {sorted(missing)}')

    rows = []
    for code in codes:
        station = stations[code]
        lat, lon = station['coords']
        rows.append({
            'stop_id': stop_id(code),
            'stop_name': station['name_en'],
            'stop_desc': station_description(station),
            'stop_lat': lat,
            'stop_lon': lon,
            'stop_url': station_url(code),
            'stop_timezone': STOP_TIMEZONES.get(code, ''),
        })

    ids = [row['stop_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate stop_id after transliteration')

    return sorted(rows, key=lambda row: row['stop_id'])

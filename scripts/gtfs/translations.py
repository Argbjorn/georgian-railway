"""translations.txt — ka/ru versions of rider-facing texts and site URLs (the feed itself is in en)."""

from .config import AGENCY_NAME_TRANSLATIONS, TRANSLATION_LANGS
from .ids import stop_id
from .routes import line_name, line_url
from .stops import station_description, station_url, used_station_codes
from .trips import trip_headsign

FILE_NAME = 'translations.txt'
FIELDS = ['table_name', 'field_name', 'language', 'translation', 'record_id', 'record_sub_id', 'field_value']
REQUIRED_FIELDS = {'table_name', 'field_name', 'language', 'translation', 'record_id'}


def _rows(table_name, record_id, fields):
    """`fields`: {field_name: (value in the feed, callable(lang) → translated value)}.

    Empty translations and translations equal to the feed value (e.g. a Latin-script station
    name copied into name_ru) are skipped.
    """
    rows = []
    for field_name, (original, value_for) in fields.items():
        for lang in TRANSLATION_LANGS:
            value = value_for(lang)
            if value and value != original:
                rows.append({
                    'table_name': table_name,
                    'field_name': field_name,
                    'language': lang,
                    'translation': value,
                    'record_id': record_id,
                })
    return rows


def build_translations(agency_rows, routes, stations, lines, direction_pages):
    rows = []

    for agency in agency_rows:
        names = AGENCY_NAME_TRANSLATIONS.get(agency['agency_id'], {})
        rows += _rows('agency', agency['agency_id'], {'agency_name': (agency['agency_name'], names.get)})

    for code in sorted(used_station_codes(routes), key=stop_id):
        station = stations[code]
        rows += _rows('stops', stop_id(code), {
            'stop_name': (station['name_en'], lambda lang: station.get(f'name_{lang}')),
            'stop_desc': (station_description(station), lambda lang: station_description(station, lang)),
            'stop_url': (station_url(code), lambda lang: station_url(code, lang)),
        })

    for line in lines:
        rows += _rows('routes', line.route_id, {
            'route_long_name': (line_name(line), lambda lang: line_name(line, lang)),
            'route_url': (line_url(line, direction_pages), lambda lang: line_url(line, direction_pages, lang)),
        })

    for line in lines:
        for train in line.trains:
            rows += _rows('trips', str(train['ref']), {
                'trip_headsign': (trip_headsign(train), lambda lang: trip_headsign(train, lang)),
            })

    return rows

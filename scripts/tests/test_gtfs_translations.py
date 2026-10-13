from gtfs import agency, routes, translations
from gtfs.config import AGENCY_NAME_TRANSLATIONS
from gtfs.ids import stop_id
from gtfs.stops import used_station_codes
from gtfs.source import load_direction_pages, load_json, select_routes
from config import DIRECTIONS_CONTENT_DIR
from utils import ROUTES_FILE, STATIONS_FILE


def train(ref, start, end, names):
    return {
        'ref': ref,
        'train_type': None,
        'operator': 'GR',
        'name:en': names['en'],
        'name:ka': names['ka'],
        'name:ru': names['ru'],
        'stations': [{'code': start}, {'code': end}],
    }


STATIONS = {
    'borjomi': {'name_en': 'Borjomi', 'name_ka': 'ბორჯომი', 'name_ru': 'Боржоми', 'coords': [41.8, 43.4],
                'description': {'en': 'Far <br>from center', 'ka': '', 'ru': 'Далеко от <a href="/x">центра</a>'}},
    'tbilisi': {'name_en': 'Tbilisi', 'name_ka': 'თბილისი', 'name_ru': 'Tbilisi', 'coords': [41.7, 44.8]},
}
TRAINS = [train(617, 'borjomi', 'tbilisi', {'en': 'Borjomi → Tbilisi', 'ka': 'ბორჯომი → თბილისი', 'ru': 'Боржоми → Тбилиси'})]


def build(trains=TRAINS, stations=STATIONS, pages=None):
    lines = routes.group_lines(trains)
    return translations.build_translations(agency.build_agency(trains), trains, stations, lines, pages or {})


def find(rows, table, field, lang, record_id):
    matches = [row['translation'] for row in rows if (row['table_name'], row['field_name'], row['language'],
                                                      row['record_id']) == (table, field, lang, record_id)]
    return matches[0] if matches else None


class TestBuildTranslations:
    def test_agency_name(self):
        rows = build()
        for lang in ('ka', 'ru'):
            assert find(rows, 'agency', 'agency_name', lang, 'GR') == AGENCY_NAME_TRANSLATIONS['GR'][lang]

    def test_stop_fields(self):
        rows = build()
        assert find(rows, 'stops', 'stop_name', 'ru', 'borjomi') == 'Боржоми'
        assert find(rows, 'stops', 'stop_desc', 'ru', 'borjomi') == 'Далеко от центра'
        assert find(rows, 'stops', 'stop_url', 'ka', 'borjomi') == 'https://georailway.com/ka/stations/borjomi/'

    def test_empty_and_untranslated_values_skipped(self):
        rows = build()
        assert find(rows, 'stops', 'stop_desc', 'ka', 'borjomi') is None  # empty description
        assert find(rows, 'stops', 'stop_name', 'ru', 'tbilisi') is None  # same as English name
        assert find(rows, 'stops', 'stop_desc', 'ru', 'tbilisi') is None  # no description at all

    def test_route_and_trip_fields(self):
        rows = build()
        route_id = 'tbilisi-borjomi'
        assert find(rows, 'routes', 'route_long_name', 'ru', route_id) == 'Тбилиси — Боржоми'
        assert find(rows, 'routes', 'route_url', 'ru', route_id) == 'https://georailway.com/ru/routes/617/'
        assert find(rows, 'trips', 'trip_headsign', 'ka', '617') == 'თბილისი'

    def test_rows_use_record_id_only(self):
        for row in build():
            assert set(row) == {'table_name', 'field_name', 'language', 'translation', 'record_id'}


class TestRealData:
    def test_every_record_exists_in_feed(self):
        trains = select_routes(load_json(ROUTES_FILE))
        stations = load_json(STATIONS_FILE)
        lines = routes.group_lines(trains)
        rows = translations.build_translations(agency.build_agency(trains), trains, stations, lines,
                                               load_direction_pages(DIRECTIONS_CONTENT_DIR))
        records = {
            'agency': {a['agency_id'] for a in agency.build_agency(trains)},
            'stops': {stop_id(code) for code in used_station_codes(trains)},
            'routes': {line.route_id for line in lines},
            'trips': {str(t['ref']) for t in trains},
        }
        for row in rows:
            assert row['record_id'] in records[row['table_name']], row
        keys = [(r['table_name'], r['field_name'], r['language'], r['record_id']) for r in rows]
        assert len(keys) == len(set(keys))

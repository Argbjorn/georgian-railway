import pytest

from gtfs import stops
from gtfs.config import STOP_TIMEZONES
from gtfs.ids import stop_id
from gtfs.source import load_json, select_routes
from gtfs.text import html_to_text
from utils import ROUTES_FILE, STATIONS_FILE


def station(code, **extra):
    return {'code': code, 'name_en': code.title(), 'coords': [41.5, 44.5], **extra}


def route(*codes):
    return {'stations': [{'code': code} for code in codes]}


class TestStopId:
    def test_ascii_code_unchanged(self):
        assert stop_id('tbilisicentralstation') == 'tbilisicentralstation'

    @pytest.mark.parametrize('code, expected', [
        ('böyükkəsik', 'boyukkesik'),
        ('bakı', 'baki'),
        ('ağstafastansiyası', 'agstafastansiyasi'),
        ('biləcəri', 'bileceri'),
    ])
    def test_azerbaijani_letters(self, code, expected):
        assert stop_id(code) == expected

    def test_unknown_letter_fails(self):
        with pytest.raises(ValueError, match='transliteration'):
            stop_id('şəkiä')


class TestHtmlToText:
    def test_link_text_kept_and_br_replaced(self):
        value = "Go to <a href='/stations/rioni/'>Rioni</a>.<br><br>Ticket office: 8:00&ndash;22:00"
        assert html_to_text(value) == 'Go to Rioni. Ticket office: 8:00–22:00'

    def test_empty(self):
        assert html_to_text(None) == ''
        assert html_to_text('') == ''


class TestBuildStops:
    def test_only_used_stations_sorted(self):
        stations = {code: station(code) for code in ['b', 'a', 'unused']}
        rows = stops.build_stops([route('b', 'a')], stations)
        assert [row['stop_id'] for row in rows] == ['a', 'b']

    def test_missing_station_fails(self):
        with pytest.raises(ValueError, match='nowhere'):
            stops.build_stops([route('nowhere')], {})

    def test_duplicate_stop_id_fails(self):
        stations = {'bakı': station('bakı'), 'baki': station('baki')}
        with pytest.raises(ValueError, match='Duplicate'):
            stops.build_stops([route('bakı', 'baki')], stations)

    def test_row_fields(self):
        stations = {'baku': station('baku', coords=[40.38, 49.85],
                                    description={'en': 'Main <br>station'})}
        [row] = stops.build_stops([route('baku')], stations)
        assert row == {
            'stop_id': 'baku',
            'stop_name': 'Baku',
            'stop_desc': 'Main station',
            'stop_lat': 40.38,
            'stop_lon': 49.85,
            'stop_url': 'https://georailway.com/stations/baku/',
            'stop_timezone': 'Asia/Baku',
        }

    def test_non_ascii_code(self):
        [row] = stops.build_stops([route('bakı')], {'bakı': station('bakı')})
        assert row['stop_id'] == 'baki'
        assert row['stop_url'] == 'https://georailway.com/stations/bak%C4%B1/'

    def test_georgian_station_has_no_timezone(self):
        [row] = stops.build_stops([route('rioni')], {'rioni': station('rioni')})
        assert row['stop_timezone'] == ''


class TestStationUrl:
    def test_languages(self):
        assert stops.station_url('rioni') == 'https://georailway.com/stations/rioni/'
        assert stops.station_url('rioni', 'ru') == 'https://georailway.com/ru/stations/rioni/'
        assert stops.station_url('rioni', 'ka') == 'https://georailway.com/ka/stations/rioni/'


class TestRealData:
    """Checks the generator against the current data/*.json files."""

    def test_builds_from_current_data(self):
        routes = select_routes(load_json(ROUTES_FILE))
        rows = stops.build_stops(routes, load_json(STATIONS_FILE))
        assert rows
        assert all(row['stop_id'].isascii() for row in rows)
        assert all('<' not in row['stop_desc'] for row in rows)

    def test_timezone_config_refers_to_existing_stations(self):
        assert set(STOP_TIMEZONES) <= set(load_json(STATIONS_FILE))

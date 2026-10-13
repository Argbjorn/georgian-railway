import calendar
from datetime import date

import pytest

from gtfs import routes, trips
from gtfs.services import ms_to_date, service_id
from gtfs.source import load_json, select_routes
from utils import ROUTES_FILE


def ms(d):
    return calendar.timegm(d.timetuple()) * 1000


def train(ref, start, end, name, train_type=None, frequency='daily', start_date=None, end_date=None):
    return {
        'ref': ref,
        'train_type': train_type,
        'operator': 'GR',
        'frequency': frequency,
        'start_date': start_date,
        'end_date': end_date,
        'name:en': name,
        'stations': [{'code': start}, {'code': end}],
    }


class TestServiceId:
    def test_without_dates(self):
        assert service_id(train(1, 'a', 'b', 'A → B')) == 'daily'
        assert service_id(train(1, 'a', 'b', 'A → B', frequency='on workdays')) == 'workdays'

    def test_with_dates(self):
        t = train(1, 'a', 'b', 'A → B', frequency='on odd days',
                  start_date=ms(date(2026, 10, 3)), end_date=ms(date(2027, 4, 30)))
        assert service_id(t) == 'odd_20261003_20270430'

    def test_open_end(self):
        t = train(1, 'a', 'b', 'A → B', frequency='every second day', start_date=ms(date(2025, 6, 2)))
        assert service_id(t) == 'esd_20250602_open'

    def test_open_start(self):
        t = train(1, 'a', 'b', 'A → B', end_date=ms(date(2026, 12, 31)))
        assert service_id(t) == 'daily_open_20261231'

    def test_every_second_day_requires_start_date(self):
        with pytest.raises(ValueError, match='requires start_date'):
            service_id(train(1, 'a', 'b', 'A → B', frequency='every second day'))

    def test_unknown_frequency_fails(self):
        with pytest.raises(ValueError, match='unsupported frequency'):
            service_id(train(1, 'a', 'b', 'A → B', frequency='on full moon'))

    def test_ms_to_date_uses_utc(self):
        assert ms_to_date(1790985600000) == date(2026, 10, 3)
        assert ms_to_date(None) is None


class TestBuildTrips:
    def test_rows(self):
        lines = routes.group_lines([
            train(801, 'batumi', 'tbilisi', 'Batumi → Tbilisi', 'stadler'),
            train(802, 'tbilisi', 'batumi', 'Tbilisi → Batumi', 'stadler'),
        ])
        assert trips.build_trips(lines) == [
            {
                'route_id': 'tbilisi-batumi-stadler',
                'service_id': 'daily',
                'trip_id': '801',
                'trip_headsign': 'Tbilisi',
                'trip_short_name': '801',
                'direction_id': 1,
                'shape_id': '',
                'wheelchair_accessible': 1,
                'bikes_allowed': 0,
                'cars_allowed': 2,
            },
            {
                'route_id': 'tbilisi-batumi-stadler',
                'service_id': 'daily',
                'trip_id': '802',
                'trip_headsign': 'Batumi',
                'trip_short_name': '802',
                'direction_id': 0,
                'shape_id': '',
                'wheelchair_accessible': 1,
                'bikes_allowed': 0,
                'cars_allowed': 2,
            },
        ]

    def test_shape_id_from_mapping(self):
        lines = routes.group_lines([train(801, 'batumi', 'tbilisi', 'Batumi → Tbilisi')])
        [row] = trips.build_trips(lines, {801: '123'})
        assert row['shape_id'] == '123'

    def test_non_stadler_has_no_wheelchair_info(self):
        lines = routes.group_lines([train(617, 'borjomi', 'tbilisi', 'Borjomi → Tbilisi', 'suburban')])
        [row] = trips.build_trips(lines)
        assert row['wheelchair_accessible'] == 0

    def test_headsign_translation(self):
        t = train(617, 'borjomi', 'tbilisi', 'Borjomi → Tbilisi')
        t['name:ru'] = 'Боржоми → Тбилиси'
        assert trips.trip_headsign(t, 'ru') == 'Тбилиси'


class TestRealData:
    def test_builds_from_current_data(self):
        selected = select_routes(load_json(ROUTES_FILE))
        rows = trips.build_trips(routes.group_lines(selected))
        assert sorted(int(row['trip_id']) for row in rows) == sorted(r['ref'] for r in selected)

import pytest

from gtfs import routes, stop_times
from gtfs.source import load_json, select_routes
from utils import ROUTES_FILE


def single_time_train(*times, ref=1):
    """has_arrival_time=false: one time per station, stored as departure_time."""
    return {
        'ref': ref,
        'has_arrival_time': False,
        'stations': [{'code': f's{i}', 'departure_time': t, 'arrival_time': None}
                     for i, t in enumerate(times)],
    }


def arrival_departure_train(*pairs, ref=1):
    """has_arrival_time=true: (arrival, departure) per station."""
    return {
        'ref': ref,
        'has_arrival_time': True,
        'stations': [{'code': f's{i}', 'arrival_time': a, 'departure_time': d}
                     for i, (a, d) in enumerate(pairs)],
    }


def times(rows):
    return [(row['arrival_time'], row['departure_time']) for row in rows]


class TestTimeHelpers:
    @pytest.mark.parametrize('value, expected', [
        ('06:24', 384), ('0:05', 5), ('-', None), ('nn:nn', None), ('', None), (None, None),
    ])
    def test_parse_time(self, value, expected):
        assert stop_times.parse_time(value) == expected

    def test_format_time_beyond_24h(self):
        assert stop_times.format_time(6 * 60 + 24) == '06:24:00'
        assert stop_times.format_time(30 * 60 + 24) == '30:24:00'


class TestSingleTimeTrains:
    def test_arrival_equals_departure(self):
        rows = stop_times.build_trip_stop_times(single_time_train('10:00', '10:30', '11:00'))
        assert times(rows) == [('10:00:00', '10:00:00'), ('10:30:00', '10:30:00'), ('11:00:00', '11:00:00')]

    def test_crossing_midnight(self):
        # Train 37 Tbilisi → Baku
        rows = stop_times.build_trip_stop_times(single_time_train('21:00', '22:55', '00:20', '06:24'))
        assert [row['departure_time'] for row in rows] == ['21:00:00', '22:55:00', '24:20:00', '30:24:00']

    def test_missing_middle_time_left_empty(self):
        rows = stop_times.build_trip_stop_times(single_time_train('10:00', '-', '11:00'))
        assert times(rows)[1] == ('', '')
        assert rows[1]['timepoint'] == 0
        assert rows[0]['timepoint'] == 1

    def test_midnight_after_missing_time(self):
        rows = stop_times.build_trip_stop_times(single_time_train('23:00', '-', '01:00'))
        assert times(rows)[2] == ('25:00:00', '25:00:00')

    @pytest.mark.parametrize('schedule', [('-', '10:00'), ('10:00', '-')])
    def test_missing_terminal_time_fails(self, schedule):
        with pytest.raises(ValueError, match='terminal station'):
            stop_times.build_trip_stop_times(single_time_train(*schedule))

    def test_backward_step_within_day_fails(self):
        with pytest.raises(ValueError, match='backwards'):
            stop_times.build_trip_stop_times(single_time_train('10:10', '10:05'))


class TestArrivalDepartureTrains:
    def test_terminals_mirror_known_time_and_midnight(self):
        # Train 371 Tbilisi → Yerevan (shortened)
        rows = stop_times.build_trip_stop_times(arrival_departure_train(
            ('-', '20:00'), ('23:20', '00:20'), ('02:00', '02:05'), ('06:35', '-')))
        assert times(rows) == [
            ('20:00:00', '20:00:00'),
            ('23:20:00', '24:20:00'),
            ('26:00:00', '26:05:00'),
            ('30:35:00', '30:35:00'),
        ]

    def test_middle_station_with_one_time_mirrors_it(self):
        rows = stop_times.build_trip_stop_times(arrival_departure_train(
            ('-', '10:00'), ('10:30', '-'), ('11:00', '-')))
        assert times(rows)[1] == ('10:30:00', '10:30:00')

    def test_middle_station_without_times_left_empty(self):
        # The train stops here, but neither time is known
        rows = stop_times.build_trip_stop_times(arrival_departure_train(
            ('-', '10:00'), ('-', '-'), ('11:00', '-')))
        assert times(rows)[1] == ('', '')
        assert rows[1]['timepoint'] == 0


class TestTerminalTimes:
    def test_split_by_terminal_times(self):
        trains = [
            single_time_train('10:00', '-', '11:00', ref=1),
            single_time_train('-', '10:30', '11:00', ref=2),
            arrival_departure_train(('-', '10:00'), ('10:30', '10:35'), ('-', '-'), ref=3),
            arrival_departure_train(('-', '10:00'), ('-', '-'), ('11:00', '-'), ref=4),
        ]
        kept, skipped = stop_times.split_by_terminal_times(trains)
        assert [train['ref'] for train in kept] == [1, 4]
        assert skipped == [2, 3]


class TestRowFields:
    def test_row(self):
        train = single_time_train('10:00', '10:30', '11:00', ref=617)
        train['stations'][1]['code'] = 'bakı'
        rows = stop_times.build_trip_stop_times(train)
        assert rows[1] == {
            'trip_id': '617',
            'arrival_time': '10:30:00',
            'departure_time': '10:30:00',
            'stop_id': 'baki',
            'stop_sequence': 2,
            'pickup_type': '',
            'drop_off_type': '',
            'shape_dist_traveled': '',
            'timepoint': 1,
        }

    def test_shape_dist_traveled(self):
        rows = stop_times.build_trip_stop_times(single_time_train('10:00', '10:30', '11:00'), [0.0, None, 950.5])
        assert [row['shape_dist_traveled'] for row in rows] == [0.0, '', 950.5]

    def test_no_drop_off_at_first_and_no_pickup_at_last(self):
        rows = stop_times.build_trip_stop_times(single_time_train('10:00', '10:30', '11:00'))
        assert [(row['pickup_type'], row['drop_off_type']) for row in rows] == [('', 1), ('', ''), (1, '')]


class TestRealData:
    def test_builds_from_current_data(self):
        selected = select_routes(load_json(ROUTES_FILE))
        rows = stop_times.build_stop_times(routes.group_lines(selected))
        assert len(rows) == sum(len(train['stations']) for train in selected)
        assert {row['trip_id'] for row in rows} == {str(train['ref']) for train in selected}

    def test_duration_matches_travel_time(self):
        # travel_time is computed independently by make_routes_files
        def minutes(value):
            hours, mins, *_ = map(int, value.split(':'))
            return hours * 60 + mins

        for train in select_routes(load_json(ROUTES_FILE)):
            if train.get('travel_time') in (None, '-'):
                continue
            rows = stop_times.build_trip_stop_times(train)
            duration = minutes(rows[-1]['arrival_time']) - minutes(rows[0]['departure_time'])
            assert duration == minutes(train['travel_time']), f'Train {train["ref"]}'

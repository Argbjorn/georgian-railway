import json

import pytest

from config import ROUTES_GEODATA_DIR
from gtfs import shapes
from gtfs.shapes import chain_ways, distance_m, orient_to_stations, project_stops
from gtfs.source import load_json, select_routes
from utils import ROUTES_FILE, STATIONS_FILE

# Points along a meridian, ~111 m apart
P = [(41.0 + i * 0.001, 44.0) for i in range(6)]


def write_relation(directory, relation_id, ways):
    members = [{'type': 'way', 'ref': i, 'role': '',
                'geometry': [{'lat': lat, 'lon': lon} for lat, lon in way]} for i, way in enumerate(ways)]
    members.append({'type': 'node', 'ref': 99, 'role': 'stop', 'lat': 0, 'lon': 0})
    (directory / f'{relation_id}.json').write_text(json.dumps({'members': members}), encoding='utf-8')


def train(ref, relation_id, first='a', last='b'):
    return {'ref': ref, 'id': relation_id, 'stations': [{'code': first}, {'code': last}]}


STATIONS = {'a': {'coords': list(P[0])}, 'b': {'coords': list(P[-1])}}


class TestDistance:
    def test_one_thousandth_degree_of_latitude(self):
        assert distance_m(P[0], P[1]) == pytest.approx(111.2, abs=0.1)


class TestChainWays:
    def test_ways_in_order(self):
        points, gaps = chain_ways([P[0:3], P[2:6]])
        assert points == P and gaps == []

    def test_reversed_ways_are_flipped(self):
        points, _ = chain_ways([P[2::-1], P[5:1:-1]])  # both ways drawn backwards
        assert points == P

    def test_gap_reported_and_bridged(self):
        points, gaps = chain_ways([P[0:2], P[3:6]])
        assert points == P[0:2] + P[3:6]
        assert gaps == [222]

    def test_empty(self):
        assert chain_ways([]) == ([], [])


class TestOrientToStations:
    def test_reversed_when_running_backwards(self):
        assert orient_to_stations(P[::-1], P[0], P[-1]) == P

    def test_kept_when_running_forward(self):
        assert orient_to_stations(P, P[0], P[-1]) == P


class TestBuildShapes:
    def test_rows_and_cumulative_distance(self, tmp_path):
        write_relation(tmp_path, 100, [P[5:2:-1], P[3::-1]])  # drawn from b to a
        rows, shape_ids, warnings = shapes.build_shapes([train(1, 100)], STATIONS, tmp_path)
        assert shape_ids == {1: '100'} and warnings == []
        assert [(row['shape_pt_lat'], row['shape_pt_lon']) for row in rows] == P
        assert [row['shape_pt_sequence'] for row in rows] == [1, 2, 3, 4, 5, 6]
        assert rows[0]['shape_dist_traveled'] == 0
        assert rows[-1]['shape_dist_traveled'] == pytest.approx(5 * 111.2, abs=0.5)

    def test_missing_geodata_gives_no_shape(self, tmp_path):
        rows, shape_ids, warnings = shapes.build_shapes([train(1, 404)], STATIONS, tmp_path)
        assert rows == [] and shape_ids == {}
        assert 'no geodata' in warnings[0]

    def test_shared_relation_same_direction_reused(self, tmp_path):
        write_relation(tmp_path, 100, [P])
        rows, shape_ids, warnings = shapes.build_shapes([train(1, 100), train(2, 100)], STATIONS, tmp_path)
        assert shape_ids == {1: '100', 2: '100'}
        assert len(rows) == len(P) and warnings == []

    def test_shared_relation_opposite_direction_rejected(self, tmp_path):
        write_relation(tmp_path, 100, [P])
        _, shape_ids, warnings = shapes.build_shapes(
            [train(1, 100), train(2, 100, first='b', last='a')], STATIONS, tmp_path)
        assert shape_ids == {1: '100'}
        assert 'opposite direction' in warnings[0]


def shape_points(points):
    rows = shapes.shape_rows('s', points)
    return [(row['shape_pt_lat'], row['shape_pt_lon'], row['shape_dist_traveled']) for row in rows]


class TestProjectStops:
    def test_stop_on_vertex_and_between_vertices(self):
        line = shape_points(P)
        [(a, _), (b, offset_b)] = project_stops(line, [P[0], (41.0025, 44.0)])
        assert a == 0
        assert b == pytest.approx(2.5 * 111.2, abs=0.5)
        assert offset_b == pytest.approx(0, abs=0.1)

    def test_offset_of_stop_beside_the_line(self):
        [(along, offset)] = project_stops(shape_points(P), [(41.002, 44.001)])
        assert along == pytest.approx(2 * 111.2, abs=0.5)
        assert offset == pytest.approx(84, abs=1)  # 0.001° of longitude at 41°N

    def test_stops_do_not_jump_back(self):
        # A line going north and coming back south next to itself. The second stop is exactly
        # between both directions; an unrestricted search would pick the earlier, outbound part
        out_and_back = P + [(lat, 44.0001) for lat, _ in reversed(P)]
        [(first, _), (second, _)] = project_stops(shape_points(out_and_back), [P[5], (41.002, 44.00005)])
        assert second > first


class TestStopDistances:
    def test_non_increasing_value_left_empty(self, tmp_path):
        write_relation(tmp_path, 100, [P])
        stations = {**STATIONS, 'c': {'coords': list(P[1])}}
        t = {'ref': 1, 'id': 100, 'stations': [{'code': 'a'}, {'code': 'c'}, {'code': 'a'}, {'code': 'b'}]}
        rows, shape_ids, _ = shapes.build_shapes([t], stations, tmp_path)
        distances, warnings = shapes.stop_distances([t], stations, rows, shape_ids)
        assert distances[1][0] == 0 and distances[1][2] is None
        assert distances[1][1] < distances[1][3]
        assert 'does not advance' in warnings[0]

    def test_far_station_reported(self, tmp_path):
        write_relation(tmp_path, 100, [P])
        stations = {**STATIONS, 'far': {'coords': [41.002, 44.02]}}
        t = {'ref': 1, 'id': 100, 'stations': [{'code': 'a'}, {'code': 'far'}, {'code': 'b'}]}
        rows, shape_ids, _ = shapes.build_shapes([t], stations, tmp_path)
        _, warnings = shapes.stop_distances([t], stations, rows, shape_ids)
        assert 'far' in warnings[0] and 'from the shape' in warnings[0]

    def test_train_without_shape_skipped(self):
        assert shapes.stop_distances([train(1, 404)], STATIONS, [], {}) == ({}, [])


class TestRealData:
    def test_shapes_start_and_end_near_terminal_stations(self):
        trains = select_routes(load_json(ROUTES_FILE))
        stations = load_json(STATIONS_FILE)
        rows, shape_ids, _ = shapes.build_shapes(trains, stations, ROUTES_GEODATA_DIR)
        assert shape_ids
        points = {}
        for row in rows:
            points.setdefault(row['shape_id'], []).append((row['shape_pt_lat'], row['shape_pt_lon']))
        for t in trains:
            if t['ref'] not in shape_ids:
                continue
            line = points[shape_ids[t['ref']]]
            first = stations[t['stations'][0]['code']]['coords']
            last = stations[t['stations'][-1]['code']]['coords']
            assert distance_m(line[0], first) < 500, f'Train {t["ref"]}: shape start far from first station'
            assert distance_m(line[-1], last) < 500, f'Train {t["ref"]}: shape end far from last station'

    def test_every_stop_projects_close_and_in_order(self):
        trains = select_routes(load_json(ROUTES_FILE))
        stations = load_json(STATIONS_FILE)
        rows, shape_ids, _ = shapes.build_shapes(trains, stations, ROUTES_GEODATA_DIR)
        distances, warnings = shapes.stop_distances(trains, stations, rows, shape_ids)
        assert warnings == []
        for ref, values in distances.items():
            assert None not in values, f'Train {ref}'
            assert values == sorted(set(values)), f'Train {ref}: distances not strictly increasing'

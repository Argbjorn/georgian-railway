"""shapes.txt — train paths built from the OSM route relations in static/data/routes_geodata/."""

import json
import math
import os

FILE_NAME = 'shapes.txt'
FIELDS = ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled']
REQUIRED_FIELDS = {'shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'}

EARTH_RADIUS_M = 6371000
# Consecutive ways whose ends are farther apart than this are reported as a gap in the relation.
MAX_JOINT_GAP_M = 50
# A station farther than this from its train's shape is reported (likely a wrong relation or stop).
MAX_STOP_OFFSET_M = 500


def distance_m(a, b):
    """Haversine distance between two (lat, lon) points in metres."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def load_relation_ways(geodata_dir, relation_id):
    """Way geometries of the route relation in member order, or None if there is no geodata file."""
    path = os.path.join(geodata_dir, f'{relation_id}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        relation = json.load(f)
    return [[(point['lat'], point['lon']) for point in member['geometry']]
            for member in relation['members'] if member['type'] == 'way']


def chain_ways(ways):
    """Joins ways into one polyline, flipping each way to continue from the end of the previous.

    Returns (points, gaps), where gaps are distances (m) of joints wider than MAX_JOINT_GAP_M;
    such joints are bridged by a straight segment.
    """
    ways = [way for way in ways if way]
    if not ways:
        return [], []

    first = ways[0]
    if len(ways) > 1:
        # Orient the first way so that its end is the one closer to the second way
        nearest_to_next = lambda point: min(distance_m(point, ways[1][0]), distance_m(point, ways[1][-1]))
        if nearest_to_next(first[0]) < nearest_to_next(first[-1]):
            first = first[::-1]

    points, gaps = list(first), []
    for way in ways[1:]:
        end = points[-1]
        if distance_m(end, way[-1]) < distance_m(end, way[0]):
            way = way[::-1]
        gap = distance_m(end, way[0])
        if gap > MAX_JOINT_GAP_M:
            gaps.append(round(gap))
        points.extend(way)

    deduplicated = [points[0]] + [point for prev, point in zip(points, points[1:]) if point != prev]
    return deduplicated, gaps


def orient_to_stations(points, first_station, last_station):
    """Reverses the polyline if it runs from the last station towards the first one."""
    forward = distance_m(points[0], first_station) + distance_m(points[-1], last_station)
    backward = distance_m(points[-1], first_station) + distance_m(points[0], last_station)
    return points[::-1] if backward < forward else points


def shape_rows(shape_id, points):
    rows = []
    travelled = 0.0
    for index, point in enumerate(points):
        if index:
            travelled += distance_m(points[index - 1], point)
        rows.append({
            'shape_id': shape_id,
            'shape_pt_lat': point[0],
            'shape_pt_lon': point[1],
            'shape_pt_sequence': index + 1,
            'shape_dist_traveled': round(travelled, 1),
        })
    return rows


def _project(point, a, b):
    """(distance in m from `point` to segment a–b, position 0..1 of the nearest point on it).

    Uses a local plane around `point`, accurate enough for segments of a railway polyline.
    """
    scale_y = math.radians(1) * EARTH_RADIUS_M
    scale_x = scale_y * math.cos(math.radians(point[0]))
    ax, ay = (a[1] - point[1]) * scale_x, (a[0] - point[0]) * scale_y
    bx, by = (b[1] - point[1]) * scale_x, (b[0] - point[0]) * scale_y
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / length_sq))
    return math.hypot(ax + t * dx, ay + t * dy), t


def project_stops(shape_points, stop_coords):
    """Distance along the shape (m) and offset from it (m) for each stop, in stop order.

    `shape_points` are (lat, lon, shape_dist_traveled). Each stop is searched on the part of the
    shape from the previous stop's segment onwards, so stops cannot jump back along the line.
    """
    result = []
    start = 0
    for coords in stop_coords:
        best = None
        for i in range(start, len(shape_points) - 1):
            offset, t = _project(coords, shape_points[i][:2], shape_points[i + 1][:2])
            if best is None or offset < best[0]:
                best = (offset, i, t)
        offset, i, t = best
        along = shape_points[i][2] + t * (shape_points[i + 1][2] - shape_points[i][2])
        result.append((round(along, 1), offset))
        start = i
    return result


def stop_distances(trains, stations, rows, shape_ids):
    """Returns ({train ref: [shape_dist_traveled or None per stop]}, warnings).

    GTFS requires strictly increasing distances along a trip; a value not greater than the
    previous one is left empty.
    """
    points_by_shape = {}
    for row in rows:
        points_by_shape.setdefault(row['shape_id'], []).append(
            (row['shape_pt_lat'], row['shape_pt_lon'], row['shape_dist_traveled']))

    distances, warnings = {}, []
    for train in trains:
        if train['ref'] not in shape_ids:
            continue
        codes = [station['code'] for station in train['stations']]
        projected = project_stops(points_by_shape[shape_ids[train['ref']]],
                                  [stations[code]['coords'] for code in codes])
        values, last = [], None
        for code, (along, offset) in zip(codes, projected):
            if offset > MAX_STOP_OFFSET_M:
                warnings.append(f'Train {train["ref"]}: station {code} is {round(offset)} m from the shape')
            if last is not None and along <= last:
                warnings.append(f'Train {train["ref"]}: station {code} does not advance along the shape, '
                                f'no shape_dist_traveled')
                values.append(None)
                continue
            values.append(along)
            last = along
        distances[train['ref']] = values
    return distances, warnings


def build_shapes(trains, stations, geodata_dir):
    """Returns (rows, {train ref: shape_id}, warnings). One shape per OSM relation (train `id`)."""
    rows, shape_ids, warnings = [], {}, []
    # shape_id → first station code of the train the shape was oriented for
    built = {}
    for train in sorted(trains, key=lambda t: t['ref']):
        shape_id = str(train['id'])
        first_code = train['stations'][0]['code']
        if shape_id in built:
            if built[shape_id] == first_code:
                shape_ids[train['ref']] = shape_id
            else:
                warnings.append(f'Train {train["ref"]}: relation {shape_id} is shared with a train in the '
                                f'opposite direction, no shape')
            continue

        ways = load_relation_ways(geodata_dir, shape_id)
        if ways is None:
            warnings.append(f'Train {train["ref"]}: no geodata file for relation {shape_id}, no shape')
            continue
        points, gaps = chain_ways(ways)
        if len(points) < 2:
            warnings.append(f'Train {train["ref"]}: relation {shape_id} has no way geometry, no shape')
            continue
        if gaps:
            warnings.append(f'Train {train["ref"]}: relation {shape_id} has gaps between ways (m): {gaps}')

        first_station = stations[first_code]['coords']
        last_station = stations[train['stations'][-1]['code']]['coords']
        rows.extend(shape_rows(shape_id, orient_to_stations(points, first_station, last_station)))
        built[shape_id] = first_code
        shape_ids[train['ref']] = shape_id

    return rows, shape_ids, warnings

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
from utils.overpass_handler import OverpassHandler
from utils.string_utils import make_station_code

gr_workbook = GeoRoutesExcelHandler()
overpass = OverpassHandler()


def station_lists_diff(local_stations, osm_stations):
    local_set, osm_set = set(local_stations), set(osm_stations)
    if local_set == osm_set:
        return False, None, None
    local_diff = [s for s in local_stations if s not in osm_set]
    osm_diff = [s for s in osm_stations if s not in local_set]
    return True, local_diff, osm_diff


def check_all_routes():
    active_routes = [
        r for r in gr_workbook.routes_json
        if r.get('active') == 'y' and gr_workbook.is_sheet_exists(r['ref'])
    ]

    osm_id_to_ref = {int(r['id']): r['ref'] for r in active_routes}

    stops_data = overpass.get_route_stops_data(list(osm_id_to_ref.keys()))
    routes = [e for e in stops_data['elements'] if e['type'] == 'relation']
    stops = [e for e in stops_data['elements'] if e['type'] == 'node']

    route_stop_ids = {}
    for route in routes:
        route_stop_ids[route['id']] = [m['ref'] for m in route['members'] if m['type'] == 'node' and m['role'] == 'stop']

    station_code_by_id = {}
    for s in stops:
        if 'tags' in s and 'name:en' in s['tags']:
            station_code_by_id[s['id']] = make_station_code(s['tags']['name:en'])
        else:
            station_code_by_id[s['id']] = f'unknownstation{s["id"]}'

    diffs = []
    for osm_id, route_ref in osm_id_to_ref.items():
        existing = gr_workbook.get_route_stations(route_ref)
        actual = [station_code_by_id.get(sid, f'unknownstation{sid}') for sid in route_stop_ids.get(osm_id, [])]
        has_diff, local_diff, osm_diff = station_lists_diff(existing, actual)
        if has_diff:
            diffs.append((route_ref, local_diff, osm_diff))

    if not diffs:
        print('All routes are consistent with OSM')
    else:
        for route_ref, local_diff, osm_diff in diffs:
            print(f'Route {route_ref} requires a manual check')
            print(f'  Only in local data: {local_diff}')
            print(f'  Only in OSM: {osm_diff}')


if __name__ == '__main__':
    check_all_routes()

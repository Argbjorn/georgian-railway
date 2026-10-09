# Builds the GTFS feed from data/routes.json and data/stations.json (run after make_routes_files
# and make_stations_files). Field mapping and decisions: scripts/GTFS.md.
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ROUTES_JSON_PATH, STATIONS_JSON_PATH, DIRECTIONS_CONTENT_DIR, GTFS_BUILD_DIR
from gtfs import agency, routes as gtfs_routes, stops
from gtfs.source import load_direction_pages, load_json, select_routes
from gtfs.writer import write_table


def make_gtfs(output_dir=GTFS_BUILD_DIR):
    routes = select_routes(load_json(ROUTES_JSON_PATH))
    stations = load_json(STATIONS_JSON_PATH)
    lines = gtfs_routes.group_lines(routes)
    direction_pages = load_direction_pages(DIRECTIONS_CONTENT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    tables = [
        (agency, agency.build_agency(routes)),
        (stops, stops.build_stops(routes, stations)),
        (gtfs_routes, gtfs_routes.build_routes(lines, direction_pages)),
    ]
    for table, rows in tables:
        write_table(os.path.join(output_dir, table.FILE_NAME), table.FIELDS, rows, table.REQUIRED_FIELDS)

    print(f'GTFS files written to {output_dir}')


if __name__ == '__main__':
    make_gtfs()

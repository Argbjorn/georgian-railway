# Builds the GTFS feed from data/routes.json and data/stations.json (run after make_routes_files
# and make_stations_files). Field mapping and decisions: scripts/GTFS.md.
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ROUTES_JSON_PATH, GTFS_BUILD_DIR
from gtfs import agency
from gtfs.source import load_json, select_routes
from gtfs.writer import write_table


def make_gtfs(output_dir=GTFS_BUILD_DIR):
    routes = select_routes(load_json(ROUTES_JSON_PATH))
    os.makedirs(output_dir, exist_ok=True)

    write_table(os.path.join(output_dir, agency.FILE_NAME),
                agency.FIELDS, agency.build_agency(routes), agency.REQUIRED_FIELDS)

    print(f'GTFS files written to {output_dir}')


if __name__ == '__main__':
    make_gtfs()

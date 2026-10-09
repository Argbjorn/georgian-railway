# Builds the GTFS feed from data/routes.json and data/stations.json (run after make_routes_files
# and make_stations_files). Field mapping and decisions: scripts/GTFS.md.
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ROUTES_JSON_PATH, STATIONS_JSON_PATH, DIRECTIONS_CONTENT_DIR, GTFS_BUILD_DIR
from gtfs import agency, calendar, calendar_dates, feed_info, routes as gtfs_routes, stop_times, stops, trips
from gtfs.services import feed_window, split_by_service, unique_services
from gtfs.source import load_direction_pages, load_json, select_routes
from gtfs.writer import write_table


def make_gtfs(output_dir=GTFS_BUILD_DIR, today=None):
    window = feed_window(today)
    routes, idle_refs = split_by_service(select_routes(load_json(ROUTES_JSON_PATH)), window)
    if idle_refs:
        print(f'Trains without service days in {window.start}..{window.end}, skipped: {idle_refs}')
    stations = load_json(STATIONS_JSON_PATH)
    lines = gtfs_routes.group_lines(routes)
    services = unique_services(routes, window)
    direction_pages = load_direction_pages(DIRECTIONS_CONTENT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    tables = [
        (agency, agency.build_agency(routes)),
        (stops, stops.build_stops(routes, stations)),
        (gtfs_routes, gtfs_routes.build_routes(lines, direction_pages)),
        (trips, trips.build_trips(lines)),
        (stop_times, stop_times.build_stop_times(lines)),
        (calendar, calendar.build_calendar(services)),
        (calendar_dates, calendar_dates.build_calendar_dates(services)),
    ]
    written = []
    for table, rows in tables:
        path = os.path.join(output_dir, table.FILE_NAME)
        if rows:
            write_table(path, table.FIELDS, rows, table.REQUIRED_FIELDS)
            written.append(path)
        elif os.path.exists(path):
            # An empty optional table is omitted rather than written as a header-only file
            os.remove(path)

    # Written last: its version is a hash of the other files
    version = feed_info.feed_version(window, written)
    write_table(os.path.join(output_dir, feed_info.FILE_NAME), feed_info.FIELDS,
                feed_info.build_feed_info(window, version), feed_info.REQUIRED_FIELDS)

    print(f'GTFS feed for {window.start}..{window.end} written to {output_dir}')


if __name__ == '__main__':
    make_gtfs()

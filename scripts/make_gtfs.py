# Builds the GTFS feed from data/routes.json and data/stations.json (run after make_routes_files
# and make_stations_files). Feed files are written to build/gtfs/ and zipped into
# static/gtfs/georgian-railway.zip, which Hugo publishes with the site. Field mapping and decisions:
# scripts/GTFS.md.
import os
import sys
import zipfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (ROUTES_JSON_PATH, STATIONS_JSON_PATH, DIRECTIONS_CONTENT_DIR, ROUTES_GEODATA_DIR, GTFS_BUILD_DIR,
                    GTFS_ZIP_PATH)
from gtfs import (agency, attributions, calendar, calendar_dates, feed_info, routes as gtfs_routes, shapes, stop_times,
                  stops, translations, trips)
from gtfs.services import feed_window, split_by_service, unique_services
from gtfs.source import load_direction_pages, load_json, select_routes
from gtfs.writer import write_table


def write_zip(zip_path, paths):
    """Zips the feed files into the archive root (GTFS forbids subfolders)."""
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, arcname=os.path.basename(path))


def make_gtfs(output_dir=GTFS_BUILD_DIR, zip_path=GTFS_ZIP_PATH, today=None):
    window = feed_window(today)
    routes, idle_refs = split_by_service(select_routes(load_json(ROUTES_JSON_PATH)), window)
    if idle_refs:
        print(f'Trains without service days in {window.start}..{window.end}, skipped: {idle_refs}')
    stations = load_json(STATIONS_JSON_PATH)
    lines = gtfs_routes.group_lines(routes)
    services = unique_services(routes, window)
    direction_pages = load_direction_pages(DIRECTIONS_CONTENT_DIR)
    shape_rows, shape_ids, shape_warnings = shapes.build_shapes(routes, stations, ROUTES_GEODATA_DIR)
    stop_distances, distance_warnings = shapes.stop_distances(routes, stations, shape_rows, shape_ids)
    for warning in shape_warnings + distance_warnings:
        print(f'Warning: {warning}')
    agency_rows = agency.build_agency(routes)
    os.makedirs(output_dir, exist_ok=True)

    tables = [
        (agency, agency_rows),
        (stops, stops.build_stops(routes, stations)),
        (gtfs_routes, gtfs_routes.build_routes(lines, direction_pages)),
        (trips, trips.build_trips(lines, shape_ids)),
        (stop_times, stop_times.build_stop_times(lines, stop_distances)),
        (calendar, calendar.build_calendar(services)),
        (calendar_dates, calendar_dates.build_calendar_dates(services)),
        (shapes, shape_rows),
        (translations, translations.build_translations(agency_rows, routes, stations, lines, direction_pages)),
        (attributions, attributions.build_attributions(agency_rows)),
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
    feed_info_path = os.path.join(output_dir, feed_info.FILE_NAME)
    write_table(feed_info_path, feed_info.FIELDS, feed_info.build_feed_info(window, version),
                feed_info.REQUIRED_FIELDS)

    # Only the files of this build: output_dir may contain stale or unrelated files
    write_zip(zip_path, written + [feed_info_path])
    print(f'GTFS feed {version} for {window.start}..{window.end} written to {zip_path}')


if __name__ == '__main__':
    make_gtfs()

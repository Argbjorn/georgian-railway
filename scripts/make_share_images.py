# Builds the share-preview images (og:image) in static/images/share/, published with the site:
#   home-<lang>.png         home page, one per language (has text)
#   routes-list.png         the routes list: every passenger line in red
#   routes/<ref>.png        active routes: the route in red, start and end stations
#   stations/<code>.png     stations inside Georgia: the station point
#   stations-list.png       the stations list: every station inside Georgia
#   trains/<type>.jpg       train pages: the cover photo of photos.yaml
#   trains-list.jpg         the trains list and trains without photos: 2x2 collage of covers
# The images are committed. By default only missing ones are drawn (a new route or station); CI
# runs it in every deploy workflow and commits what it adds. --force redraws everything: after a
# change of style, or delete a single file to redraw it (e.g. a route whose path changed, a new
# cover photo; the collage after a change of the first four trains).
# Run after make_routes_files, make_stations_files and make_routes_geo_files. Hugo links an image
# only if its file exists (see the routes/stations _content*.gotmpl).
#
#   python scripts/make_share_images.py [--force]
import argparse
import functools
import glob
import json
import os
import sys
import time

from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (ROUTES_GEODATA_DIR, ROUTES_JSON_PATH, SHARE_IMAGES_DIR, STATIONS_JSON_PATH,
                    TRAINS_CONTENT_DIR, TRAINS_PHOTOS_DIR)
from share_images import frame, render, trains
from share_images.geometry import inside


def save(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith('.jpg'):
        image.save(path, quality=85, optimize=True, progressive=True)
        return
    # A 256-colour palette halves the file. Median cut keeps the white land and the shadow
    # gradient clean; the default octree method bands the shadow and tints the land.
    image.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)


def station_point(station, ring):
    """Station position in frame pixels, or None if it is outside Georgia."""
    lat, lon = station['coords']
    point = frame.project(lon, lat)
    return point if inside(point, ring) else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='redraw existing images too')
    args = parser.parse_args()

    started = time.time()
    with open(ROUTES_JSON_PATH, encoding='utf-8') as f:
        routes = json.load(f)
    with open(STATIONS_JSON_PATH, encoding='utf-8') as f:
        stations = json.load(f)
    ring = render.georgia_ring()

    route_ways = {}
    for path in glob.glob(os.path.join(ROUTES_GEODATA_DIR, '*.json')):
        route_ways[os.path.splitext(os.path.basename(path))[0]] = render.route_ways(path)

    # The shared parts are computed only if something is missing.
    @functools.cache
    def passenger():
        all_ways = {ref: way for ways in route_ways.values() for ref, way in ways.items()}
        return render.railway_lines(list(all_ways.values()), ring)

    @functools.cache
    def base():
        return render.whole_base(ring, passenger())

    def needed(path):
        return args.force or not os.path.exists(path)

    drawn = []

    for lang in render.HOME_TEXT:
        path = os.path.join(SHARE_IMAGES_DIR, f'home-{lang}.png')
        if needed(path):
            save(render.home_image(lang, ring, passenger()), path)
            drawn.append(path)

    path = os.path.join(SHARE_IMAGES_DIR, 'routes-list.png')
    if needed(path):
        save(render.routes_list_image(base(), passenger()), path)
        drawn.append(path)

    for route in routes:
        ways = route_ways.get(str(route['id']))
        if not route.get('active') or not ways or not route.get('stations'):
            continue
        path = os.path.join(SHARE_IMAGES_DIR, 'routes', f'{route["ref"]}.png')
        if not needed(path):
            continue
        # The route itself keeps its short pieces: they may be its real start or end.
        lines = render.railway_lines(list(ways.values()), ring, drop_short_dead_ends=False)
        ends = [station_point(stations[s['code']], ring) if s['code'] in stations else None
                for s in (route['stations'][0], route['stations'][-1])]
        save(render.route_image(base(), lines, ends), path)
        drawn.append(path)

    for code, station in stations.items():
        path = os.path.join(SHARE_IMAGES_DIR, 'stations', f'{code}.png')
        point = station_point(station, ring)
        if point and needed(path):
            save(render.station_image(base(), point), path)
            drawn.append(path)

    path = os.path.join(SHARE_IMAGES_DIR, 'stations-list.png')
    if needed(path):
        points = [p for p in (station_point(s, ring) for s in stations.values()) if p]
        save(render.stations_list_image(base(), points), path)
        drawn.append(path)

    covers = trains.train_covers(TRAINS_PHOTOS_DIR, TRAINS_CONTENT_DIR)
    for train_type, cover in covers:
        path = os.path.join(SHARE_IMAGES_DIR, 'trains', f'{train_type}.jpg')
        if cover and needed(path):
            save(trains.cover_image(cover), path)
            drawn.append(path)
    path = os.path.join(SHARE_IMAGES_DIR, 'trains-list.jpg')
    if needed(path):
        save(trains.collage_image([cover for _, cover in covers if cover]), path)
        drawn.append(path)

    for path in drawn:
        print(f'drawn: {os.path.relpath(path, SHARE_IMAGES_DIR)}')
    print(f'{SHARE_IMAGES_DIR}: {len(drawn)} image(s) drawn in {time.time() - started:.0f}s')


if __name__ == '__main__':
    main()

# Builds scripts/share_images/basemap.json: the outline of Georgia for the share-preview images,
# simplified for the image frame, from Natural Earth (public domain, no attribution required).
# Run by hand when the frame (share_images/frame.py) changes; the result is committed, so CI
# does not download Natural Earth.
#
#   python scripts/make_share_basemap.py [--preview path.png]
import argparse
import json
import os
import sys

import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from share_images import frame
from share_images.geometry import clip_ring, ring_area, simplify_ring
from share_images.render import BASEMAP_PATH, WHOLE, Canvas, draw_land, georgia_ring

NATURAL_EARTH_URL = ('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
                     'geojson/ne_10m_admin_0_countries.geojson')

# The clip rectangle sticks out of the image, so the cut edges and their outlines stay off-canvas.
CLIP_MARGIN_PX = 20
SIMPLIFY_TOLERANCE_PX = 0.6
MIN_RING_AREA_PX = 4


def outer_rings(geometry):
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return [polygon[0] for polygon in polygons]


def frame_lonlat_bounds():
    lon_min, lat_max = frame.unproject(-CLIP_MARGIN_PX, -CLIP_MARGIN_PX)
    lon_max, lat_min = frame.unproject(frame.WIDTH + CLIP_MARGIN_PX, frame.HEIGHT + CLIP_MARGIN_PX)
    return lon_min, lat_min, lon_max, lat_max


def prepare_ring(ring):
    """Lon/lat ring -> clipped, simplified ring back in lon/lat, or None if nothing is left in the frame."""
    lon_min, lat_min, lon_max, lat_max = frame_lonlat_bounds()
    lons, lats = [p[0] for p in ring], [p[1] for p in ring]
    # Also keeps far-away polar rings out of the Mercator projection.
    if max(lons) < lon_min or min(lons) > lon_max or max(lats) < lat_min or min(lats) > lat_max:
        return None
    projected = [frame.project(lon, lat) for lon, lat in ring]
    if projected[0] == projected[-1]:
        projected = projected[:-1]
    clipped = clip_ring(projected, -CLIP_MARGIN_PX, -CLIP_MARGIN_PX,
                        frame.WIDTH + CLIP_MARGIN_PX, frame.HEIGHT + CLIP_MARGIN_PX)
    if len(clipped) < 3 or ring_area(clipped) < MIN_RING_AREA_PX:
        return None
    simplified = simplify_ring(clipped, SIMPLIFY_TOLERANCE_PX)
    if len(simplified) < 3:
        return None
    return [[round(lon, 4), round(lat, 4)] for lon, lat in (frame.unproject(x, y) for x, y in simplified)]


def build_basemap(countries):
    rings = []
    for feature in countries['features']:
        if feature['properties']['ADMIN'] == 'Georgia':
            rings = [r for r in (prepare_ring(ring) for ring in outer_rings(feature['geometry'])) if r]
    if len(rings) != 1:
        raise RuntimeError(f'expected one outline of Georgia in Natural Earth data, got {len(rings)}')
    return {'source': NATURAL_EARTH_URL, 'georgia': rings[0]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', help='also render the outline alone to this PNG')
    args = parser.parse_args()

    response = requests.get(NATURAL_EARTH_URL, timeout=120)
    response.raise_for_status()
    basemap = build_basemap(response.json())

    with open(BASEMAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(basemap, f, separators=(',', ':'))
    print(f'{BASEMAP_PATH}: {len(basemap["georgia"])} points')

    if args.preview:
        canvas = Canvas()
        draw_land(canvas, georgia_ring(), WHOLE)
        canvas.finish().save(args.preview)
        print(f'preview: {args.preview}')

if __name__ == '__main__':
    main()

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RAILWAY_NETWORK_JS_PATH
from utils.overpass_handler import OverpassHandler

QUERY = """[out:json][timeout:25];
( area(id:3600028699); )->.searchArea;
way["railway"="rail"]["usage"!="industrial"]["service"!="spur"]["service"!="yard"]["service"!="siding"](area.searchArea);
out skel geom;"""

OUTPUT_PATH = RAILWAY_NETWORK_JS_PATH
# 5 decimal places is ~1 m
COORD_PRECISION = 5

overpass = OverpassHandler()


def overpass_to_geojson(data):
    # The frontend draws the whole network as one layer with one style and uses no properties,
    # so all ways are packed into a single MultiLineString feature to keep the file small
    lines = []
    for element in data.get('elements', []):
        if element.get('type') != 'way':
            continue
        geom = element.get('geometry', [])
        if not geom:
            continue
        lines.append([[round(p['lon'], COORD_PRECISION), round(p['lat'], COORD_PRECISION)] for p in geom])

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "MultiLineString", "coordinates": lines},
        }],
    }


def update_file(data):
    geojson = overpass_to_geojson(data)
    content = "export const railwayNetworkData = " + json.dumps(geojson, separators=(',', ':'))
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"railway-network-data.js updated")


if __name__ == '__main__':
    data = overpass.get_data(QUERY)
    update_file(data)

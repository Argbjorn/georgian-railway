import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RAILWAY_NETWORK_JS_PATH
from utils.overpass_handler import OverpassHandler

KUKUSHKA_WIKIDATA = 'Q3650431'

# The Kukushka set is subtracted from the main network so a way matching both is drawn once.
# The main network is output without tags, the Kukushka with them: ways are told apart by the wikidata tag
QUERY = f"""[out:json][timeout:25];
( area(id:3600028699); )->.searchArea;
way["railway"]["wikidata"="{KUKUSHKA_WIKIDATA}"](area.searchArea)->.kukushka;
(
  way["railway"="rail"]["usage"!="industrial"]["service"!="spur"]["service"!="yard"]["service"!="siding"](area.searchArea);
  - .kukushka;
);
out skel geom;
.kukushka out geom;"""

OUTPUT_PATH = RAILWAY_NETWORK_JS_PATH
# 5 decimal places is ~1 m
COORD_PRECISION = 5

overpass = OverpassHandler()


def multiline_feature(lines, properties):
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "MultiLineString", "coordinates": lines},
    }


def overpass_to_geojson(data):
    # To keep the file small, ways are packed into one MultiLineString feature per style:
    # the main network and the Kukushka line (drawn in its own colour, marked by the "kind" property)
    network_lines = []
    kukushka_lines = []
    for element in data.get('elements', []):
        if element.get('type') != 'way':
            continue
        geom = element.get('geometry', [])
        if not geom:
            continue
        line = [[round(p['lon'], COORD_PRECISION), round(p['lat'], COORD_PRECISION)] for p in geom]
        if element.get('tags', {}).get('wikidata') == KUKUSHKA_WIKIDATA:
            kukushka_lines.append(line)
        else:
            network_lines.append(line)

    if not kukushka_lines:
        print("WARNING: no Kukushka ways returned by Overpass")

    # The Kukushka feature goes last so it is drawn on top of the main network
    features = [multiline_feature(network_lines, {})]
    if kukushka_lines:
        features.append(multiline_feature(kukushka_lines, {"kind": "kukushka"}))
    return {"type": "FeatureCollection", "features": features}


def update_file(data):
    geojson = overpass_to_geojson(data)
    content = "export const railwayNetworkData = " + json.dumps(geojson, separators=(',', ':'))
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"railway-network-data.js updated")


if __name__ == '__main__':
    data = overpass.get_data(QUERY)
    update_file(data)

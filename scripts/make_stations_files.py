# make_stations_json() обновляет stations-list.js, который используется на фронте для отрисовки станций, а также на
# бэке в make_routes_files.py для названий станций на разных языках.
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config import STATIONS_LIST_JS_PATH, STATIONS_JSON_PATH, ROUTES_JSON_PATH
from utils.geo_routes_excel_handler import GeoRoutesExcelHandler
from utils.overpass_handler import OverpassHandler
from utils.string_utils import *
from pathlib import Path

file_path = Path(__file__).parent.parent / "data" / "station_gr_codes.json"
gr_workbook = GeoRoutesExcelHandler()
overpass = OverpassHandler()

# Stations whose code cannot be matched to a name in the GR codes source
EXCEPTIONAL_STATIONS = {'batumicentral': 'Batumi',
                        'borjomiparki': 'Borjomi',
                        'jumati': 'Djumati',
                        'kutaisiinternationalairport': 'Kutaisi International Airport',
                        'kutaisi1': 'Kutaisi I',
                        'platform11km': 'Platform 11 km',
                        'platform16km': 'Platform 16 km',
                        'rustavicentral': 'Rustavi -pass.',
                        'samtredia1': 'Samtredia',
                        'samtredia2': 'Samtredia II',
                        'tbilisicentralstation': 'Tbilisi-pass.',
                        'navtlughi': 'Tbilisi-cross.',
                        'tbilisimarshalling': 'Tbilisi-sort.',
                        'rustavicargo': 'Rustavi-fr.'}

_gr_codes_by_name = None


def get_station_gr_code(station_name):
    """Returns the Georgian Railway (GR) code by station code (English name, lowercased, without spaces).
    The GR codes file is loaded once into a lowercase name -> code dict."""
    global _gr_codes_by_name
    if _gr_codes_by_name is None:
        with open(file_path, "r", encoding='utf-8') as station_codes_file:
            _gr_codes_by_name = {}
            for station in json.load(station_codes_file):
                # Keep the first match on duplicate names, as the former linear search did
                _gr_codes_by_name.setdefault(station['Name'].lower(), station['Code'])
    station_name = EXCEPTIONAL_STATIONS.get(station_name, station_name)
    return _gr_codes_by_name.get(station_name.lower(), '00000')


def get_existing_station_descriptions():
    """Первоисточником описаний станций является stations.json. Поэтому при обновлении stations-list.js и stations.json
     сначала сохраняем существующие описания и добавляем их обратно в пересозданный файл"""
    with open(STATIONS_JSON_PATH, 'r', encoding='utf-8') as file:
        stations = json.load(file)
    if isinstance(stations, list):
        return {s['code']: s['description'] for s in stations if 'description' in s}
    return {code: data['description'] for code, data in stations.items() if 'description' in data}


ROLE_TO_BUCKET = {'start': 'departure', 'end': 'arrival'}


def add_route_to_stations_list(stations_list, station_code, route_data, role, arrival_time, departure_time, stop_time):
    """Adds the route to the station's departure/arrival/via list according to its role.
    Mutates stations_list in place."""
    route_data_updated = {**route_data,
                          'arrival_time': arrival_time,
                          'departure_time': departure_time,
                          'stop_time': stop_time}
    station_routes = stations_list.setdefault(station_code, {'departure': [], 'arrival': [], 'via': []})
    station_routes[ROLE_TO_BUCKET.get(role, 'via')].append(route_data_updated)


def get_routes_for_stations():
    """Составляет словарь всех станций и проходящих через них маршрутов"""
    with open(ROUTES_JSON_PATH, 'r', encoding="utf-8") as file:
        routes_data = json.load(file)
    stations_with_routes = {}
    for r in routes_data:
        if not r.get('active'):
            continue
        route_data = {
            'ref': r['ref'],
            'name_en': r['name:en'],
            'name_ru': r['name:ru'],
            'name_ka': r['name:ka'],
            'frequency': r['frequency'],
            'start_date': r['start_date'],
            'end_date': r['end_date'],
            }
        if r.get('stations'):
            for s in r['stations']:
                add_route_to_stations_list(stations_with_routes, s['code'], route_data, s['role'], s['arrival_time'], s['departure_time'], s['stop_time'])
    return stations_with_routes


def make_stations_json():
    all_route_osm_ids = gr_workbook.get_all_routes_osm_id(show_on_site_only=True)
    stops_data = overpass.get_route_stops_data(all_route_osm_ids)
    station_descriptions = get_existing_station_descriptions()
    stations_with_routes = get_routes_for_stations()
    stations_dict = {}
    for station in stops_data['elements']:
        if station['type'] != 'node':
            continue
        tags = station.get('tags', {})
        generic_name = tags.get('name', 'unknown station')
        name_en = tags.get('name:en', generic_name)
        name_ka = tags.get('name:ka', generic_name)
        name_ru = tags.get('name:ru', generic_name)
        code = make_station_code(name_en)
        if code in stations_dict:
            stations_dict[code]['id'].append(station['id'])
        else:
            station_type = 'secondary'
            if code == 'batumicentral':
                station_type = 'beach'
            elif code == 'kutaisiinternationalairport':
                station_type = 'airport'
            elif code == 'tbilisicentralstation':
                station_type = 'main'
            station_data = {"id": [station['id']],
                            "coords": [station['lat'], station['lon']],
                            "code": code,
                            "type": station_type,
                            "name_en": name_en,
                            "name_ka": name_ka,
                            "name_ru": name_ru,
                            "gr_code": get_station_gr_code(code)
                            }
            if code in station_descriptions:
                station_data['description'] = station_descriptions[code]
            if code in stations_with_routes:
                station_data['routes'] = stations_with_routes[code]
            stations_dict[code] = station_data
    result = json.dumps(dict(sorted(stations_dict.items(), key=lambda x: x[1]['name_en'])), ensure_ascii=False, indent=3)
    with open(STATIONS_LIST_JS_PATH, 'w', encoding='utf-8') as file:
        file.write("export const stations = " + result)
        print('station-list.js was rewrited')
    with open(STATIONS_JSON_PATH, 'w', encoding='utf-8') as file:
        file.write(result)
        print('stations.json was rewrited')


if __name__ == '__main__':
    # Retries are handled by OverpassHandler
    make_stations_json()

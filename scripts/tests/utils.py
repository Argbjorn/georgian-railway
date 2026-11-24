import os

# Paths relative to project root (parent of scripts/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROUTES_FILE = os.path.join(_PROJECT_ROOT, 'data', 'routes.json')
STATIONS_FILE = os.path.join(_PROJECT_ROOT, 'data', 'stations.json')
STATION_META_FILE = os.path.join(_PROJECT_ROOT, 'data', 'station_meta.json')

REQUIRED_FILES = [
    ROUTES_FILE,
    STATIONS_FILE,
]

def time_string_to_minutes(time_string):
    """Преобразует строку времени в формате HH:MM в минуты"""
    try:
        hours, minutes = map(int, time_string.split(":"))
        return hours * 60 + minutes
    except ValueError:
        raise ValueError(f"Неверный формат времени: {time_string}, ожидается HH:MM")
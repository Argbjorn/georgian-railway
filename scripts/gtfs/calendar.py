"""calendar.txt — weekly patterns and date ranges of all services.

Services without a weekly pattern (every second day, odd/even days) get a row with all weekdays
set to 0: their dates come from calendar_dates.txt, the row only states the date range. Some
consumers (e.g. gtfs-to-html) take a service's date range from calendar.txt only.
"""

FILE_NAME = 'calendar.txt'
FIELDS = [
    'service_id',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
    'start_date',
    'end_date',
]
REQUIRED_FIELDS = set(FIELDS)

_WEEKDAYS = FIELDS[1:8]
_KIND_DAYS = {
    'daily': set(_WEEKDAYS),
    'workdays': set(_WEEKDAYS[:5]),
}


def build_calendar(services):
    return [{
        'service_id': service.service_id,
        **{day: 1 if day in _KIND_DAYS.get(service.kind, ()) else 0 for day in _WEEKDAYS},
        'start_date': service.start.strftime('%Y%m%d'),
        'end_date': service.end.strftime('%Y%m%d'),
    } for service in services]

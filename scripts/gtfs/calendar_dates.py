"""calendar_dates.txt — explicit operating dates of services without a weekly pattern
(every second day, odd/even days of the month)."""

from .services import WEEKLY_KINDS, service_dates

FILE_NAME = 'calendar_dates.txt'
FIELDS = ['service_id', 'date', 'exception_type']
REQUIRED_FIELDS = set(FIELDS)

SERVICE_ADDED = 1


def build_calendar_dates(services):
    return [{
        'service_id': service.service_id,
        'date': day.strftime('%Y%m%d'),
        'exception_type': SERVICE_ADDED,
    } for service in services if service.kind not in WEEKLY_KINDS for day in service_dates(service)]

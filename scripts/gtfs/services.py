"""Services (operating days) shared by trips.txt, calendar.txt and calendar_dates.txt."""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from .config import FEED_HORIZON_MONTHS, FEED_UTC_OFFSET_HOURS

# routes.json `frequency` → service kind used in service_id.
FREQUENCY_KINDS = {
    'daily': 'daily',
    'on workdays': 'workdays',
    'every second day': 'esd',
    'on odd days': 'odd',
    'on even days': 'even',
}
# Kinds expressed as a weekly pattern in calendar.txt; the rest are listed date by date in
# calendar_dates.txt.
WEEKLY_KINDS = {'daily', 'workdays'}

# Kinds whose dates are counted from start_date and therefore require it.
_START_DATE_REQUIRED = {'esd'}


@dataclass(frozen=True)
class Window:
    """Dates covered by the feed, inclusive."""
    start: date
    end: date


@dataclass(frozen=True)
class Service:
    service_id: str
    kind: str
    # Train dates clipped to the feed window, inclusive; start > end means no service.
    start: date
    end: date
    # Train start_date: day 0 of the "every second day" pattern.
    anchor: date | None


def ms_to_date(ms):
    """routes.json dates are Unix ms at UTC midnight; convert via UTC, not local time."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date() if ms is not None else None


def add_months(day, months):
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def feed_window(today=None):
    if today is None:
        today = datetime.now(timezone(timedelta(hours=FEED_UTC_OFFSET_HOURS))).date()
    return Window(today, add_months(today, FEED_HORIZON_MONTHS))


def service_kind(train):
    try:
        kind = FREQUENCY_KINDS[train['frequency']]
    except KeyError:
        raise ValueError(f'Train {train["ref"]}: unsupported frequency {train["frequency"]!r}')
    if kind in _START_DATE_REQUIRED and train.get('start_date') is None:
        raise ValueError(f'Train {train["ref"]}: frequency {train["frequency"]!r} requires start_date')
    return kind


def service_id(train):
    """Same id for trains with the same frequency and date range, e.g. `daily`, `esd_20250602_open`."""
    kind = service_kind(train)
    start, end = ms_to_date(train.get('start_date')), ms_to_date(train.get('end_date'))
    if start is None and end is None:
        return kind
    return '_'.join([kind] + [d.strftime('%Y%m%d') if d else 'open' for d in (start, end)])


def train_service(train, window):
    start, end = ms_to_date(train.get('start_date')), ms_to_date(train.get('end_date'))
    return Service(
        service_id=service_id(train),
        kind=service_kind(train),
        start=max(start, window.start) if start else window.start,
        end=min(end, window.end) if end else window.end,
        anchor=start,
    )


def _runs_on(service, day):
    if service.kind == 'daily':
        return True
    if service.kind == 'workdays':
        return day.weekday() < 5
    if service.kind == 'esd':
        return (day - service.anchor).days % 2 == 0
    if service.kind == 'odd':
        return day.day % 2 == 1
    if service.kind == 'even':
        return day.day % 2 == 0
    raise ValueError(f'Unknown service kind {service.kind!r}')


def service_dates(service):
    """All operating dates of the service within its (window-clipped) range."""
    days = (service.end - service.start).days + 1
    return [day for day in (service.start + timedelta(n) for n in range(max(days, 0)))
            if _runs_on(service, day)]


def unique_services(trains, window):
    """Services of `trains`, one per service_id, ordered by service_id."""
    services = {}
    for train in trains:
        service = train_service(train, window)
        services.setdefault(service.service_id, service)
    return [services[key] for key in sorted(services)]


def split_by_service(trains, window):
    """(trains running at least once within the window, refs of the others)."""
    running, idle = [], []
    for train in trains:
        if service_dates(train_service(train, window)):
            running.append(train)
        else:
            idle.append(train['ref'])
    return running, idle

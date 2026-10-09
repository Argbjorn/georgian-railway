"""Service (operating days) definitions shared by trips.txt, calendar.txt and calendar_dates.txt."""

from datetime import datetime, timezone

# routes.json `frequency` → service kind used in service_id.
FREQUENCY_KINDS = {
    'daily': 'daily',
    'on workdays': 'workdays',
    'every second day': 'esd',
    'on odd days': 'odd',
    'on even days': 'even',
}

# Kinds whose dates are counted from start_date and therefore require it.
_START_DATE_REQUIRED = {'esd'}


def ms_to_date(ms):
    """routes.json dates are Unix ms at UTC midnight; convert via UTC, not local time."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date() if ms is not None else None


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

"""stop_times.txt — arrival and departure of every train at every station."""

import re

from .ids import stop_id

FILE_NAME = 'stop_times.txt'
FIELDS = [
    'trip_id',
    'arrival_time',
    'departure_time',
    'stop_id',
    'location_group_id',
    'location_id',
    'stop_sequence',
    'stop_headsign',
    'start_pickup_drop_off_window',
    'end_pickup_drop_off_window',
    'pickup_type',
    'drop_off_type',
    'continuous_pickup',
    'continuous_drop_off',
    'shape_dist_traveled',
    'timepoint',
    'pickup_booking_rule_id',
    'drop_off_booking_rule_id',
]
REQUIRED_FIELDS = {'trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'}

NO_PICKUP = 1
NO_DROP_OFF = 1
# The train stops here, but its time is unknown: consumers estimate it from the neighbouring stops
APPROXIMATE_TIME = 0
EXACT_TIME = 1

_TIME = re.compile(r'(\d{1,2}):(\d{2})')
MINUTES_PER_DAY = 24 * 60
# A backward step in time is taken as crossing midnight. A resulting gap longer than this between
# two consecutive times is implausible and means a data error (e.g. 10:05 listed after 10:10).
MAX_GAP_MINUTES = 12 * 60


def parse_time(value):
    """'HH:MM' → minutes since midnight; '-', 'nn:nn', '' or None → None."""
    match = _TIME.fullmatch(value) if isinstance(value, str) else None
    return int(match[1]) * 60 + int(match[2]) if match else None


def format_time(minutes):
    """Minutes since the start of the trip's service day → 'HH:MM:SS' (hours may exceed 23)."""
    return f'{minutes // 60:02d}:{minutes % 60:02d}:00'


def station_times(train, index):
    """(arrival, departure) in minutes since midnight for the station at `index`.

    Without separate arrival times (has_arrival_time=false) the only known time is used for both.
    If one of the two is missing (e.g. arrival at the first station), it mirrors the other: GTFS
    does not allow a stop time with only one of them.
    """
    station = train['stations'][index]
    departure = parse_time(station.get('departure_time'))
    arrival = parse_time(station.get('arrival_time')) if train.get('has_arrival_time') else departure
    return (arrival if arrival is not None else departure,
            departure if departure is not None else arrival)


def has_terminal_times(train):
    """GTFS requires times at the first and the last stop of a trip."""
    return all(station_times(train, index)[0] is not None for index in (0, len(train['stations']) - 1))


def split_by_terminal_times(routes):
    """(trains with times at both terminal stations, refs of the other trains)."""
    kept = [train for train in routes if has_terminal_times(train)]
    skipped = [train['ref'] for train in routes if not has_terminal_times(train)]
    return kept, skipped


def unwrap_midnight(train, times):
    """Turns per-station (arrival, departure) minutes into minutes since the departure day's
    midnight, adding a day each time the schedule steps back in time. Missing times stay None."""
    result = []
    offset = 0
    previous = None
    for station_index, pair in enumerate(times):
        unwrapped = []
        for value in pair:
            if value is None:
                unwrapped.append(None)
                continue
            value += offset
            if previous is not None and value < previous:
                offset += MINUTES_PER_DAY
                value += MINUTES_PER_DAY
                if value - previous > MAX_GAP_MINUTES:
                    code = train['stations'][station_index]['code']
                    raise ValueError(f'Train {train["ref"]}: time goes backwards at station {code}')
            unwrapped.append(value)
            previous = value
        result.append(tuple(unwrapped))
    return result


def build_trip_stop_times(train, distances=None):
    """`distances`: shape_dist_traveled per station (None where unknown), or None without a shape."""
    stations = train['stations']
    times = unwrap_midnight(train, [station_times(train, i) for i in range(len(stations))])
    for index in (0, len(stations) - 1):
        if times[index][0] is None:
            raise ValueError(f'Train {train["ref"]}: no time at terminal station {stations[index]["code"]}')

    rows = []
    for index, (station, (arrival, departure)) in enumerate(zip(stations, times)):
        has_time = arrival is not None  # arrival and departure are either both set or both missing
        rows.append({
            'trip_id': str(train['ref']),
            'arrival_time': format_time(arrival) if has_time else '',
            'departure_time': format_time(departure) if has_time else '',
            'stop_id': stop_id(station['code']),
            'stop_sequence': index + 1,
            'pickup_type': NO_PICKUP if index == len(stations) - 1 else '',
            'drop_off_type': NO_DROP_OFF if index == 0 else '',
            'shape_dist_traveled': distances[index] if distances and distances[index] is not None else '',
            'timepoint': EXACT_TIME if has_time else APPROXIMATE_TIME,
        })
    return rows


def build_stop_times(lines, stop_distances=None):
    """`stop_distances` maps train ref to shape_dist_traveled per station."""
    stop_distances = stop_distances or {}
    return [row for line in lines for train in line.trains
            for row in build_trip_stop_times(train, stop_distances.get(train['ref']))]

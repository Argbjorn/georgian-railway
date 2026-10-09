"""agency.txt — railway companies operating the trains in the feed."""

from .config import AGENCIES

FILE_NAME = 'agency.txt'
FIELDS = [
    'agency_id',
    'agency_name',
    'agency_url',
    'agency_timezone',
    'agency_lang',
    'agency_phone',
    'agency_fare_url',
    'agency_email',
    'cemv_support',
]
# agency_id is conditionally required (multiple agencies) — always written.
REQUIRED_FIELDS = {'agency_id', 'agency_name', 'agency_url', 'agency_timezone'}


def build_agency(routes):
    """Returns agency rows for the operators referenced by `routes`, in AGENCIES order."""
    without_operator = [route['ref'] for route in routes if not route.get('operator')]
    if without_operator:
        raise ValueError(f'Routes without operator: {without_operator}')
    used = {route['operator'] for route in routes}
    unknown = used - AGENCIES.keys()
    if unknown:
        raise ValueError(f'Unknown operator(s) in routes: {sorted(unknown)}')

    return [{'agency_id': agency_id, **AGENCIES[agency_id]}
            for agency_id in AGENCIES if agency_id in used]

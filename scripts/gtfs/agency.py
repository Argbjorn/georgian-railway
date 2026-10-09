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
    """Returns agency rows for the operators referenced by `routes`, in AGENCIES order.

    Until make_routes_files exports the `operator` field, no route references an agency
    and all known agencies are written.
    """
    used = {route['operator'] for route in routes if route.get('operator')}
    unknown = used - AGENCIES.keys()
    if unknown:
        raise ValueError(f'Unknown operator(s) in routes: {sorted(unknown)}')
    if not used:
        used = set(AGENCIES)

    return [{'agency_id': agency_id, **AGENCIES[agency_id]}
            for agency_id in AGENCIES if agency_id in used]

"""attributions.txt — data sources and roles: OSM (required by ODbL), the operators, the site."""

from .config import FEED_CONTACT_EMAIL, FEED_PUBLISHER_NAME, SITE_URL

FILE_NAME = 'attributions.txt'
FIELDS = [
    'attribution_id',
    'agency_id',
    'route_id',
    'trip_id',
    'organization_name',
    'is_producer',
    'is_operator',
    'is_authority',
    'attribution_url',
    'attribution_email',
    'attribution_phone',
]
REQUIRED_FIELDS = {'organization_name'}

OSM_ATTRIBUTION = {
    'attribution_id': 'osm',
    'organization_name': 'OpenStreetMap contributors',
    'is_producer': 1,
    'attribution_url': 'https://www.openstreetmap.org/copyright',
}


def build_attributions(agency_rows):
    """Feed-wide rows for the site and OSM; one row per operator, scoped to its agency."""
    site = {
        'attribution_id': 'site',
        'organization_name': FEED_PUBLISHER_NAME,
        'is_producer': 1,
        'attribution_url': SITE_URL,
        'attribution_email': FEED_CONTACT_EMAIL,
    }
    operators = [{
        'attribution_id': agency['agency_id'].lower(),
        'agency_id': agency['agency_id'],
        'organization_name': agency['agency_name'],
        'is_operator': 1,
        'attribution_url': agency['agency_url'],
    } for agency in agency_rows]
    return [site, OSM_ATTRIBUTION, *operators]

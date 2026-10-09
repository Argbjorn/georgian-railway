"""feed_info.txt — publisher, language, validity period and version of the feed."""

import hashlib
import os

from .config import FEED_CONTACT_EMAIL, FEED_CONTACT_URL, FEED_LANG, FEED_PUBLISHER_NAME, SITE_URL

FILE_NAME = 'feed_info.txt'
FIELDS = [
    'feed_publisher_name',
    'feed_publisher_url',
    'feed_lang',
    'default_lang',
    'feed_start_date',
    'feed_end_date',
    'feed_version',
    'feed_contact_email',
    'feed_contact_url',
]
REQUIRED_FIELDS = {'feed_publisher_name', 'feed_publisher_url', 'feed_lang'}


def feed_version(window, paths):
    """`<build date>-<first 8 hex chars of sha256 over the given feed files>`."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=os.path.basename):
        digest.update(os.path.basename(path).encode())
        with open(path, 'rb') as f:
            digest.update(f.read())
    return f'{window.start:%Y%m%d}-{digest.hexdigest()[:8]}'


def build_feed_info(window, version):
    return [{
        'feed_publisher_name': FEED_PUBLISHER_NAME,
        'feed_publisher_url': SITE_URL,
        'feed_lang': FEED_LANG,
        'default_lang': FEED_LANG,
        'feed_start_date': f'{window.start:%Y%m%d}',
        'feed_end_date': f'{window.end:%Y%m%d}',
        'feed_version': version,
        'feed_contact_email': FEED_CONTACT_EMAIL,
        'feed_contact_url': FEED_CONTACT_URL,
    }]

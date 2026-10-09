"""Stable GTFS identifiers derived from site data."""

# Non-ASCII letters found in station codes (Azerbaijani names). The table is explicit rather than
# a generic Unicode fold so that stop_ids never change silently; a new letter fails the build.
_TRANSLITERATION = str.maketrans({
    'ə': 'e',
    'ı': 'i',
    'ğ': 'g',
    'ö': 'o',
    'ü': 'u',
    'ç': 'c',
    'ş': 's',
})


def stop_id(station_code):
    result = station_code.translate(_TRANSLITERATION)
    if not result.isascii():
        raise ValueError(f'Station code {station_code!r} has letters missing from the '
                         f'transliteration table in gtfs/ids.py')
    return result

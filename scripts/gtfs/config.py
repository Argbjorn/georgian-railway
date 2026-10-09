# GTFS requires every agency in a feed to have the same agency_timezone. Georgia, Azerbaijan and
# Armenia are all UTC+4 without DST, so Asia/Tbilisi is used for every agency; the real time zones
# of foreign stations are expressed via stops.stop_timezone.
FEED_TIMEZONE = 'Asia/Tbilisi'

SITE_URL = 'https://georailway.com'
# Site URL prefix per language; English pages live at the site root.
LANG_URL_PREFIX = {'en': '', 'ka': '/ka', 'ru': '/ru'}

# City priority for naming lines: a line is named from the terminal city that comes first in this
# list ("Tbilisi — Borjomi", not "Borjomi — Tbilisi"); the same city defines direction_id=0.
# Matched against the city names in the trains' `name:en` ("Borjomi → Tbilisi").
LINE_NAME_CITY_PRIORITY = ['Yerevan', 'Baku', 'Tbilisi', 'Batumi', 'Kutaisi']

# stops.stop_timezone for stations outside Georgia, keyed by station code. Georgian stations are
# omitted and inherit agency_timezone. Does not affect stop_times (always in agency_timezone).
STOP_TIMEZONES = {
    # Azerbaijan
    'böyükkəsik': 'Asia/Baku',
    'ağstafastansiyası': 'Asia/Baku',
    'ganja': 'Asia/Baku',
    'yevlaxstansiyası': 'Asia/Baku',
    'biləcəri': 'Asia/Baku',
    'bakı': 'Asia/Baku',
    # Armenia
    'ayrum': 'Asia/Yerevan',
    'vanadzor': 'Asia/Yerevan',
    'gyumri': 'Asia/Yerevan',
    'armavir': 'Asia/Yerevan',
    'yerevan': 'Asia/Yerevan',
}

# Keyed by agency_id, which matches the `operator` column of the routes sheet.
AGENCIES = {
    'GR': {
        'agency_name': 'Georgian Railway',
        'agency_url': 'https://www.railway.ge/',
        'agency_timezone': FEED_TIMEZONE,
        'agency_lang': 'ka',
        'agency_phone': '1331',
        'agency_fare_url': 'https://gr.com.ge/',
        'agency_email': 'callcenter@railway.ge',
    },
    'AR': {
        'agency_name': 'Azerbaijan Railways',
        'agency_url': 'https://ady.az/',
        'agency_timezone': FEED_TIMEZONE,
        'agency_lang': 'az',
        'agency_phone': '1822',
        'agency_fare_url': 'https://ticket.ady.az/',
        'agency_email': 'elaqe@ady.az',
    },
    'SCR': {
        'agency_name': 'South Caucasus Railway',
        'agency_url': 'https://www.railway.am/',
        'agency_timezone': FEED_TIMEZONE,
        'agency_lang': 'hy',
        'agency_phone': '+37460463440',
        'agency_fare_url': 'https://ticket.railway.am/',
        'agency_email': 'mail@railway.am',
    },
}

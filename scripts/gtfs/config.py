# GTFS requires every agency in a feed to have the same agency_timezone. Georgia, Azerbaijan and
# Armenia are all UTC+4 without DST, so Asia/Tbilisi is used for every agency; the real time zones
# of foreign stations are expressed via stops.stop_timezone.
FEED_TIMEZONE = 'Asia/Tbilisi'

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

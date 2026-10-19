import re
import time

import requests


class OverpassHandler:
    ATTEMPTS_PER_INSTANCE = 5
    RETRY_DELAY_SECONDS = 1
    # Default declared [timeout] of the generated queries, in seconds
    SERVER_TIMEOUT = 25
    # The client waits longer than the query's declared timeout: time spent queued for a slot is not counted
    # by the server
    CLIENT_TIMEOUT_MARGIN = 30
    # Declared [maxsize] in bytes: full route geometry is ~3 MB of output, stop lists are a few KB
    MAXSIZE_ROUTES_GEOM = 64 * 1024 * 1024
    MAXSIZE_SMALL = 16 * 1024 * 1024

    def __init__(self):
        self.base_url = 'https://overpass-api.de/api/interpreter'
        self.base_url_reserve = 'https://maps.mail.ru/osm/tools/overpass/api/interpreter'

    def get_data(self, query):
        # Alternate between the main and the reserve instance, so neither is hit again right after a failure
        urls = [self.base_url, self.base_url_reserve] * self.ATTEMPTS_PER_INSTANCE
        last_error = None
        for attempt, url in enumerate(urls, start=1):
            try:
                return self._request(url, query)
            except Exception as error:
                last_error = error
                print(f"Overpass attempt {attempt}/{len(urls)} failed ({url}): {error}")
                if attempt < len(urls):
                    time.sleep(self.RETRY_DELAY_SECONDS)
        raise last_error

    def _request(self, url, query):
        headers = {
            "User-Agent": "georailway",
        }
        timeout = self._client_timeout(query)
        result = requests.post(url, data={"data": query}, headers=headers, timeout=timeout)
        if result.status_code != 200:
            raise Exception(f"Failed to get data from Overpass API: {result.status_code} {result.text[:300]}")
        return result.json()

    def _client_timeout(self, query):
        # Hand-written queries (e.g. make_railway_network_file) may declare their own [timeout:N];
        # Overpass falls back to 180 s when none is declared
        match = re.search(r"\[timeout:(\d+)\]", query)
        server_timeout = int(match.group(1)) if match else 180
        return server_timeout + self.CLIENT_TIMEOUT_MARGIN

    def get_routes_data(self, routes_id):
        if not routes_id:
            return {'elements': []}
        query = self._create_routes_query(routes_id)
        return self.get_data(query)

    def get_route_stops_data(self, routes_id):
        """Route relations without geometry (members only) plus their stop nodes with tags and coordinates.
        Much lighter than get_routes_data when only the stop list is needed."""
        if not routes_id:
            return {'elements': []}
        query = self._create_route_stops_query(routes_id)
        return self.get_data(query)

    # The Overpass dispatcher admits a query based on its declared timeout and maxsize (default 512 MiB),
    # so declaring a realistic maxsize makes the query much more likely to get a slot on a loaded server
    def _header(self, maxsize):
        return f"[out:json][timeout:{self.SERVER_TIMEOUT}][maxsize:{maxsize}];"

    @staticmethod
    def _ids(ids):
        return ",".join(str(i) for i in ids)

    def _create_routes_query(self, routes_id):
        return self._header(self.MAXSIZE_ROUTES_GEOM) + f"relation(id:{self._ids(routes_id)});out geom;"

    def _create_route_stops_query(self, routes_id):
        return (self._header(self.MAXSIZE_SMALL)
                + f"relation(id:{self._ids(routes_id)})->.routes;"
                + ".routes out body;"
                + 'node(r.routes:"stop");out;')
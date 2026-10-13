from gtfs import agency, attributions

ALL_AGENCIES = agency.build_agency([{'operator': 'GR'}, {'operator': 'AR'}, {'operator': 'SCR'}])


class TestBuildAttributions:
    def test_site_and_osm_are_feed_wide_producers(self):
        rows = {row['attribution_id']: row for row in attributions.build_attributions(ALL_AGENCIES)}
        assert rows['site']['organization_name'] == 'Georgian Railway Map'
        assert rows['osm'] == {
            'attribution_id': 'osm',
            'organization_name': 'OpenStreetMap contributors',
            'is_producer': 1,
            'attribution_url': 'https://www.openstreetmap.org/copyright',
        }
        for key in ('site', 'osm'):
            assert not {'agency_id', 'route_id', 'trip_id'} & set(rows[key])

    def test_operator_per_agency(self):
        rows = attributions.build_attributions(agency.build_agency([{'operator': 'AR'}]))
        operators = [row for row in rows if row.get('is_operator')]
        assert operators == [{
            'attribution_id': 'ar',
            'agency_id': 'AR',
            'organization_name': 'Azerbaijan Railways',
            'is_operator': 1,
            'attribution_url': 'https://ady.az/',
        }]

    def test_every_row_has_a_role_and_unique_id(self):
        rows = attributions.build_attributions(ALL_AGENCIES)
        assert all(row.get('is_producer') or row.get('is_operator') for row in rows)
        ids = [row['attribution_id'] for row in rows]
        assert len(ids) == len(set(ids))
        assert all(set(row) <= set(attributions.FIELDS) for row in rows)

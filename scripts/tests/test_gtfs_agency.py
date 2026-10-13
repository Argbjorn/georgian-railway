import csv

import pytest

from gtfs import agency
from gtfs.config import AGENCIES, FEED_LANG
from gtfs.writer import write_table


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


ALL_OPERATORS = [{'operator': agency_id} for agency_id in AGENCIES]


class TestBuildAgency:
    def test_route_without_operator_fails(self):
        with pytest.raises(ValueError, match='without operator'):
            agency.build_agency([{'ref': 1, 'operator': 'GR'}, {'ref': 2, 'operator': None}])

    def test_agencies_in_config_order(self):
        rows = agency.build_agency(list(reversed(ALL_OPERATORS)))
        assert [row['agency_id'] for row in rows] == ['GR', 'AR', 'SCR']

    def test_only_referenced_agencies(self):
        rows = agency.build_agency([{'operator': 'SCR'}, {'operator': 'GR'}, {'operator': 'GR'}])
        assert [row['agency_id'] for row in rows] == ['GR', 'SCR']

    def test_unknown_operator_fails(self):
        with pytest.raises(ValueError, match='XX'):
            agency.build_agency([{'operator': 'XX'}])

    def test_agencies_share_timezone(self):
        # GTFS requires one agency_timezone for all agencies of a feed
        assert len({a['agency_timezone'] for a in AGENCIES.values()}) == 1

    def test_agency_lang_matches_feed_lang(self):
        assert {a['agency_lang'] for a in AGENCIES.values()} == {FEED_LANG}

    def test_rows_have_required_fields_and_only_known_fields(self):
        for row in agency.build_agency(ALL_OPERATORS):
            assert all(row.get(field) for field in agency.REQUIRED_FIELDS)
            assert set(row) <= set(agency.FIELDS)


class TestWriteTable:
    def test_omits_empty_optional_columns(self, tmp_path):
        path = tmp_path / 'agency.txt'
        write_table(path, agency.FIELDS, agency.build_agency(ALL_OPERATORS), agency.REQUIRED_FIELDS)

        with open(path, encoding='utf-8') as f:
            header = f.readline().strip().split(',')
        assert header == agency.FIELDS[:-1]  # cemv_support is empty everywhere

    def test_keeps_required_columns_even_if_empty(self, tmp_path):
        path = tmp_path / 't.txt'
        write_table(path, ['a', 'b'], [{'a': 1, 'b': ''}], required_fields={'b'})
        assert read_csv(path) == [{'a': '1', 'b': ''}]

    def test_rejects_unknown_fields(self, tmp_path):
        with pytest.raises(ValueError, match='c'):
            write_table(tmp_path / 't.txt', ['a'], [{'a': 1, 'c': 2}])

    def test_utf8_lf_and_quoting(self, tmp_path):
        path = tmp_path / 't.txt'
        write_table(path, ['a'], [{'a': 'საქართველო, "quoted"'}])
        raw = path.read_bytes()
        assert b'\r\n' not in raw
        assert read_csv(path) == [{'a': 'საქართველო, "quoted"'}]

    def test_agency_roundtrip(self, tmp_path):
        path = tmp_path / 'agency.txt'
        write_table(path, agency.FIELDS, agency.build_agency(ALL_OPERATORS), agency.REQUIRED_FIELDS)
        rows = read_csv(path)
        assert rows[0]['agency_id'] == 'GR'
        assert rows[0]['agency_phone'] == '1331'
        assert rows[2]['agency_phone'] == '+37460463440'

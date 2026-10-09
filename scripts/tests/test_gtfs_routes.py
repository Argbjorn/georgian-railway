import pytest

from gtfs import routes
from gtfs.source import load_direction_pages, load_json, select_routes
from utils import ROUTES_FILE
from config import DIRECTIONS_CONTENT_DIR


def train(ref, start, end, train_type=None, operator='GR', name=None):
    return {
        'ref': ref,
        'train_type': train_type,
        'operator': operator,
        'name:en': name or f'{start.title()} → {end.title()}',
        'stations': [{'code': start}, {'code': end}],
    }


class TestGroupLines:
    def test_pair_and_analogues_form_one_line(self):
        trains = [train(804, 'tbilisi', 'batumi', 'stadler'), train(801, 'batumi', 'tbilisi', 'stadler'),
                  train(802, 'tbilisi', 'batumi', 'stadler'), train(803, 'batumi', 'tbilisi', 'stadler')]
        [line] = routes.group_lines(trains)
        assert line.route_id == 'tbilisi-batumi-stadler'
        assert [t['ref'] for t in line.trains] == [801, 802, 803, 804]

    def test_direction_id_follows_representative(self):
        [line] = routes.group_lines([train(2, 'gori', 'khashuri'), train(1, 'khashuri', 'gori')])
        directions = {t['ref']: line.direction_id(t) for t in line.trains}
        assert directions == {1: 0, 2: 1}

    def test_different_train_types_are_different_lines(self):
        lines = routes.group_lines([train(1, 'a', 'b', 'stadler'), train(2, 'a', 'b', 'suburban')])
        assert [line.route_id for line in lines] == ['a-b-stadler', 'a-b-suburban']

    def test_route_id_without_train_type_and_ascii(self):
        [line] = routes.group_lines([train(37, 'tbilisicentralstation', 'bakı', name='Tbilisi → Baku')])
        assert line.route_id == 'baki-tbilisicentralstation'

    def test_lines_ordered_by_lowest_ref(self):
        lines = routes.group_lines([train(6413, 'x', 'y'), train(37, 'a', 'b'), train(6414, 'y', 'x')])
        assert [line.representative['ref'] for line in lines] == [37, 6413]

    def test_different_operators_in_line_fail(self):
        with pytest.raises(ValueError, match='several operators'):
            routes.group_lines([train(1, 'a', 'b', operator='GR'), train(2, 'b', 'a', operator='SCR')])


class TestLineNaming:
    def test_priority_city_goes_first(self):
        [line] = routes.group_lines([train(617, 'borjomi', 'tbilisi'), train(618, 'tbilisi', 'borjomi')])
        assert routes.line_name(line) == 'Tbilisi — Borjomi'
        assert line.route_id == 'tbilisi-borjomi'
        assert line.representative['ref'] == 618
        assert line.direction_id(line.representative) == 0

    def test_higher_priority_city_wins(self):
        [line] = routes.group_lines([train(371, 'tbilisi', 'yerevan'), train(372, 'yerevan', 'tbilisi')])
        assert routes.line_name(line) == 'Yerevan — Tbilisi'
        assert line.representative['ref'] == 372

    def test_priority_city_only_as_destination(self):
        # No train departs from Tbilisi: the name still starts with it, direction 0 stays the
        # lowest-ref train
        [line] = routes.group_lines([train(1, 'borjomi', 'tbilisi')])
        assert routes.line_name(line) == 'Tbilisi — Borjomi'
        assert line.route_id == 'tbilisi-borjomi'
        assert line.representative['ref'] == 1

    def test_no_priority_city_uses_lowest_ref(self):
        [line] = routes.group_lines([train(6418, 'khashuri', 'zestafoni'), train(6417, 'zestafoni', 'khashuri')])
        assert routes.line_name(line) == 'Zestafoni — Khashuri'
        assert line.route_id == 'zestafoni-khashuri'
        assert line.representative['ref'] == 6417

    def test_translations_follow_english_order(self):
        t = train(617, 'borjomi', 'tbilisi')
        t['name:ru'] = 'Боржоми → Тбилиси'
        [line] = routes.group_lines([t])
        assert routes.line_name(line, 'ru') == 'Тбилиси — Боржоми'

    def test_name_without_arrow_fails(self):
        with pytest.raises(ValueError, match='A → B'):
            routes.group_lines([train(1, 'a', 'b', name='Somewhere')])


class TestBuildRoutes:
    def test_row(self):
        lines = routes.group_lines([train(38, 'baku', 'tbilisi', operator='AR'),
                                    train(37, 'tbilisi', 'baku', operator='AR')])
        assert routes.build_routes(lines, {}) == [{
            'route_id': 'baku-tbilisi',
            'agency_id': 'AR',
            'route_long_name': 'Baku — Tbilisi',
            'route_type': 2,
            'route_url': 'https://georailway.com/routes/38/',
            'route_sort_order': 37,
        }]

    def test_url_prefers_direction_page(self):
        [line] = routes.group_lines([train(801, 'batumicentral', 'tbilisicentralstation', 'stadler', name='Batumi → Tbilisi'),
                                     train(802, 'tbilisicentralstation', 'batumicentral', 'stadler', name='Tbilisi → Batumi')])
        pages = {('tbilisicentralstation', 'batumicentral'): 'tbilisi-batumi'}
        assert routes.line_url(line, pages) == 'https://georailway.com/directions/tbilisi-batumi/'
        assert routes.line_url(line, pages, 'ru') == 'https://georailway.com/ru/directions/tbilisi-batumi/'


class TestRealData:
    """Checks the generator against the current data files and site content."""

    def test_direction_pages_found(self):
        pages = load_direction_pages(DIRECTIONS_CONTENT_DIR)
        assert pages[('batumicentral', 'tbilisicentralstation')] == 'batumi-tbilisi'
        assert pages[('tbilisicentralstation', 'batumicentral')] == 'tbilisi-batumi'

    def test_builds_from_current_data(self):
        lines = routes.group_lines(select_routes(load_json(ROUTES_FILE)))
        rows = routes.build_routes(lines, load_direction_pages(DIRECTIONS_CONTENT_DIR))
        ids = [row['route_id'] for row in rows]
        assert len(ids) == len(set(ids))
        assert all(route_id.isascii() for route_id in ids)

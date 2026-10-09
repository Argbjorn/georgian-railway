from datetime import date

from gtfs import feed_info
from gtfs.services import Window

WINDOW = Window(date(2026, 10, 9), date(2027, 4, 9))


def write(path, text):
    path.write_text(text, encoding='utf-8')
    return str(path)


class TestFeedVersion:
    def test_format(self, tmp_path):
        version = feed_info.feed_version(WINDOW, [write(tmp_path / 'a.txt', 'x')])
        date_part, hash_part = version.split('-')
        assert date_part == '20261009'
        assert len(hash_part) == 8

    def test_same_content_same_version_regardless_of_order(self, tmp_path):
        a, b = write(tmp_path / 'a.txt', 'x'), write(tmp_path / 'b.txt', 'y')
        assert feed_info.feed_version(WINDOW, [a, b]) == feed_info.feed_version(WINDOW, [b, a])

    def test_content_change_changes_version(self, tmp_path):
        path = tmp_path / 'a.txt'
        before = feed_info.feed_version(WINDOW, [write(path, 'x')])
        after = feed_info.feed_version(WINDOW, [write(path, 'y')])
        assert before != after


class TestBuildFeedInfo:
    def test_row(self):
        assert feed_info.build_feed_info(WINDOW, '20261009-abcdef12') == [{
            'feed_publisher_name': 'Georgian Railway Map',
            'feed_publisher_url': 'https://georailway.com',
            'feed_lang': 'en',
            'default_lang': 'en',
            'feed_start_date': '20261009',
            'feed_end_date': '20270409',
            'feed_version': '20261009-abcdef12',
            'feed_contact_email': 'geo.railways.help@gmail.com',
            'feed_contact_url': 'https://georailway.com/about/',
        }]

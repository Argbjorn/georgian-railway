import calendar as std_calendar
from datetime import date

import pytest

from gtfs import calendar, calendar_dates, services
from gtfs.services import Window, add_months, feed_window, service_dates, split_by_service, train_service
from gtfs.source import load_json, select_routes
from utils import ROUTES_FILE


def ms(d):
    return std_calendar.timegm(d.timetuple()) * 1000


def train(ref=1, frequency='daily', start=None, end=None):
    return {
        'ref': ref,
        'frequency': frequency,
        'start_date': ms(start) if start else None,
        'end_date': ms(end) if end else None,
    }


WINDOW = Window(date(2026, 10, 9), date(2027, 4, 9))


class TestWindow:
    def test_six_months(self):
        assert feed_window(date(2026, 10, 9)) == WINDOW

    def test_add_months_clamps_day(self):
        assert add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)
        assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)


class TestServiceRange:
    def test_open_dates_take_window(self):
        service = train_service(train(), WINDOW)
        assert (service.start, service.end) == (WINDOW.start, WINDOW.end)

    def test_train_dates_clipped_to_window(self):
        service = train_service(train(start=date(2025, 1, 1), end=date(2030, 1, 1)), WINDOW)
        assert (service.start, service.end) == (WINDOW.start, WINDOW.end)

    def test_train_dates_inside_window(self):
        service = train_service(train(start=date(2026, 11, 1), end=date(2026, 11, 30)), WINDOW)
        assert (service.start, service.end) == (date(2026, 11, 1), date(2026, 11, 30))

    def test_end_date_inclusive(self):
        service = train_service(train(end=date(2026, 10, 11)), WINDOW)
        assert service_dates(service) == [date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 11)]


class TestServiceDates:
    def test_workdays(self):
        # 2026-10-09 is a Friday
        service = train_service(train(frequency='on workdays', end=date(2026, 10, 13)), WINDOW)
        assert service_dates(service) == [date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 13)]

    def test_every_second_day_parity_from_start_date(self):
        # Started the day before the window: runs on the 10th, 12th, ..., not on the window start
        service = train_service(train(frequency='every second day', start=date(2026, 10, 8),
                                      end=date(2026, 10, 15)), WINDOW)
        assert service_dates(service) == [date(2026, 10, 10), date(2026, 10, 12), date(2026, 10, 14)]

    def test_every_second_day_parity_over_long_period(self):
        start = date(2025, 6, 2)
        service = train_service(train(frequency='every second day', start=start), WINDOW)
        dates = service_dates(service)
        assert all((d - start).days % 2 == 0 for d in dates)
        assert all((b - a).days == 2 for a, b in zip(dates, dates[1:]))

    def test_odd_days_include_31st_and_1st(self):
        service = train_service(train(frequency='on odd days', start=date(2026, 10, 29),
                                      end=date(2026, 11, 3)), WINDOW)
        assert service_dates(service) == [date(2026, 10, 29), date(2026, 10, 31),
                                          date(2026, 11, 1), date(2026, 11, 3)]

    def test_even_days(self):
        service = train_service(train(frequency='on even days', end=date(2026, 10, 13)), WINDOW)
        assert service_dates(service) == [date(2026, 10, 10), date(2026, 10, 12)]

    def test_past_end_date_has_no_dates(self):
        service = train_service(train(end=date(2026, 1, 1)), WINDOW)
        assert service_dates(service) == []

    def test_start_after_window_has_no_dates(self):
        service = train_service(train(start=date(2027, 6, 1)), WINDOW)
        assert service_dates(service) == []


class TestSplitByService:
    def test_idle_trains_reported(self):
        running, idle = split_by_service(
            [train(1), train(2, end=date(2026, 1, 1)), train(3, start=date(2026, 12, 1))], WINDOW)
        assert [t['ref'] for t in running] == [1, 3]
        assert idle == [2]

    def test_workdays_without_workday_in_range_is_idle(self):
        # Saturday and Sunday only
        _, idle = split_by_service(
            [train(1, 'on workdays', start=date(2026, 10, 10), end=date(2026, 10, 11))], WINDOW)
        assert idle == [1]


class TestCalendar:
    def test_rows(self):
        svc = services.unique_services(
            [train(1), train(2), train(3, 'on workdays', start=date(2026, 11, 1)),
             train(4, 'on odd days')], WINDOW)
        assert calendar.build_calendar(svc) == [
            {'service_id': 'daily', 'monday': 1, 'tuesday': 1, 'wednesday': 1, 'thursday': 1,
             'friday': 1, 'saturday': 1, 'sunday': 1, 'start_date': '20261009', 'end_date': '20270409'},
            {'service_id': 'workdays_20261101_open', 'monday': 1, 'tuesday': 1, 'wednesday': 1,
             'thursday': 1, 'friday': 1, 'saturday': 0, 'sunday': 0,
             'start_date': '20261101', 'end_date': '20270409'},
        ]


class TestCalendarDates:
    def test_only_non_weekly_services(self):
        svc = services.unique_services(
            [train(1), train(2, 'on even days', end=date(2026, 10, 13))], WINDOW)
        assert calendar_dates.build_calendar_dates(svc) == [
            {'service_id': 'even_open_20261013', 'date': '20261010', 'exception_type': 1},
            {'service_id': 'even_open_20261013', 'date': '20261012', 'exception_type': 1},
        ]


class TestRealData:
    def test_every_train_service_is_defined(self):
        window = feed_window(date(2026, 10, 9))
        running, _ = split_by_service(select_routes(load_json(ROUTES_FILE)), window)
        svc = services.unique_services(running, window)
        defined = ({row['service_id'] for row in calendar.build_calendar(svc)}
                   | {row['service_id'] for row in calendar_dates.build_calendar_dates(svc)})
        assert {services.service_id(t) for t in running} == defined

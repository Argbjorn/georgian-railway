from check_gtfs_report import check_report


def notice(code, severity, total=1, samples=()):
    return {'code': code, 'severity': severity, 'totalNotices': total, 'sampleNotices': list(samples)}


class TestCheckReport:
    def test_no_notices(self):
        assert check_report({'notices': []}) == (['No notices'], False)

    def test_warnings_do_not_fail(self):
        lines, has_errors = check_report({'notices': [notice('unused_shape', 'WARNING')]})
        assert not has_errors
        assert lines == ['WARNING: unused_shape (1)']

    def test_error_fails_and_samples_printed(self):
        report = {'notices': [notice('invalid_phone_number', 'ERROR', 2, [{'fieldValue': '1331'}])]}
        lines, has_errors = check_report(report)
        assert has_errors
        assert lines == ['ERROR: invalid_phone_number (2)', '    {"fieldValue": "1331"}']

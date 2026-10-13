# Checks the MobilityData GTFS validator report: prints all notices and exits with 1 if any of them
# is an ERROR. The validator itself exits with 0 regardless of the notices found.
# Usage: python scripts/check_gtfs_report.py <validator output dir>/report.json
import json
import sys


def check_report(report):
    """Returns (lines to print, whether the feed has errors)."""
    lines = []
    has_errors = False
    for notice in sorted(report['notices'], key=lambda n: (n['severity'], n['code'])):
        lines.append(f'{notice["severity"]}: {notice["code"]} ({notice["totalNotices"]})')
        for sample in notice.get('sampleNotices', [])[:5]:
            lines.append(f'    {json.dumps(sample, ensure_ascii=False)}')
        has_errors = has_errors or notice['severity'] == 'ERROR'
    if not report['notices']:
        lines.append('No notices')
    return lines, has_errors


def main(report_path):
    with open(report_path, encoding='utf-8') as f:
        lines, has_errors = check_report(json.load(f))
    print('\n'.join(lines))
    return 1 if has_errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

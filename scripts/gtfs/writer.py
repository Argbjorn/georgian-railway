import csv


def write_table(path, fields, rows, required_fields=()):
    """Writes a GTFS table as UTF-8 CSV.

    `fields` defines the column order (spec order). Optional columns that are empty in every row
    are omitted; required columns are always written.
    """
    unknown = {key for row in rows for key in row} - set(fields)
    if unknown:
        raise ValueError(f'{path}: unknown fields {sorted(unknown)}')

    columns = [field for field in fields
               if field in required_fields or any(row.get(field) not in (None, '') for row in rows)]

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator='\n', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

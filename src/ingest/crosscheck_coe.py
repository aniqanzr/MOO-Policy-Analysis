"""Cross-check the two COE bidding sources against each other.

Run it:

    python -m src.ingest.crosscheck_coe

Section 8 names two sources that carry the same numbers. `coe-bidding-results` is LTA's long
table, one row per category per exercise. `quota-premium-monthly` is the SingStat and LTA wide
table. They overlap from 2010-01 and both publish quota, successful bids, bids received and
quota premium per category per exercise, so every overlapping value can be compared.

This is not a model test. It is the stage 2 gate asking what is actually in the files, run
before stage 3 sums quota times premium and blames MOF for the difference. Two kinds of
disagreement come out of it and they need different handling, so they are reported separately:
a value written two ways, and two different values.

The wide table is treated as the reference where they conflict, because its per-category
figures sum to its own published category totals and the long table's do not. That check is
part of the output rather than an assertion made here.
"""

import argparse
import csv
import sys
from pathlib import Path

from src.ingest.sources import by_key

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
LONG_FILE = by_key("coe_bidding_results").raw_filename
WIDE_FILE = by_key("quota_and_premium_monthly").raw_filename

# Category labels in the long table mapped to the series-name prefix in the wide table.
CATEGORIES = {
    "Category A": "Cars Up To 1600cc And 97kW",
    "Category B": "Cars Above 1600cc Or 97kW",
    "Category C": "Goods Vehicles & Buses",
    "Category D": "Motorcycles",
    "Category E": "Open Category",
}

# Long-table column mapped to the measure name inside a wide-table series label.
MEASURES = {
    "quota": "Quota",
    "bids_success": "Successful Bids",
    "bids_received": "Bids Received",
    "premium": "Quota Premium",
}

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ORDINALS = {"1": "1st", "2": "2nd"}

# The wide table writes a suspended or unpublished exercise as one of these.
MISSING = {"", "-", "na", "n.a.", "s"}

# The two conflicts found when this check was written, both in the long table, both repeating
# the value from the row above. Recorded so the script can tell an already-understood defect
# from a new one. A-12 says the thing to watch for is a third conflict appearing, which would
# mean the upstream table changed, so that is what the exit status reports.
KNOWN_CONFLICTS = {
    ("2010-01", "2", "Category D", "premium", "20090", "852"),
    ("2010-02", "1", "Category B", "quota", "1154", "693"),
}


def wide_column(month):
    """`2010-01` in the long table is the column `2010Jan` in the wide table."""
    year, number = month.split("-")
    return f"{year}{MONTHS[int(number) - 1]}"


def normalise(value):
    """Strip thousands separators so `1,438` and `1438` compare as the same number."""
    return value.strip().replace(",", "")


def load(raw_dir):
    long_rows = list(csv.DictReader((raw_dir / LONG_FILE).open(newline="")))
    wide_rows = list(csv.reader((raw_dir / WIDE_FILE).open(newline="")))
    header = wide_rows[0]
    wide = {row[0]: row for row in wide_rows[1:]}
    return long_rows, header, wide


def compare(long_rows, header, wide):
    """Every overlapping value, split into formatting differences and real conflicts."""
    formatting, conflicts, compared, no_column = [], [], 0, set()

    for row in long_rows:
        column = wide_column(row["month"])
        if column not in header:
            no_column.add(row["month"])
            continue

        index = header.index(column)
        prefix = CATEGORIES[row["vehicle_class"]]
        ordinal = ORDINALS[row["bidding_no"]]

        for field, measure in MEASURES.items():
            series = wide.get(f"{prefix}, {measure}, {ordinal} Bidding")
            if series is None or series[index].strip().lower() in MISSING:
                continue

            compared += 1
            left, right = row[field].strip(), series[index].strip()
            if left == right:
                continue

            record = (row["month"], row["bidding_no"], row["vehicle_class"],
                      field, left, right)
            if normalise(left) == normalise(right):
                formatting.append(record)
            else:
                conflicts.append(record)

    return compared, sorted(no_column), formatting, conflicts


def category_totals(header, wide, month, ordinal):
    """Per-category quota summed against the wide table's own published total.

    The tie-breaker when the two sources conflict on a quota. A source whose parts sum to its
    own total is the one to believe.
    """
    index = header.index(wide_column(month))
    parts = 0
    for prefix in CATEGORIES.values():
        value = wide[f"{prefix}, Quota, {ordinal} Bidding"][index].strip()
        if value.lower() in MISSING:
            return None, None
        parts += int(normalise(value))

    published = wide[f"Total Quota, {ordinal} Bidding"][index].strip()
    if published.lower() in MISSING:
        return parts, None
    return parts, int(normalise(published))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)

    long_rows, header, wide = load(args.raw)
    compared, no_column, formatting, conflicts = compare(long_rows, header, wide)

    print(f"\nvalues compared across the overlap: {compared}")
    if no_column:
        print(f"months in the long table with no wide column: {', '.join(no_column)}")

    print(f"\nsame number written two ways: {len(formatting)}")
    if formatting:
        fields = sorted({record[3] for record in formatting})
        months = sorted({record[0] for record in formatting})
        print(f"  affected columns: {', '.join(fields)}")
        print(f"  from {months[0]} onward")
        print("  the long table writes thousands separators, the wide table does not.")
        print("  read those columns as strings and strip commas before any numeric use.")

    unexpected = [c for c in conflicts if tuple(c) not in KNOWN_CONFLICTS]
    missing = KNOWN_CONFLICTS - {tuple(c) for c in conflicts}

    print(f"\ngenuine value conflicts: {len(conflicts)}")
    for record in conflicts:
        month, bidding, category, field, left, right = record
        status = "new" if tuple(record) not in KNOWN_CONFLICTS else "known, see A-12"
        print(f"  {month} bidding {bidding} {category} {field}: "
              f"long={left} wide={right}  [{status}]")
        if field == "quota":
            parts, published = category_totals(header, wide, month, ORDINALS[bidding])
            if published is not None:
                agrees = "agrees" if parts == published else "disagrees"
                print(f"    wide per-category quota sums to {parts} against its own "
                      f"published total of {published}, {agrees}")

    if missing:
        print("\nConflicts recorded in A-12 that no longer appear:")
        for month, bidding, category, field, left, right in sorted(missing):
            print(f"  {month} bidding {bidding} {category} {field}")
        print("  Upstream may have fixed them. Update A-12 and KNOWN_CONFLICTS.")

    if unexpected:
        print(f"\n{len(unexpected)} conflict(s) not recorded in A-12. The upstream table has")
        print("changed. Investigate before running anything downstream.")

    print()
    # Nonzero on a change, not on the defects already understood and written up. A check that
    # always fails is a check nobody reads.
    return 1 if (unexpected or missing) else 0


if __name__ == "__main__":
    sys.exit(main())

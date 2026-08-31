"""Reconcile the SingStat deregistration series against Annex A. Resolves A-16.

Run it:

    python -m src.ingest.crosscheck_deregistrations

Section 8 originally held that deregistration counts are not published as a standalone series
and that stage 4 would extract them from Annex A PDFs. SingStat table M650291 publishes them
monthly from 1990. The question this answers is not whether that table exists but whether it
carries the same quantity the quota formula uses, which is the difference between saving stage
4 a week and quietly modelling the wrong number.

The test sums M650291 over exactly the window each annex names in its own B1 row, and compares
category by category against the figure that annex prints. Four consecutive quarters straddling
February 2023, two under each regime.

Two things it deliberately does not do. It does not compare against the annex's totals column,
because that column sums the four VQS categories only while M650291's own total line also
includes taxis and VQS-exempt vehicles. And it does not treat B1 as the formula's input, because
from August 2023 the formula runs on B1 minus B2 and B2 is not in the published series.
"""

import argparse
import json
import sys
from pathlib import Path

from src.ingest.annexa import QUARTERS
from src.ingest.sources import by_key

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
SERIES_FILE = by_key("vqs_deregistrations_monthly").raw_filename

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# Series in M650291 that the annex's category columns do not cover.
OUTSIDE_THE_CATEGORIES = ("Taxis", "Vehicles Exempted From VQS")
TOTAL_ROW = "Total Motor Vehicles De-Registered"


def load_series(path):
    data = json.loads(path.read_text())
    return {
        row["rowText"]: {c["key"]: c["value"] for c in row["columns"]}
        for row in data["row"]
    }


def window(year, month, count):
    """SingStat period keys for `count` months from `year`/`month`, as "2022 Apr"."""
    keys = []
    for _ in range(count):
        keys.append(f"{year} {MONTHS[month - 1]}")
        month += 1
        if month == 13:
            month, year = 1, year + 1
    return keys


def total_over(series, category, keys):
    values = series[category]
    missing = [key for key in keys if key not in values]
    if missing:
        raise KeyError(f"{category} missing {len(missing)} periods, first {missing[0]}")
    return sum(int(values[key]) for key in keys)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW)
    args = parser.parse_args(argv)

    series = load_series(args.raw / SERIES_FILE)
    mismatches = []

    for quarter in QUARTERS:
        keys = window(*quarter.b1_window)
        print(f"\n{quarter.quota_period}   {quarter.regime}")
        print(f"  B1 window: {quarter.b1_window_label} ({len(keys)} months)")

        computed_total = 0
        for category, published in quarter.b1.items():
            computed = total_over(series, category, keys)
            computed_total += computed
            ok = computed == published
            if not ok:
                mismatches.append((quarter.slug, category, computed, published))
            print(
                f"    {category:<38}{computed:>9,}  vs {published:>9,}  "
                f"{'match' if ok else 'MISMATCH'}"
            )

        ok = computed_total == quarter.b1_total
        if not ok:
            mismatches.append((quarter.slug, "stated total", computed_total,
                               quarter.b1_total))
        print(
            f"    {'four categories summed':<38}{computed_total:>9,}  vs "
            f"{quarter.b1_total:>9,}  {'match' if ok else 'MISMATCH'}"
        )

        outside = sum(total_over(series, name, keys) for name in OUTSIDE_THE_CATEGORIES)
        published_total = total_over(series, TOTAL_ROW, keys)
        print(
            f"    M650291 total row is {published_total:,}, which is "
            f"{outside:,} higher: it includes {' and '.join(OUTSIDE_THE_CATEGORIES).lower()}."
        )

        if quarter.guaranteed:
            guaranteed = sum(quarter.guaranteed.values())
            share = guaranteed / computed_total * 100
            print(
                f"    B2 guaranteed deregistrations: {guaranteed:,}, "
                f"{share:.5f} percent of B1. The formula runs on B1 minus B2."
            )

    print()
    if mismatches:
        print(f"{len(mismatches)} mismatches:")
        for slug, what, computed, published in mismatches:
            print(f"  {slug} {what}: computed {computed:,}, annex {published:,}")
        return 1

    checks = sum(len(q.b1) + 1 for q in QUARTERS)
    print(f"All {checks} comparisons across {len(QUARTERS)} quarters reconcile exactly.")
    print(
        "M650291 carries Annex A row B1, gross deregistrations, on the four VQS category\n"
        "lines. It does not carry B2, the guaranteed deregistration subset, which from the\n"
        "August 2023 annex the formula subtracts before taking its quarterly slice. Read\n"
        "A-16 before relying on either fact."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

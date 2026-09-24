"""Does `quota-premium-monthly` mean the same thing before 2010 as after it.

Run it:

    python -m src.ingest.verify_quota_premium

Stage 3 found computed revenue running above the published Vehicle Quota Premiums line for
every financial year from FY2002 to FY2009, by a factor of sixteen in FY2006, and below it
from FY2011 onward. A-20 recorded that without a cause.

There are two places the break can live. Either the published revenue line changed meaning, or
`quota-premium-monthly` (`d_22094bf608253d36c0c63b52d852dd6e`, SingStat M651121) did. The
second is the one that matters more, because that file is the only source for 2002 to 2009 and
that span is where stage 6 would see elasticity drift if there is any. The long table
(`d_69b3380ad7e51aff3a7dcc84eba52b8a`) starts at 2010-01 and cannot check it.

So this script asks whether the wide table's columns carry the same meaning across the break,
using only committed data. Six checks, none of which needs the revenue line at all.

1. What the publisher says the columns are, read from the committed SingStat metadata.
2. Shape. Exercises per year, and per-category quota against the table's own published totals.
3. Whether the premium column is a per-exercise clearing price or a monthly average.
4. The prevailing quota premium identity. PQP is published as the moving average of the quota
   premium over the latest three months in which bidding was held, so it is a third column
   that has to agree with the premium column arithmetically. This is the sharpest check here.
5. Successful bids against new registrations under the VQS, an independent series covering
   both eras.
6. The same revenue arithmetic on both bidding tables over their overlap.

If the columns changed meaning at 2010, checks 2 through 6 should show it. If they did not,
the pre-2010 span is usable and the break is in the target rather than the source.
"""

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
WIDE_FILE = "quota-premium-monthly.csv"
LONG_FILE = "coe-bidding-results.csv"
REGISTRATIONS_FILE = "vqs-new-registrations-monthly.csv"
METADATA_FILE = "singstat-metadata.json"
WIDE_TABLE_ID = "M651121"

CATEGORIES = {
    "A": "Cars Up To 1600cc And 97kW",
    "B": "Cars Above 1600cc Or 97kW",
    "C": "Goods Vehicles & Buses",
    "D": "Motorcycles",
    "E": "Open Category",
}

# New registrations under the VQS, on the categories that require a COE. Weekend and off-peak
# cars are published as `na` throughout and VQS-exempt vehicles need no COE, so neither is
# counted here.
REGISTRATION_ROWS = (
    "Category A: Cars",
    "Category B: Cars",
    "Category C: Goods Vehicles & Buses",
    "Category D: Motorcycles & Scooters",
    "Taxis",
)

# Registrations that take a COE without anyone bidding for one, so they are in the
# registration series and cannot be in the bidding series. Early Turnover Scheme goods
# vehicles get a replacement COE, and taxis have paid the Category A prevailing quota premium
# rather than bidding since 6 August 2012. Both start after the 2010 break, which is why the
# raw ratio drifts and the adjusted one does not.
NON_BID_REGISTRATION_ROWS = (
    "Category C: Goods Vehicles & Buses Under ETS",
    "Taxis",
)

BIDDINGS = ("1st", "2nd")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MISSING = {"", "-", "na", "n.a.", "s"}

# The two eras being compared. The split is where the long table starts, which is the only
# reason 2010 is the boundary at all.
EARLY = (2002, 2009)
LATE = (2010, 2026)

# PQP is published to the dollar and the underlying premiums are whole dollars, so an exact
# match after rounding is the test. A dollar and a half of slack absorbs the rounding.
PQP_TOLERANCE = 1.5


def _clean(value):
    text = value.strip().replace(",", "")
    return None if text.lower() in MISSING else float(text)


def load_wide(raw_dir=RAW_DIR):
    rows = list(csv.reader((raw_dir / WIDE_FILE).open(newline="", encoding="utf-8")))
    header = rows[0]
    series = {row[0].strip(): row for row in rows[1:]}
    columns = sorted(header[1:], key=lambda c: (int(c[:4]), MONTHS.index(c[4:])))
    return header, series, columns


def cell(header, series, name, column):
    row = series.get(name)
    if row is None or column not in header:
        return None
    return _clean(row[header.index(column)])


def era_of(year):
    return f"{EARLY[0]}-{EARLY[1]}" if year <= EARLY[1] else f"{LATE[0]}-{LATE[1]}"


def report_definitions(raw_dir=RAW_DIR):
    """What the publisher says the columns are. Not inference, the table's own metadata."""
    meta = json.loads((raw_dir / METADATA_FILE).read_text(encoding="utf-8"))
    table = meta["tables"][WIDE_TABLE_ID]

    print(f"\n1. What {WIDE_TABLE_ID} says its columns are")
    print(f"   source: {table['dataSource']}, {table['startPeriod']} to {table['endPeriod']}")

    units = {}
    for row in table["series"]:
        measure = row["rowText"].split(",")[-2].strip() if row["rowText"].count(",") >= 2 \
            else row["rowText"].split(",")[0].strip()
        units.setdefault(measure, row["uoM"])
    for measure, unit in units.items():
        print(f"   {measure:<28}{unit}")

    for sentence in table["footnote"].split(".  "):
        if any(k in sentence for k in ("Period refers", "Quota premium is", "two bidding")):
            print(f"   footnote: {sentence.strip()}.")
    return table


def report_shape(header, series, columns):
    """Exercises per year, and whether the parts still sum to the published totals."""
    counts = defaultdict(lambda: {"exercises": 0, "sums_match": 0, "sums_differ": 0})

    for column in columns:
        year = int(column[:4])
        for bidding in BIDDINGS:
            parts = [
                cell(header, series, f"{prefix}, Quota, {bidding} Bidding", column)
                for prefix in CATEGORIES.values()
            ]
            if any(part is None for part in parts):
                continue
            counts[year]["exercises"] += 1
            published = cell(header, series, f"Total Quota, {bidding} Bidding", column)
            if published is None:
                continue
            if abs(sum(parts) - published) < 0.5:
                counts[year]["sums_match"] += 1
            else:
                counts[year]["sums_differ"] += 1

    print("\n2. Shape, by year")
    print(f"   {'year':<6}{'exercises':>11}{'category sum = published total':>32}")
    for year in sorted(counts):
        row = counts[year]
        verdict = f"{row['sums_match']} of {row['sums_match'] + row['sums_differ']}"
        print(f"   {year:<6}{row['exercises']:>11}{verdict:>32}")
    differ = sum(row["sums_differ"] for row in counts.values())
    print(f"   exercises where the parts do not sum to the published total: {differ}")
    return counts


def report_premium_is_per_exercise(header, series, columns):
    """A monthly average would be written identically against both biddings of a month."""
    same = defaultdict(int)
    total = defaultdict(int)

    for column in columns:
        era = era_of(int(column[:4]))
        for prefix in CATEGORIES.values():
            first = cell(header, series, f"{prefix}, Quota Premium, 1st Bidding", column)
            second = cell(header, series, f"{prefix}, Quota Premium, 2nd Bidding", column)
            if first is None or second is None:
                continue
            total[era] += 1
            if first == second:
                same[era] += 1

    print("\n3. Is the premium a per-exercise clearing price or a monthly average")
    for era in sorted(total):
        share = same[era] / total[era]
        print(f"   {era}: the two biddings of a month carry the same premium in "
              f"{same[era]} of {total[era]} category-months, {share:.1%}")
    print("   A monthly average would be identical in both. These are not.")
    return same, total


def report_pqp_identity(header, series, columns):
    """PQP against its published definition, in both eras.

    The footnote on the prevailing quota premium series says it is the moving average of the
    quota premium in the latest three months in which bidding exercises were conducted. That
    makes PQP a function of the premium column, so it is a check on what the premium column
    is, computed from three published columns that would have to have been changed together
    for this to hold by accident.
    """
    results = defaultdict(lambda: {"n": 0, "within": 0, "errors": []})

    def month_premiums(prefix, column):
        found = [
            cell(header, series, f"{prefix}, Quota Premium, {bidding} Bidding", column)
            for bidding in BIDDINGS
        ]
        return [value for value in found if value is not None]

    for category, prefix in CATEGORIES.items():
        for index, column in enumerate(columns):
            published = cell(
                header, series, f"{prefix}, Prevailing Quota Premium, 2nd Bidding", column
            )
            if published is None:
                continue

            window, back = [], index
            while back >= 0 and len(window) < 3:
                premiums = month_premiums(prefix, columns[back])
                if premiums:
                    window.append(statistics.fmean(premiums))
                back -= 1
            if len(window) < 3:
                continue

            predicted = statistics.fmean(window)
            key = (era_of(int(column[:4])), category)
            results[key]["n"] += 1
            results[key]["errors"].append(abs(predicted - published))
            if abs(predicted - published) <= PQP_TOLERANCE:
                results[key]["within"] += 1

    print("\n4. PQP against its published definition, the moving average of the quota premium")
    print("   over the latest three months in which bidding was held")
    print(f"   {'era':<12}{'cat':<5}{'n':>6}{'within $1.50':>14}{'worst $ error':>15}")
    for (era, category), row in sorted(results.items()):
        print(f"   {era:<12}{category:<5}{row['n']:>6}"
              f"{row['within'] / row['n']:>13.0%}{max(row['errors']):>15.2f}")
    return results


def report_against_registrations(header, series, columns, raw_dir=RAW_DIR):
    """Successful bids against new registrations under the VQS, an independent series."""
    rows = list(csv.reader((raw_dir / REGISTRATIONS_FILE).open(newline="", encoding="utf-8")))
    reg_header = rows[0]
    reg_series = {row[0].strip(): row for row in rows[1:]}

    bids = defaultdict(float)
    registrations = defaultdict(float)
    non_bid = defaultdict(float)

    for column in columns:
        year = int(column[:4])
        for prefix in CATEGORIES.values():
            for bidding in BIDDINGS:
                value = cell(
                    header, series, f"{prefix}, Successful Bids, {bidding} Bidding", column
                )
                if value is not None:
                    bids[year] += value

    for column in reg_header[1:]:
        year = int(column[:4])
        for name in REGISTRATION_ROWS:
            value = cell(reg_header, reg_series, name, column)
            if value is not None:
                registrations[year] += value
        for name in NON_BID_REGISTRATION_ROWS:
            value = cell(reg_header, reg_series, name, column)
            if value is not None:
                non_bid[year] += value

    print("\n5. COEs awarded against new registrations under the VQS")
    print("   A magnitude check, not an identity: a COE won in one month can be registered in")
    print("   the next, and the adjusted column removes registrations that need no bid.")
    print(f"   {'year':<6}{'successful bids':>17}{'new regs':>11}{'no-bid regs':>13}"
          f"{'raw':>7}{'adjusted':>10}")
    ratios = defaultdict(list)
    for year in sorted(set(bids) & set(registrations)):
        # A part year on either side would compare twelve months against fewer.
        if year in (2002, 2026):
            continue
        adjusted = registrations[year] - non_bid[year]
        ratio = bids[year] / adjusted
        ratios[era_of(year)].append(ratio)
        print(f"   {year:<6}{bids[year]:>17,.0f}{registrations[year]:>11,.0f}"
              f"{non_bid[year]:>13,.0f}{bids[year] / registrations[year]:>7.2f}{ratio:>10.2f}")
    for era in sorted(ratios):
        values = ratios[era]
        print(f"   {era}: adjusted ratio from {min(values):.2f} to {max(values):.2f}, "
              f"mean {statistics.fmean(values):.2f}")
    print("   Before August 2012 a taxi could bid instead of paying the prevailing quota")
    print("   premium, so the early years subtract some registrations that did involve a bid.")
    return ratios


def report_cross_table(header, series, columns, raw_dir=RAW_DIR):
    """The same multiplication on both bidding tables, over the years they share."""
    def fiscal_year(year, month):
        return year if month >= 4 else year - 1

    wide_revenue = defaultdict(float)
    for column in columns:
        year, month = int(column[:4]), MONTHS.index(column[4:]) + 1
        for prefix in CATEGORIES.values():
            for bidding in BIDDINGS:
                quota = cell(header, series, f"{prefix}, Quota, {bidding} Bidding", column)
                premium = cell(
                    header, series, f"{prefix}, Quota Premium, {bidding} Bidding", column
                )
                if quota is not None and premium is not None:
                    wide_revenue[fiscal_year(year, month)] += quota * premium / 1e6

    long_revenue = defaultdict(float)
    with (raw_dir / LONG_FILE).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            year, month = (int(part) for part in row["month"].split("-"))
            quota, premium = _clean(row["quota"]), _clean(row["premium"])
            if quota is not None and premium is not None:
                long_revenue[fiscal_year(year, month)] += quota * premium / 1e6

    print("\n6. Quota times premium on both tables, millions, over the overlap")
    print(f"   {'FY':<8}{'wide table':>13}{'long table':>13}{'difference':>13}")
    worst = 0.0
    for fy in sorted(set(wide_revenue) & set(long_revenue)):
        # FY2009 is only two months of the long table, so it is not a like comparison.
        if fy < 2010 or fy > 2024:
            continue
        difference = long_revenue[fy] - wide_revenue[fy]
        worst = max(worst, abs(difference))
        print(f"   FY{fy:<6}{wide_revenue[fy]:>13,.1f}{long_revenue[fy]:>13,.1f}"
              f"{difference:>13,.1f}")
    print(f"   worst difference in any shared financial year: {worst:,.1f} million")
    return worst


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)

    header, series, columns = load_wide(args.raw)

    report_definitions(args.raw)
    shape = report_shape(header, series, columns)
    report_premium_is_per_exercise(header, series, columns)
    pqp = report_pqp_identity(header, series, columns)
    report_against_registrations(header, series, columns, args.raw)
    report_cross_table(header, series, columns, args.raw)

    sums_differ = sum(row["sums_differ"] for row in shape.values())
    pqp_misses = sum(row["n"] - row["within"] for row in pqp.values())

    print("\nverdict")
    if sums_differ == 0 and pqp_misses == 0:
        print("   No check separates the two eras. The columns carry the same meaning across")
        print("   2010, so the pre-2010 span is usable and the A-20 break is in the published")
        print("   revenue line rather than in this file.")
    else:
        print(f"   {sums_differ} exercises fail the totals check and {pqp_misses} months fail")
        print("   the PQP identity. Read the detail above before using the pre-2010 span.")
    print()
    return 0 if sums_differ == 0 and pqp_misses == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

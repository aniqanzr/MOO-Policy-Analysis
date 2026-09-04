"""Revenue from the bidding record, and the A-10 reconciliation against the published line.

Run it:

    python -m src.model.revenue                # the latest financial year with actuals
    python -m src.model.revenue --fy 2023
    python -m src.model.revenue --series       # every financial year the bidding file covers

O3 is total premium collected. This module computes it from the published bidding record and
compares it against the Vehicle Quota Premiums line in the government accounts, which is the
only external check the project has on either the premium series handling or the quota
accounting. Stage 3 of the build sequence runs it before anything is built on top of the
bidding data, so that an ingestion error surfaces here rather than inside a fit.

Three things the brief and the register insist on, all of them enforced below.

All five categories are summed. The published line covers A, B, C, D and E even though only
A, B and C are decision dimensions. See A-06.

Periods are aligned before comparing. The published figures are financial years beginning
1 April. The bidding record is monthly exercises. FY2024 means April 2024 to March 2025.

The target year has to be an actual figure. Revised and budgeted estimates are not outturns
and reconciling against one measures the estimate, not the pipeline. The cutoff is read from
the table footnote in the committed metadata rather than hardcoded here.

Source choice. Quota, successful bids and premium come from `quota-premium-monthly.csv`, the
wide SingStat and LTA table, not from the long `coe-bidding-results.csv`. A-12 found two
values where the two sources conflict and settled the wide table as the reference, and the
wide table also reaches back to 2002Feb where the long table starts at 2010-01. A-13's
thousands separators are stripped on read for the same reason.

Two revenue bases are reported. Quota times premium is what section 4.4 specifies. Successful
bids times premium is what was actually paid, since an undersubscribed exercise issues fewer
COEs than the quota released. The gap between them is small and reporting both costs nothing.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
BIDDING_FILE = "quota-premium-monthly.csv"
TARGET_FILE = "vehicle-quota-premiums-annual.csv"
TARGET_META_FILE = "vehicle-quota-premiums-annual.meta.json"

# Category label used here, mapped to the series-name prefix in the wide table. All five,
# per A-06: the published revenue line covers every category, not just the decision ones.
CATEGORIES = {
    "A": "Cars Up To 1600cc And 97kW",
    "B": "Cars Above 1600cc Or 97kW",
    "C": "Goods Vehicles & Buses",
    "D": "Motorcycles",
    "E": "Open Category",
}

BIDDINGS = ("1st", "2nd")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# How the wide table writes a suspended or unpublished exercise.
MISSING = {"", "-", "na", "n.a.", "s"}

# The government financial year begins 1 April.
FY_START_MONTH = 4

BASES = ("quota", "successful")

ACTUALS_SENTENCE = re.compile(r"Data up to FY(\d{4}) are actual figures")


class ReconciliationError(RuntimeError):
    """The reconciliation cannot be run as asked. Not a result, a refusal to produce one."""


@dataclass(frozen=True)
class Exercise:
    """One category in one bidding exercise."""

    year: int
    month: int
    bidding: str
    category: str
    quota: float
    successful: float
    premium: float

    @property
    def fiscal_year(self) -> int:
        return fiscal_year(self.year, self.month)

    def revenue(self, basis: str) -> float:
        """Dollars collected in this exercise under the given basis."""
        if basis == "quota":
            return self.quota * self.premium
        if basis == "successful":
            return self.successful * self.premium
        raise ValueError(f"basis must be one of {BASES}, got {basis!r}")


@dataclass(frozen=True)
class Target:
    """The published Vehicle Quota Premiums line, in millions of dollars."""

    values: dict[int, float]
    latest_actual_fy: int
    meta: dict

    def actual(self, fy: int) -> float:
        if fy not in self.values:
            raise ReconciliationError(
                f"FY{fy} is not in {TARGET_FILE}, which covers "
                f"FY{min(self.values)} to FY{max(self.values)}"
            )
        if fy > self.latest_actual_fy:
            kind = "a budgeted or revised estimate"
            raise ReconciliationError(
                f"FY{fy} is {kind}, not an actual figure. The table footnote gives actuals "
                f"up to FY{self.latest_actual_fy}. Reconciling against an estimate measures "
                f"the estimate rather than the pipeline, so it is refused. See A-10."
            )
        return self.values[fy]


def fiscal_year(year: int, month: int) -> int:
    """The financial year a calendar month falls in. April 2024 to March 2025 is FY2024."""
    return year if month >= FY_START_MONTH else year - 1


def fiscal_year_months(fy: int) -> list[tuple[int, int]]:
    """The twelve calendar months of a financial year, in order."""
    return [(fy, m) for m in range(FY_START_MONTH, 13)] + [
        (fy + 1, m) for m in range(1, FY_START_MONTH)
    ]


def _clean(value: str) -> float | None:
    """A wide-table cell as a number, or None where nothing was published.

    Thousands separators are stripped because A-13 found them written inconsistently across
    the published files. A missing marker is not a zero and is not treated as one.
    """
    text = value.strip().replace(",", "")
    if text.lower() in MISSING:
        return None
    return float(text)


def load_bidding(raw_dir: Path = RAW_DIR) -> tuple[list[Exercise], list[dict], list[str]]:
    """Every category-exercise cell in the wide table.

    Returns the exercises that carry a premium, the cells that do not, and the month columns
    the file publishes. A cell with no premium is not revenue and not an error either: April
    to June 2020 were suspended, and the register records that under A-11.
    """
    rows = list(csv.reader((raw_dir / BIDDING_FILE).open(newline="", encoding="utf-8")))
    header, series = rows[0], {row[0]: row for row in rows[1:]}
    columns = header[1:]

    exercises: list[Exercise] = []
    gaps: list[dict] = []

    for column in columns:
        year, month = _parse_column(column)
        index = header.index(column)
        for category, prefix in CATEGORIES.items():
            for bidding in BIDDINGS:
                premium = _cell(series, f"{prefix}, Quota Premium, {bidding} Bidding", index)
                quota = _cell(series, f"{prefix}, Quota, {bidding} Bidding", index)
                successful = _cell(
                    series, f"{prefix}, Successful Bids, {bidding} Bidding", index
                )
                if premium is None or quota is None or successful is None:
                    gaps.append(
                        {
                            "year": year,
                            "month": month,
                            "bidding": bidding,
                            "category": category,
                            "premium": premium,
                            "quota": quota,
                            "successful": successful,
                        }
                    )
                    continue
                exercises.append(
                    Exercise(year, month, bidding, category, quota, successful, premium)
                )

    return exercises, gaps, columns


def _cell(series: dict[str, list[str]], name: str, index: int) -> float | None:
    row = series.get(name)
    return None if row is None else _clean(row[index])


def _parse_column(column: str) -> tuple[int, int]:
    """`2024Apr` to (2024, 4)."""
    year, month = column[:4], column[4:]
    return int(year), MONTHS.index(month) + 1


def load_target(raw_dir: Path = RAW_DIR) -> Target:
    """The published line, with the actual-versus-estimate cutoff read off the footnote.

    The cutoff is not a constant in this file. It comes from the sentence in the table
    footnote that the pull script commits, so a re-pull that moves the cutoff moves this too.
    """
    meta = json.loads((raw_dir / TARGET_META_FILE).read_text(encoding="utf-8"))
    footnote = meta.get("table", {}).get("footnote", "")
    match = ACTUALS_SENTENCE.search(footnote)
    if not match:
        raise ReconciliationError(
            f"{TARGET_META_FILE} no longer says which financial years are actual figures. "
            "Read the footnote before reconciling against this file."
        )

    values: dict[int, float] = {}
    with (raw_dir / TARGET_FILE).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            values[int(row["financial_year"])] = float(row["vehicle_quota_premiums_million"])

    return Target(values=values, latest_actual_fy=int(match.group(1)), meta=meta)


def covered_fiscal_years(columns: list[str]) -> list[int]:
    """Financial years for which the bidding file publishes all twelve months."""
    published = {_parse_column(column) for column in columns}
    years = {fiscal_year(*month) for month in published}
    return sorted(fy for fy in years if set(fiscal_year_months(fy)) <= published)


def revenue_by_category(
    exercises: list[Exercise], fy: int, basis: str = "quota"
) -> dict[str, float]:
    """Dollars per category for one financial year."""
    totals = {category: 0.0 for category in CATEGORIES}
    for exercise in exercises:
        if exercise.fiscal_year == fy:
            totals[exercise.category] += exercise.revenue(basis)
    return totals


def revenue_in_window(exercises: list[Exercise], start_year: int, start_month: int) -> float:
    """Dollars over the twelve months beginning at a given month.

    Used to show that the residual is not an artefact of the period alignment. Shifting the
    window moves the total by far less than the residual.
    """
    window = set()
    for offset in range(12):
        month = start_month + offset
        window.add((start_year + (month - 1) // 12, (month - 1) % 12 + 1))
    return sum(
        exercise.revenue("quota")
        for exercise in exercises
        if (exercise.year, exercise.month) in window
    )


def weighted_mean_premium(exercises: list[Exercise], fy: int) -> float:
    """Quota-weighted mean clearing premium across all categories in a financial year.

    The unit price implied by the year's own bidding, used only to express the residual as a
    number of COEs. It is a diagnostic, not a parameter, and nothing downstream reads it.
    """
    quota = sum(e.quota for e in exercises if e.fiscal_year == fy)
    if quota == 0:
        return float("nan")
    return sum(e.quota * e.premium for e in exercises if e.fiscal_year == fy) / quota


@dataclass(frozen=True)
class Reconciliation:
    fy: int
    computed: dict[str, float]          # basis to dollars
    by_category: dict[str, float]       # category to dollars, quota basis
    published_million: float
    exercises: int
    gaps: list[dict]

    @property
    def computed_million(self) -> float:
        return self.computed["quota"] / 1e6

    @property
    def residual_million(self) -> float:
        """Published minus computed. Positive means the bidding record falls short."""
        return self.published_million - self.computed_million

    @property
    def ratio(self) -> float:
        return self.computed_million / self.published_million


def reconcile(fy: int, raw_dir: Path = RAW_DIR) -> Reconciliation:
    """Computed revenue against the published line for one financial year.

    Refuses a year that is not an actual figure, and a year the bidding file does not cover
    in full. A part-year total compared against a full-year published figure is not a
    reconciliation, it is a smaller number.
    """
    exercises, gaps, columns = load_bidding(raw_dir)
    target = load_target(raw_dir)

    if fy not in covered_fiscal_years(columns):
        raise ReconciliationError(
            f"{BIDDING_FILE} does not publish all twelve months of FY{fy}. Covered: "
            f"FY{min(covered_fiscal_years(columns))} to FY{max(covered_fiscal_years(columns))}."
        )

    published = target.actual(fy)
    in_year = [e for e in exercises if e.fiscal_year == fy]

    return Reconciliation(
        fy=fy,
        computed={
            basis: sum(e.revenue(basis) for e in in_year) for basis in BASES
        },
        by_category=revenue_by_category(exercises, fy),
        published_million=published,
        exercises=len({(e.year, e.month, e.bidding) for e in in_year}),
        gaps=[g for g in gaps if fiscal_year(g["year"], g["month"]) == fy],
    )


def _report(fy: int, raw_dir: Path) -> int:
    exercises, gaps, columns = load_bidding(raw_dir)
    target = load_target(raw_dir)
    result = reconcile(fy, raw_dir)

    table = target.meta["table"]
    print(f"\ntarget: {table['id']} series {target.meta['series']['seriesNo']}, "
          f"{target.meta['series']['rowText']}, {target.meta['series']['uoM']}")
    print(f"        {table['dataSource']}, table last updated {table['dataLastUpdated']}")
    print(f"        actual figures up to FY{target.latest_actual_fy}")
    print(f"source: {BIDDING_FILE}, all five categories, both biddings")

    print(f"\nFY{fy}, April {fy} to March {fy + 1}, in millions of dollars")
    print(f"  computed, quota times premium            {result.computed_million:>12,.1f}")
    print(f"  computed, successful bids times premium  "
          f"{result.computed['successful'] / 1e6:>12,.1f}")
    print(f"  published                                {result.published_million:>12,.1f}")
    print(f"  residual, published minus computed       {result.residual_million:>12,.1f}")
    print(f"  computed as a share of published         {result.ratio:>12.1%}")

    print("\nby category, quota times premium, millions")
    for category, total in result.by_category.items():
        print(f"  Category {category}  {total / 1e6:>10,.1f}")

    print(f"\nexercises found: {result.exercises} of 24")
    if result.gaps:
        months = sorted({f"{g['year']}-{g['month']:02d}" for g in result.gaps})
        print(f"cells with nothing published: {len(result.gaps)} in {', '.join(months)}")
    else:
        print("cells with nothing published: none")

    print("\nperiod alignment, twelve-month windows, quota basis, millions")
    for label, start in (
        (f"April {fy}, the financial year", (fy, 4)),
        (f"January {fy}, calendar year", (fy, 1)),
        (f"March {fy}, one month early", (fy, 3)),
        (f"May {fy}, one month late", (fy, 5)),
    ):
        total = revenue_in_window(exercises, *start) / 1e6
        print(f"  {label:<34}{total:>12,.1f}")

    unit = weighted_mean_premium(exercises, fy)
    print("\nresidual expressed as COEs, a diagnostic and nothing more")
    print(f"  quota-weighted mean premium              {unit:>12,.0f}")
    print(f"  residual divided by that premium         "
          f"{result.residual_million * 1e6 / unit:>12,.0f}")
    print("  The bidding record cannot contain a payment made at the prevailing quota")
    print("  premium without a bid, which is what a COE renewal is. The line above says how")
    print("  many such payments the residual is the size of. It is not a renewal count and")
    print("  no committed source gives one. See A-19.")

    print()
    return 0


def _series(raw_dir: Path) -> int:
    exercises, _, columns = load_bidding(raw_dir)
    target = load_target(raw_dir)

    print("\nmillions of dollars, quota times premium, all five categories")
    print(f"{'FY':<8}{'computed':>12}{'published':>12}{'residual':>12}{'computed/pub':>14}")
    print("-" * 58)
    for fy in covered_fiscal_years(columns):
        if fy not in target.values:
            continue
        computed = sum(e.revenue("quota") for e in exercises if e.fiscal_year == fy) / 1e6
        published = target.values[fy]
        flag = "" if fy <= target.latest_actual_fy else "  estimate, not an actual"
        print(f"FY{fy:<6}{computed:>12,.1f}{published:>12,.1f}"
              f"{published - computed:>12,.1f}{computed / published:>13.0%}{flag}")
    print()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fy", type=int, default=None,
                        help="financial year to reconcile, default the latest with actuals")
    parser.add_argument("--series", action="store_true",
                        help="print every covered financial year instead")
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    args = parser.parse_args(argv)

    try:
        if args.series:
            return _series(args.raw)
        fy = args.fy if args.fy is not None else load_target(args.raw).latest_actual_fy
        return _report(fy, args.raw)
    except ReconciliationError as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

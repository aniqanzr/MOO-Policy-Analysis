"""Published data turned into model inputs: Annex A tables as quota inputs, and the reference
quarter the stage 5 placeholder model is anchored to.

Nothing here is estimated. Every number comes from a committed file: the Annex A tables under
`data/raw/lta-annex-a/` via `src/ingest/extract_annex_a.py`, and the bidding record in
`data/raw/quota-premium-monthly.csv`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.ingest import extract_annex_a as annex
from src.model.quota import CATEGORIES, QuotaInputs

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
WIDE_FILE = RAW_DIR / "quota-premium-monthly.csv"

WIDE_PREFIX = {
    "A": "Cars Up To 1600cc And 97kW",
    "B": "Cars Above 1600cc Or 97kW",
    "C": "Goods Vehicles & Buses",
    "D": "Motorcycles",
    "E": "Open Category",
}
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MISSING = {"", "-", "na", "n.a.", "s"}

# The policy in force for every Annex A table on file: zero growth for A, B and D from
# February 2018, 0.25 percent for C. Stated in the footnotes of every table.
CURRENT_G_AB = 0.0
CURRENT_G_C = 0.0025


@lru_cache(maxsize=1)
def annex_tables():
    """Annex A tables with formula lines, in date order."""
    releases, _, _ = annex.extract()
    return tuple(r for r in releases if not r["revision"] and "A1)" in r["lines"])


def final_total_line(release):
    lines = release["lines"]
    if "(D)" in lines:
        return lines["(D)"]
    return lines[f"Total Quota for {release['period']}"]


def inputs_from_annex(release) -> tuple[QuotaInputs, dict]:
    """Quota inputs from one Annex A table, and the published lines to check against.

    Adjustments are taken as whatever the published final total holds beyond the growth (A)
    and replacement (B) subtotals. They do not respond to the levers, so reading them off the
    table is not circular: the formula's own work is lines (A) and (B), and those are compared.
    """
    lines = release["lines"]
    b1, window = annex.deregistration_line(release)
    _, guaranteed = annex.guaranteed_line(release)
    final = final_total_line(release)["values"]

    published_growth = lines["(A)"]["values"]
    published_replacement = lines["(B)"]["values"]
    adjustments = {
        c: final[c] - published_growth[c] - published_replacement[c] for c in CATEGORIES
    }
    inputs = QuotaInputs(
        population={c: lines["A1)"]["values"][c] for c in CATEGORIES},
        deregistrations={c: b1["values"][c] for c in CATEGORIES},
        window_months=annex.months_between(window),
        guaranteed={c: abs(guaranteed["values"][c]) for c in CATEGORIES} if guaranteed else {},
        adjustments=adjustments,
    )
    published = {
        "growth": published_growth,
        "replacement_net_of_e": published_replacement,
        "total": final,
    }
    return inputs, published


def redistribution_line(release):
    """The redistribution and injection line of one table, by category, or None.

    Annex A prints guaranteed-deregistration redistribution and discretionary injection on one
    line from February 2025, and redistribution alone on the same line from August 2023. It is
    the one adjustment policy sets directly rather than computes.
    """
    for code, line in release["lines"].items():
        label = line["label"].lower()
        if code.startswith("C") and "redistribution" in label and "suspended" not in label:
            return dict(line["values"])
    return None


def injection_history():
    """(quota period, redistribution and injection by category) for every table that has one."""
    history = []
    for release in annex_tables():
        values = redistribution_line(release)
        if values is not None:
            history.append((release["period"], values))
    return history


@dataclass(frozen=True)
class ReferenceQuarter:
    """The quarter the placeholder model is anchored to.

    period           the Annex A quota period
    inputs           its quota inputs
    quota            published quarterly quota by category, the final total line
    premium          quota-weighted mean clearing premium by category over the quarter's
                     six exercises, from the bidding record
    bids_received    bids received by category over the same exercises
    """

    period: str
    inputs: QuotaInputs
    quota: dict[str, int]
    premium: dict[str, float]
    bids_received: dict[str, int]
    injection: dict[str, int]

    @property
    def theta(self) -> float:
        """Category A share of car demand, proxied by its share of A and B bids received.

        A proxy. Bids received count bids, not buyers, and a buyer can bid more than once.
        It anchors the placeholder demand split at an observed value rather than a chosen one.
        """
        a, b = self.bids_received["A"], self.bids_received["B"]
        return a / (a + b)


def _wide():
    rows = list(csv.reader(WIDE_FILE.open(newline="", encoding="utf-8")))
    return rows[0], {row[0].strip(): row for row in rows[1:]}


def _cell(header, series, name, column):
    row = series.get(name)
    if row is None or column not in header:
        return None
    text = row[header.index(column)].strip().replace(",", "")
    return None if text.lower() in MISSING else float(text)


def quarter_columns(period):
    """`May 2026 to Jul 2026` to the three wide-table columns it covers."""
    start, end = period.split(" to ")
    m0, y0 = start.split()
    m1, y1 = end.split()
    y, m = int(y0), MONTHS.index(m0) + 1
    last = (int(y1), MONTHS.index(m1) + 1)
    columns = []
    while (y, m) <= last:
        columns.append(f"{y}{MONTHS[m - 1]}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return columns


def reference_quarter(period=None) -> ReferenceQuarter:
    """The latest Annex A quarter whose six exercises all appear in the bidding record."""
    header, series = _wide()
    tables = annex_tables()

    def complete(release):
        columns = quarter_columns(release["period"])
        return all(
            _cell(header, series, f"{WIDE_PREFIX[c]}, Quota Premium, {b} Bidding", col)
            is not None
            for c in CATEGORIES for b in ("1st", "2nd") for col in columns
        )

    candidates = [t for t in tables if (period is None or t["period"] == period)]
    release = next(t for t in reversed(candidates) if complete(t))
    inputs, published = inputs_from_annex(release)

    premium, bids = {}, {}
    for c in CATEGORIES:
        weighted = quota = received = 0.0
        for column in quarter_columns(release["period"]):
            for bidding in ("1st", "2nd"):
                q = _cell(header, series, f"{WIDE_PREFIX[c]}, Quota, {bidding} Bidding", column)
                p = _cell(header, series,
                          f"{WIDE_PREFIX[c]}, Quota Premium, {bidding} Bidding", column)
                r = _cell(header, series,
                          f"{WIDE_PREFIX[c]}, Bids Received, {bidding} Bidding", column)
                weighted += q * p
                quota += q
                received += r
        premium[c] = weighted / quota
        bids[c] = int(received)

    injection = redistribution_line(release) or {}
    return ReferenceQuarter(
        period=release["period"],
        inputs=inputs,
        quota={c: published["total"][c] for c in CATEGORIES},
        premium=premium,
        bids_received=bids,
        injection={c: injection.get(c, 0) for c in CATEGORIES},
    )

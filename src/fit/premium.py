"""Premium elasticity by category: the specification declared in the decision log on 2026-09-24.

Run it:

    python -m src.fit.premium                  # Categories A and B
    python -m src.fit.premium --categories C

Section 4.1's form, ln P = a + b ln Q, one row per bidding exercise, clearing premium and exercise
quota from `quota-premium-monthly`. The grid below was fixed and committed before any estimate
was looked at, and every cell of it is reported. This module does not choose among them.

Windows, all ending at the last exercise on file:
    W1  from May 2022, the current Category A definition. Primary.
    W2  from February 2023, the four-quarter formula.
    W3  from February 2014, the 97 kW criterion.

Specifications:
    S1  ln P on ln Q, no controls. Primary.
    S2  adding a linear trend in exercise order.
    S3  first differences between consecutive exercises in the window.

Newey-West standard errors with 6 lags, one quarter of exercises.

A weakness that is structural, not a choice: quota is set once a quarter, so a window of about
100 exercises has only about 17 distinct quota levels per category. The count is reported with
every estimate.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import statsmodels.api as sm

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "quota-premium-monthly.csv"

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

WINDOWS = {
    "W1": (2022, 5),
    "W2": (2023, 2),
    "W3": (2014, 2),
}
SPECIFICATIONS = ("S1", "S2", "S3")
PRIMARY = ("W1", "S1")
HAC_LAGS = 6


@dataclass(frozen=True)
class Estimate:
    category: str
    window: str
    specification: str
    b: float
    se: float
    low: float
    high: float
    n: int
    quota_levels: int
    r2: float

    @property
    def side(self) -> str:
        """Which side of -1 the whole 95 percent interval sits on, if either."""
        if self.high < -1:
            return "stronger than -1"
        if self.low > -1:
            return "weaker than -1"
        return "straddles -1"


def exercises(category, raw=RAW):
    """(year, month, bidding, quota, premium) for every exercise with both published, in order."""
    rows = list(csv.reader(raw.open(newline="", encoding="utf-8")))
    header, series = rows[0], {row[0].strip(): row for row in rows[1:]}
    prefix = WIDE_PREFIX[category]
    out = []
    for column in header[1:]:
        year, month = int(column[:4]), MONTHS.index(column[4:]) + 1
        index = header.index(column)
        for number, bidding in ((1, "1st"), (2, "2nd")):
            q = series[f"{prefix}, Quota, {bidding} Bidding"][index].strip().replace(",", "")
            p = series[f"{prefix}, Quota Premium, {bidding} Bidding"][index].strip().replace(",", "")
            if q.lower() in MISSING or p.lower() in MISSING:
                continue
            out.append((year, month, number, float(q), float(p)))
    out.sort()
    return out


def fit(category, window, specification, raw=RAW) -> Estimate:
    start = WINDOWS[window]
    data = [row for row in exercises(category, raw) if (row[0], row[1]) >= start]
    q = np.log([row[3] for row in data])
    p = np.log([row[4] for row in data])

    if specification == "S1":
        X = sm.add_constant(q)
        y = p
    elif specification == "S2":
        X = sm.add_constant(np.column_stack([q, np.arange(len(q), dtype=float)]))
        y = p
    elif specification == "S3":
        X = sm.add_constant(np.diff(q))
        y = np.diff(p)
    else:
        raise ValueError(f"specification must be one of {SPECIFICATIONS}")

    result = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    b, se = float(result.params[1]), float(result.bse[1])
    low, high = (float(v) for v in result.conf_int()[1])
    return Estimate(
        category=category, window=window, specification=specification,
        b=b, se=se, low=low, high=high, n=int(result.nobs),
        quota_levels=len({row[3] for row in data}), r2=float(result.rsquared),
    )


def grid(categories):
    return [fit(c, w, s) for c in categories for w in WINDOWS for s in SPECIFICATIONS]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--categories", default="AB")
    args = parser.parse_args(argv)

    estimates = grid(list(args.categories))
    print(f"\n{'cat':<5}{'window':<8}{'spec':<6}{'b':>8}{'se':>8}{'95% interval':>20}"
          f"{'n':>6}{'quota levels':>14}{'R2':>7}   side of -1")
    for e in estimates:
        mark = "  primary" if (e.window, e.specification) == PRIMARY else ""
        print(f"{e.category:<5}{e.window:<8}{e.specification:<6}{e.b:>8.3f}{e.se:>8.3f}"
              f"{f'[{e.low:.3f}, {e.high:.3f}]':>20}{e.n:>6}{e.quota_levels:>14}{e.r2:>7.3f}"
              f"   {e.side}{mark}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

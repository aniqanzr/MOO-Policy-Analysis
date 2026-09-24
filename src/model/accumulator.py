"""Stage 7: the population accumulator and its backtest. Brief 4.2, A-04.

Run it:

    python -m src.model.accumulator

Declared in the decision log on 2026-09-24 before it ran. Three levels:

    L1  P(t) = P(t-1) + R(t) - D(t), published registrations and deregistrations. A data check.
    L2  P(t) = P(t-1) + Q(t) - D(t), Q the quota released. The brief's accumulator, and the gate.
    L3  stock against the previous 120 months of registrations. A-04 as worded. A diagnostic.

Error is measured over 60-month windows, the model's horizon: the accumulator's change in stock
minus the published change, as a share of the published stock at the window's start.
"""

from __future__ import annotations

import argparse
import csv
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CONFIG = ROOT / "config" / "backtest.toml"

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MISSING = {"", "-", "na", "n.a.", "s"}

# Row labels in the three SingStat VQS tables, stripped of leading spaces.
VQS_ROWS = {
    "A": "Category A: Cars",
    "B": "Category B: Cars",
    "C": "Category C: Goods Vehicles & Buses",
    "D": "Category D: Motorcycles & Scooters",
    "taxis": "Taxis",
    "exempted": "Vehicles Exempted From VQS",
}
TOTAL_ROWS = {
    "vqs-population-monthly.csv": "Total Motor Vehicles",
    "vqs-new-registrations-monthly.csv": "Total New Motor Vehicles Registered",
    "vqs-deregistrations-monthly.csv": "Total Motor Vehicles De-Registered",
}
QUOTA_PREFIX = {
    "A": "Cars Up To 1600cc And 97kW",
    "B": "Cars Above 1600cc Or 97kW",
    "C": "Goods Vehicles & Buses",
    "D": "Motorcycles",
    "E": "Open Category",
}

# No bidding exercise was held in these months, so no quota was released in them. LTA, "Resumption
# of COE bidding exercises from 6 July" (June 2020), in data/raw/lta-annex-a: "suspended bidding
# exercises from April to June will be returned to the market over the next 12 months from July
# 2020 to June 2021." The table leaves them blank. Read as zero, not missing: a blank here is an
# exercise that did not happen, not a figure that was not published.
SUSPENDED = pd.PeriodIndex(["2020-04", "2020-05", "2020-06"], freq="M")

# L2 groupings. E registers cars and goods vehicles, never motorcycles, so its quota goes with
# A, B and C. Taxis and exempted vehicles are outside both sides.
GROUPS = {
    "A+B+C with E": (("A", "B", "C"), ("A", "B", "C", "E")),
    "D": (("D",), ("D",)),
    "A to D with E": (("A", "B", "C", "D"), ("A", "B", "C", "D", "E")),
}


def settings(path=CONFIG):
    with path.open("rb") as f:
        return tomllib.load(f)


def _period(column):
    return pd.Period(year=int(column[:4]), month=MONTHS.index(column[4:7]) + 1, freq="M")


def vqs_table(name):
    """One SingStat VQS table as a DataFrame, monthly index, one column per VQS_ROWS key plus
    'total'. Missing cells are NaN."""
    rows = list(csv.reader((RAW / name).open(newline="", encoding="utf-8")))
    header = rows[0]
    by_label = {row[0].strip(): row for row in rows[1:]}
    labels = dict(VQS_ROWS, total=TOTAL_ROWS[name])
    index = [_period(c) for c in header[1:]]
    data = {}
    for key, label in labels.items():
        row = by_label[label]
        data[key] = [
            np.nan if v.strip().lower() in MISSING else float(v.replace(",", ""))
            for v in row[1:]
        ]
    return pd.DataFrame(data, index=pd.PeriodIndex(index, freq="M")).sort_index()


def population():
    return vqs_table("vqs-population-monthly.csv")


def registrations():
    return vqs_table("vqs-new-registrations-monthly.csv")


def deregistrations():
    return vqs_table("vqs-deregistrations-monthly.csv")


def quota(measure="Quota"):
    """Monthly quota by category, first and second bidding summed. `measure` is 'Quota' for quota
    released or 'Successful Bids'. The three suspended months are zero. Any other month with
    neither exercise published is NaN; a month with only one is that one."""
    rows = list(csv.reader((RAW / "quota-premium-monthly.csv").open(newline="", encoding="utf-8")))
    header = rows[0]
    series = {row[0].strip(): row for row in rows[1:]}
    index = pd.PeriodIndex([_period(c) for c in header[1:]], freq="M")
    data = {}
    for category, prefix in QUOTA_PREFIX.items():
        parts = []
        for bidding in ("1st", "2nd"):
            row = series[f"{prefix}, {measure}, {bidding} Bidding"]
            parts.append([
                np.nan if v.strip().lower() in MISSING else float(v.replace(",", ""))
                for v in row[1:]
            ])
        a, b = np.array(parts[0]), np.array(parts[1])
        both_missing = np.isnan(a) & np.isnan(b)
        total = np.nansum(np.vstack([a, b]), axis=0)
        total[both_missing] = np.nan
        data[category] = total
    frame = monthly(pd.DataFrame(data, index=index).sort_index())
    frame.loc[frame.index.isin(SUSPENDED)] = 0.0
    return frame


def monthly(obj):
    """Reindex to every month between the first and last, so a gap shows as NaN."""
    return obj.reindex(pd.period_range(obj.index.min(), obj.index.max(), freq="M"))


def accumulate(start_stock, inflow, outflow):
    """Run P(t) = P(t-1) + inflow(t) - outflow(t) forward from the stock at the month before
    the first flow. Returns the modelled stock, same index as the flows."""
    return start_stock + (inflow - outflow).cumsum()


@dataclass(frozen=True)
class WindowErrors:
    """Error in the change of stock over every window of `months` months, as a share of the
    published stock at the window's start."""
    label: str
    errors: pd.Series  # indexed by window start

    @property
    def median(self):
        return float(self.errors.abs().median())

    @property
    def max(self):
        return float(self.errors.abs().max())

    @property
    def worst(self):
        start = self.errors.abs().idxmax()
        return start, float(self.errors[start])

    def passes(self, tolerance):
        return self.max <= tolerance


def window_errors(label, published, inflow, outflow, months):
    """Compare modelled and published stock change over rolling windows.

    Window starting at month s runs from the stock at end of s-1 to the stock at end of s+months-1,
    so its flows are months s to s+months-1.
    """
    frame = pd.DataFrame({"p": published, "i": inflow, "o": outflow}).dropna()
    # Require a contiguous monthly run so a gap cannot be silently bridged.
    frame = monthly(frame)
    net = frame["i"] - frame["o"]
    starts, errors = [], []
    for k in range(1, len(frame) - months + 1):
        before = frame["p"].iloc[k - 1]
        after = frame["p"].iloc[k + months - 1]
        flows = net.iloc[k:k + months]
        if np.isnan(before) or np.isnan(after) or flows.isna().any():
            continue
        modelled = flows.sum()
        errors.append((modelled - (after - before)) / before)
        starts.append(frame.index[k])
    return WindowErrors(label, pd.Series(errors, index=pd.PeriodIndex(starts, freq="M")))


def level1(months):
    """Published registrations and deregistrations against the published stock."""
    P, R, D = population(), registrations(), deregistrations()
    out = []
    for key in list(VQS_ROWS) + ["total"]:
        out.append(window_errors(key, P[key], R[key], D[key], months))
    return out


def level2(months, measure="Quota"):
    """The brief's accumulator: quota released in, published deregistrations out."""
    P, D, Q = population(), deregistrations(), quota(measure)
    out = []
    for label, (stock, inflow) in GROUPS.items():
        published = P[list(stock)].sum(axis=1, min_count=len(stock))
        q = Q[list(inflow)].sum(axis=1, min_count=len(inflow))
        d = D[list(stock)].sum(axis=1, min_count=len(stock))
        out.append(window_errors(label, published, q, d, months))
    return out


def level3(horizon=120):
    """Stock against the sum of the previous `horizon` months of registrations, A to D."""
    P, R = population(), registrations()
    keys = ["A", "B", "C", "D"]
    stock = P[keys].sum(axis=1, min_count=4)
    regs = monthly(R[keys].sum(axis=1, min_count=4))
    rolling = regs.rolling(horizon, min_periods=horizon).sum()
    frame = pd.DataFrame({"stock": stock, "decade": rolling}).dropna()
    frame["ratio"] = frame["stock"] / frame["decade"]
    return frame


def residual_months(key, top=8):
    """L1 monthly residuals: published change minus registrations plus deregistrations."""
    P, R, D = population(), registrations(), deregistrations()
    frame = monthly(pd.DataFrame({"p": P[key], "r": R[key], "d": D[key]}).dropna())
    resid = frame["p"].diff() - (frame["r"] - frame["d"])
    return resid.dropna(), resid.abs().sort_values(ascending=False).head(top)


def _report(title, results, tolerance=None):
    print(f"\n{title}")
    print(f"{'series':<16}{'windows':>8}{'span':>22}{'median |err|':>14}{'max |err|':>11}"
          f"{'worst window':>14}{'err there':>11}" + ("   gate" if tolerance else ""))
    for r in results:
        if r.errors.empty:
            print(f"{r.label:<16}   no complete window")
            continue
        start, err = r.worst
        span = f"{r.errors.index[0]} to {r.errors.index[-1]}"
        gate = ("   pass" if r.passes(tolerance) else "   fail") if tolerance else ""
        print(f"{r.label:<16}{len(r.errors):>8}{span:>22}{r.median:>14.2%}{r.max:>11.2%}"
              f"{str(start):>14}{err:>11.2%}{gate}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    cfg = settings()
    months, tolerance = cfg["window_months"], cfg["tolerance"]

    _report(f"L1, published flows against published stock, {months}-month windows", level1(months))
    _report(f"L2, quota released, {months}-month windows, tolerance {tolerance:.2%}",
            level2(months, "Quota"), tolerance)
    _report(f"L2 variant, successful bids, {months}-month windows",
            level2(months, "Successful Bids"))

    l3 = level3()
    print("\nL3, stock A to D over the previous 120 months of registrations")
    for year in sorted({p.year for p in l3.index}):
        rows = l3[[p.year == year and p.month == 12 for p in l3.index]]
        if not rows.empty:
            r = rows.iloc[0]
            print(f"  Dec {year}  stock {r['stock']:>9,.0f}  decade {r['decade']:>9,.0f}"
                  f"  ratio {r['ratio']:.3f}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

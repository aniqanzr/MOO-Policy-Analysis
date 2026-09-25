"""Stage 9: BPR calibrated against annual peak-hour speeds and lane-km. Brief 4.3, A-09.

Run it:

    python -m src.fit.congestion

Declared in the decision log on 2026-09-25 before it ran.

BPR in travel-time form: pace = p0 (1 + a x^beta), pace = 1 / speed, x = PCU-weighted vehicle
stock per lane-km. With no published traffic volume, BPR's alpha and the scale from stock to
volume enter only as a = alpha k^beta, so the fit identifies p0, a and beta. O2 = 1 + a x^beta
needs exactly those.

For fixed beta the model is linear, pace = c0 + c1 x^beta, so beta is profiled on a grid and each
point is OLS. The F quantile comes from scipy, which statsmodels already requires.
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
from scipy import stats

from src.model import accumulator as acc

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CONFIG = ROOT / "config" / "congestion.toml"

ROAD_CLASS = {
    "expressway": ("ave_speed_expressway", "Expressways"),
    "arterial": ("ave_speed_arterial_roads", "Arterial Roads"),
}
CONVENTIONAL_BETA = 4.0  # US Bureau of Public Roads, Traffic Assignment Manual, 1964


def settings(path=CONFIG):
    with path.open("rb") as f:
        return tomllib.load(f)


def speeds():
    frame = pd.read_csv(RAW / "peak-hour-speed-annual.csv").set_index("year")
    return frame


def lane_km():
    rows = list(csv.reader((RAW / "public-roads-annual.csv").open(newline="", encoding="utf-8")))
    header = [int(y) for y in rows[0][1:]]
    data = {row[0].strip(): [float(v) for v in row[1:]] for row in rows[1:]}
    return pd.DataFrame(data, index=header).sort_index()


def weighted_stock(pcu):
    """Annual mean of the monthly VQS stock, PCU-weighted. Years with all twelve months only."""
    P = acc.population()
    monthly = sum(pcu[key] * P[key] for key in pcu)
    frame = pd.DataFrame({"stock": monthly, "year": [p.year for p in monthly.index]})
    grouped = frame.groupby("year")["stock"]
    counts = grouped.count()
    return grouped.mean()[counts == 12]


@dataclass(frozen=True)
class Fit:
    road: str
    variant: str
    years: tuple
    x: np.ndarray
    speed: np.ndarray
    grid: np.ndarray
    ssr: np.ndarray
    c0: np.ndarray
    c1: np.ndarray
    interval_mask: np.ndarray

    @property
    def n(self):
        return len(self.x)

    @property
    def best(self):
        return int(np.argmin(self.ssr))

    @property
    def beta(self):
        return float(self.grid[self.best])

    @property
    def interval(self):
        inside = self.grid[self.interval_mask]
        return float(inside.min()), float(inside.max())

    @property
    def bounded(self):
        low, high = self.interval
        return low > self.grid[0] and high < self.grid[-1]

    @property
    def rising(self):
        """Pace rises with load at the best fit."""
        return bool(self.c1[self.best] > 0)

    @property
    def identified(self):
        return self.rising and self.bounded

    @property
    def physical(self):
        """Free-flow pace positive at the best fit. Not part of the declared rule; reported."""
        return bool(self.c0[self.best] > 0)

    @property
    def conventional_inside(self):
        low, high = self.interval
        return low <= CONVENTIONAL_BETA <= high

    def params(self, i=None):
        i = self.best if i is None else i
        c0, c1 = self.c0[i], self.c1[i]
        return {"beta": float(self.grid[i]), "p0": float(c0), "a": float(c1 / c0)}

    @property
    def free_flow_speed(self):
        return 1.0 / self.c0[self.best]

    def o2(self, x, i=None):
        p = self.params(i)
        return 1.0 + p["a"] * np.asarray(x, dtype=float) ** p["beta"]

    def slope(self, x, i=None):
        """dO2/dx."""
        p = self.params(i)
        return p["a"] * p["beta"] * np.asarray(x, dtype=float) ** (p["beta"] - 1.0)

    @property
    def rmse_kmh(self):
        i = self.best
        fitted = 1.0 / (self.c0[i] + self.c1[i] * self.x ** self.grid[i])
        return float(np.sqrt(np.mean((fitted - self.speed) ** 2)))


def profile(road, variant, x, speed, years, cfg):
    f = cfg["fit"]
    grid = np.geomspace(f["beta_min"], f["beta_max"], f["beta_points"])
    pace = 1.0 / speed
    # Scale x to its mean so x^beta stays well conditioned across the grid; a is converted back.
    scale = x.mean()
    z = x / scale
    ssr, c0, c1 = [], [], []
    for beta in grid:
        X = np.column_stack([np.ones_like(z), z ** beta])
        coef, *_ = np.linalg.lstsq(X, pace, rcond=None)
        resid = pace - X @ coef
        ssr.append(float(resid @ resid))
        c0.append(coef[0])
        c1.append(coef[1] / scale ** beta)
    ssr = np.array(ssr)
    n = len(x)
    threshold = stats.f.ppf(f["confidence"], 1, n - 3)
    mask = (ssr - ssr.min()) / (ssr.min() / (n - 3)) <= threshold
    return Fit(road, variant, tuple(years), x, speed, grid, ssr, np.array(c0), np.array(c1), mask)


def data(road, cfg, exclude_pandemic=False, hold_capacity=False):
    speed_col, lane_row = ROAD_CLASS[road]
    s = speeds()[speed_col]
    lanes = lane_km()[lane_row].copy()
    if hold_capacity:
        year = cfg["fit"]["hold_capacity_from"]
        lanes[lanes.index > year] = lanes[year]
    stock = weighted_stock(cfg["pcu"])
    frame = pd.DataFrame({"speed": s, "lanes": lanes, "stock": stock}).dropna()
    if exclude_pandemic:
        frame = frame.drop(index=[y for y in cfg["fit"]["pandemic_years"] if y in frame.index])
    frame["x"] = frame["stock"] / frame["lanes"]
    return frame


VARIANTS = {
    "expressway": [
        ("all years, published capacity", False, False),
        ("no 2020-21, published capacity", True, False),
        ("all years, capacity held at 2023", False, True),
        ("no 2020-21, capacity held at 2023", True, True),
    ],
    "arterial": [
        ("all years", False, False),
        ("no 2020-21", True, False),
    ],
}
PRIMARY = {"expressway": "all years, published capacity", "arterial": "all years"}


def fits(cfg=None):
    cfg = cfg or settings()
    out = []
    for road, variants in VARIANTS.items():
        for label, pandemic, hold in variants:
            frame = data(road, cfg, pandemic, hold)
            out.append(profile(road, label, frame["x"].to_numpy(), frame["speed"].to_numpy(),
                               frame.index.tolist(), cfg))
    return out


def f06_comparison(fit, offset):
    """Range of dO2/dx at the latest x across the beta interval, against the range from offsetting
    x by plus and minus `offset` at the best beta. Both as ratios to the best-fit slope."""
    x_now = fit.x[-1]
    base = fit.slope(x_now)
    idx = np.flatnonzero(fit.interval_mask)
    beta_range = [float(fit.slope(x_now, i) / base) for i in idx]
    offset_range = [float(fit.slope(x_now * (1 + s * offset)) / base) for s in (-1, 1)]
    return (min(beta_range), max(beta_range)), (min(offset_range), max(offset_range))


def offset_slope_factor(beta, offset):
    """dO2/dx = a beta x^(beta - 1): offsetting x by a share scales it by (1 +/- offset)^(beta - 1)."""
    return (1 - offset) ** (beta - 1), (1 + offset) ** (beta - 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)
    cfg = settings()
    results = fits(cfg)
    print(f"\n{'road':<11}{'variant':<36}{'n':>3}{'beta':>7}{'95% profile':>16}{'c1>0':>6}"
          f"{'bounded':>9}{'4 inside':>9}{'free flow':>10}{'O2 last':>8}{'RMSE':>6}")
    for r in results:
        low, high = r.interval
        mark = "  primary" if PRIMARY[r.road] == r.variant else ""
        print(f"{r.road:<11}{r.variant:<36}{r.n:>3}{r.beta:>7.2f}{f'[{low:.2f}, {high:.2f}]':>16}"
              f"{'yes' if r.rising else 'no':>6}{'yes' if r.bounded else 'no':>9}"
              f"{'yes' if r.conventional_inside else 'no':>9}{r.free_flow_speed:>10.1f}"
              f"{float(r.o2(r.x[-1])):>8.3f}{r.rmse_kmh:>6.2f}{mark}")
    offset = cfg["f06"]["road_load_offset"]
    print("\nF-06 comparison, dO2/dx at the latest year as a ratio to the best-fit slope")
    for r in results:
        if not r.identified:
            print(f"  {r.road:<11}{r.variant:<36}beta not identified; no fitted range to compare")
            continue
        b, o = f06_comparison(r, offset)
        print(f"  {r.road:<11}{r.variant:<36}beta interval [{b[0]:.3g}, {b[1]:.3g}]"
              f"   offset +/-{offset:.2%} [{o[0]:.3g}, {o[1]:.3g}]")
    low, high = offset_slope_factor(CONVENTIONAL_BETA, offset)
    print(f"\nAt the conventional beta of 4, the +/-{offset:.2%} offset moves dO2/dx by a factor"
          f" of {low:.3f} to {high:.3f}.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

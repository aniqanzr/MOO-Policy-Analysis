"""Stage 5 only. The three objectives with placeholder coefficients, for the collinearity check.

Not the model. Stage 10 builds the objectives on fitted values. This exists to answer A-08
before any fitting is done: do the three levers move the objectives in genuinely different
directions, or do they all collapse onto total quota. Placeholder values are enough to see
that, and every one of them is in `config/placeholders.toml`, marked as an assumption, and
swept.

The model, per quarter, anchored at the reference quarter (the latest Annex A quarter with
all six exercises in the bidding record):

    quota_i     reference quota + the change the levers make through the quota formula
    premium_i   reference premium x (quota_i / reference quota_i) ^ b_i, section 4.1's
                log-log form with its intercept set by the reference quarter
    O1          quota-weighted mean premium, minimised
    O2          BPR travel time index at the horizon, from road load, minimised
    O3          premium times quota summed, maximised, so -O3 is minimised

Two lever sets. The gate is decided on the first.

    injection   g_ab, g_c, and the quarterly redistribution and injection line. Section 3.1's
                fallback for theta, which applies because no published data gives car demand
                by power output. Allocated across categories in the shares Annex A has used.
    theta       g_ab, g_c, and theta, the Category A share of car demand. Run for comparison
                only. With no power output data, theta cannot be tied to a threshold, so it is
                an abstract demand split here, anchored at the observed share of bids received.

Only the growth allowance and the injection line respond to the levers. Replacement,
the Category E contribution and every other adjustment are the same at every policy, so the
lever-dependent part is vectorised here and checked against `src/model/quota.py` in the tests.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from src.model.quota import CATEGORIES, growth_rates
from src.model.reference import (
    CURRENT_G_AB,
    CURRENT_G_C,
    ReferenceQuarter,
    injection_history,
)

CONFIG = Path(__file__).resolve().parents[2] / "config" / "placeholders.toml"
ROAD_CATEGORIES = ("A", "B", "C", "D")   # E has no vehicles of its own
LEVER_SETS = {
    "injection": ("g_ab", "g_c", "injection"),
    "theta": ("g_ab", "g_c", "theta"),
}
OBJECTIVES = ("O1 ownership cost", "O2 congestion", "O3 revenue (negated)")


def load_config(path=CONFIG):
    with open(path, "rb") as handle:
        return tomllib.load(handle)


@dataclass(frozen=True)
class Placeholders:
    """One setting of every assumed value. Built from the config defaults, then varied."""

    elasticity: dict[str, float]
    pcu: dict[str, float]
    alpha: float
    beta: float
    base_vc: float
    years: float
    categories: tuple[str, ...]
    growth_upper: float
    theta_half_width: float

    @classmethod
    def defaults(cls, config=None):
        config = config or load_config()
        b = config["premium"]["elasticity_default"]
        load = config["road_load"]
        return cls(
            elasticity={c: b for c in CATEGORIES},
            pcu={
                "A": load["car"],
                "B": load["car"],
                "C": load["goods_vehicle_and_bus_default"],
                "D": load["motorcycle"],
            },
            alpha=config["bpr"]["alpha"],
            beta=config["bpr"]["beta"],
            base_vc=config["bpr"]["base_vc"],
            years=config["horizon"]["years"],
            categories=tuple(config["objectives"]["categories_default"]),
            growth_upper=config["bounds"]["g_ab"][1],
            theta_half_width=config["bounds"]["theta_half_width"],
        )


def injection_allocation(period=None):
    """Shares of the redistribution and injection line by category, as Annex A has used them.

    With no period, pools every table that has the line. With a period, that quarter alone.
    The allocation is LTA's, read off the tables, not assumed.
    """
    history = injection_history()
    rows = history if period is None else [row for row in history if row[0] == period]
    if not rows:
        raise ValueError(f"no redistribution and injection line for {period}")
    totals = {c: sum(values[c] for _, values in rows) for c in CATEGORIES}
    grand = sum(totals.values())
    return {c: totals[c] / grand for c in CATEGORIES}


def injection_range():
    """0 to the largest quarterly redistribution and injection total Annex A has printed."""
    return 0.0, float(max(values["Total"] for _, values in injection_history()))


@dataclass
class PlaceholderModel:
    reference: ReferenceQuarter
    lever_set: str
    placeholders: Placeholders
    allocation: dict[str, float] = field(default_factory=injection_allocation)

    def __post_init__(self):
        if self.lever_set not in LEVER_SETS:
            raise ValueError(f"lever set must be one of {tuple(LEVER_SETS)}")
        self.population = {
            c: self.reference.inputs.population.get(c, 0) for c in CATEGORIES
        }
        self.reference_growth = growth_rates(CURRENT_G_AB, CURRENT_G_C)
        self.theta0 = self.reference.theta

    # ----- decision space -----

    def bounds(self):
        upper = self.placeholders.growth_upper
        third = {
            "injection": injection_range(),
            "theta": (self.theta0 - self.placeholders.theta_half_width,
                      self.theta0 + self.placeholders.theta_half_width),
        }[self.lever_set]
        return np.array([[0.0, upper], [0.0, upper], list(third)])

    def reference_point(self):
        third = {
            "injection": float(sum(self.reference.injection[c] for c in CATEGORIES)),
            "theta": self.theta0,
        }[self.lever_set]
        return np.array([CURRENT_G_AB, CURRENT_G_C, third])

    # ----- the model -----

    def growth_allowance(self, g_ab, g_c):
        """Quarterly growth allowance by category, floored, as the formula computes it."""
        g_ab = np.asarray(g_ab, dtype=float)
        rates = {"A": g_ab, "B": g_ab, "C": np.asarray(g_c, dtype=float)}
        out = {}
        for c in CATEGORIES:
            rate = rates.get(c, np.zeros_like(g_ab))
            out[c] = np.floor(rate * self.population[c] / 4)
        return out

    def injection_change(self, injection):
        """Change in each category's quota from moving the injection line off the reference.

        The allocation shapes where extra injection goes. Measured from the reference total
        under the same allocation, so the reference point reproduces the reference quarter
        exactly whichever allocation is used.
        """
        reference_total = sum(self.reference.injection[c] for c in CATEGORIES)
        return {
            c: np.round(injection * self.allocation[c])
            - round(reference_total * self.allocation[c])
            for c in CATEGORIES
        }

    def quota(self, X):
        """Quarterly quota by category for each row of X."""
        X = np.atleast_2d(X)
        g_ab, g_c, third = X[:, 0], X[:, 1], X[:, 2]
        growth = self.growth_allowance(g_ab, g_c)
        ref_growth = self.growth_allowance(
            np.full_like(g_ab, CURRENT_G_AB), np.full_like(g_c, CURRENT_G_C)
        )
        quota = {}
        for c in CATEGORIES:
            quota[c] = self.reference.quota[c] + growth[c] - ref_growth[c]
        if self.lever_set == "injection":
            change = self.injection_change(third)
            for c in CATEGORIES:
                quota[c] = quota[c] + change[c]
        return quota

    def premium(self, X, quota):
        X = np.atleast_2d(X)
        b = self.placeholders.elasticity
        premium = {}
        for c in CATEGORIES:
            ratio = np.maximum(quota[c], 1.0) / self.reference.quota[c]
            premium[c] = self.reference.premium[c] * ratio ** b[c]
        if self.lever_set == "theta":
            theta = X[:, 2]
            premium["A"] = premium["A"] * (theta / self.theta0) ** (-b["A"])
            premium["B"] = premium["B"] * ((1 - theta) / (1 - self.theta0)) ** (-b["B"])
        return premium

    def road_load(self, X, quota):
        """PCU-weighted vehicle population at the horizon."""
        X = np.atleast_2d(X)
        years = self.placeholders.years
        rates = {"A": X[:, 0], "B": X[:, 0], "C": X[:, 1]}
        extra = self.injection_change(X[:, 2]) if self.lever_set == "injection" else None
        load = np.zeros(len(X))
        for c in ROAD_CATEGORIES:
            rate = rates.get(c, np.zeros(len(X)))
            ref_rate = self.reference_growth[c]
            change = self.population[c] * ((1 + rate) ** years - (1 + ref_rate) ** years)
            if extra is not None:
                # Injected COEs are additional vehicles, not replacements, four quarters a year.
                change = change + 4 * years * extra[c]
            load = load + self.placeholders.pcu[c] * (self.population[c] + change)
        return load

    def reference_load(self):
        return sum(self.placeholders.pcu[c] * self.population[c] for c in ROAD_CATEGORIES)

    def evaluate(self, X):
        """Objectives in minimisation form, one row per policy: O1, O2, -O3."""
        X = np.atleast_2d(X)
        quota = self.quota(X)
        premium = self.premium(X, quota)
        included = self.placeholders.categories

        revenue = sum(premium[c] * quota[c] for c in included)
        volume = sum(quota[c] for c in included)
        o1 = revenue / volume

        ph = self.placeholders
        vc = ph.base_vc * self.road_load(X, quota) / self.reference_load()
        o2 = 1 + ph.alpha * vc ** ph.beta

        return np.column_stack([o1, o2, -revenue])

    def total_quota(self, X):
        quota = self.quota(X)
        return sum(quota[c] for c in CATEGORIES)

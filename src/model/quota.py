"""The LTA quota formula, as Annex A publishes it.

Quota is computed, never chosen. Per category and quarter:

    total = growth allowance
          + replacement of deregistered vehicles, less the Category E contribution
          + adjustments

Growth allowance is the annual growth rate times the vehicle population, over four, floored.
The decision variables `g_ab` and `g_c` enter here and nowhere else.

Replacement is a quarter's worth of deregistrations net of guaranteed deregistrations. How
many months of deregistrations that quarter's worth is drawn from has changed twice, and the
share changes with it: one quarter at 100 percent until July 2022, two quarters at 50 percent
from August 2022, four quarters at 25 percent from February 2023. The 25 percent is arithmetic
converting a twelve-month count into one quarter. It is not a policy rate and is not a lever.

From May 2017, Category E receives 10 percent of the Category A, B and C replacement, floored,
and Category D contributes nothing to it.

Adjustments are the named lines in Annex A: taxi population change, the Early Turnover Scheme,
expired COEs and TCOEs, redistribution of guaranteed deregistrations, injections, and in 2020
the return of suspended quota. None responds to the levers, so they are taken as published.

Rounding, measured on the 27 Annex A tables with formula lines. Growth allowance is floored in
all 27. The Category E contribution is floored in all 81 cells. The replacement line is rounded
in no fixed direction, down in 28 cells and up in 25, and four cells match no rounding at all.
See A-22. Nearest rounding is used for it here, so this formula reproduces Annex A to within
about 1.25 COEs per category on that line and exactly everywhere else.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

CATEGORIES = ("A", "B", "C", "D", "E")

# Categories whose replacement contributes 10 percent to Category E, from May 2017.
FEEDS_E = ("A", "B", "C")
E_SHARE = 0.10

# Months of deregistrations per quarter of quota, by regime. One quarter's worth is always
# drawn, so the share is 3 over the window length.
QUARTER_MONTHS = 3


@dataclass(frozen=True)
class QuotaInputs:
    """What one quarter's quota is computed from.

    population         vehicles by category at the population date, Annex A line A1
    deregistrations    deregistrations by category over the window, line B1
    guaranteed         guaranteed deregistrations by category over the window, as a
                       non-negative count to net off, line B2 from August 2023, else zero
    window_months      3, 6 or 12, by regime
    adjustments        every other line by category, taken as published
    """

    population: dict[str, int]
    deregistrations: dict[str, int]
    window_months: int
    guaranteed: dict[str, int] = field(default_factory=dict)
    adjustments: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Quota:
    growth: dict[str, int]
    replacement: dict[str, int]
    contribution_to_e: dict[str, int]
    adjustments: dict[str, int]
    total: dict[str, int]

    @property
    def total_all(self) -> int:
        return sum(self.total.values())


def growth_rates(g_ab: float, g_c: float) -> dict[str, float]:
    """Annual growth rate by category. `g_ab` applies to A and B, `g_c` to C.

    Category D is not a decision dimension and sits at zero growth with A and B under the
    current policy. Category E has no vehicle population of its own, so no growth allowance.
    """
    return {"A": g_ab, "B": g_ab, "C": g_c, "D": 0.0, "E": 0.0}


def quarterly_quota(inputs: QuotaInputs, g_ab: float, g_c: float) -> Quota:
    """One quarter's quota by category, for given growth rates."""
    rates = growth_rates(g_ab, g_c)
    share = QUARTER_MONTHS / inputs.window_months

    growth = {
        c: math.floor(rates[c] * inputs.population.get(c, 0) / 4) for c in CATEGORIES
    }

    replacement = {}
    for c in CATEGORIES:
        net = inputs.deregistrations.get(c, 0) - inputs.guaranteed.get(c, 0)
        replacement[c] = round(share * net)

    contribution = {c: 0 for c in CATEGORIES}
    for c in FEEDS_E:
        contribution[c] = -math.floor(E_SHARE * replacement[c])
    contribution["E"] = -sum(contribution[c] for c in FEEDS_E)

    adjustments = {c: inputs.adjustments.get(c, 0) for c in CATEGORIES}
    total = {
        c: growth[c] + replacement[c] + contribution[c] + adjustments[c] for c in CATEGORIES
    }
    return Quota(growth, replacement, contribution, adjustments, total)

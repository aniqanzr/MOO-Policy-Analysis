"""Stage 5 of docs/BUILD_SEQUENCE.md. Is the front a surface or a curve. A-08.

Placeholder coefficients, from `config/placeholders.toml`. These tests pin what stage 5 found,
so a change to the model, the placeholders or the formula that moves the result shows up here.

The result in one line: under the lever set the plan requires, the front is a surface only on
one side of unit premium elasticity. With `theta` unmodellable, section 3.1 falls back to a
discretionary injection lever. Injection and `g_ab` both add car quota, so cost and revenue
can only pull apart if revenue falls as quota rises, which needs an elasticity stronger than
-1. Weaker than -1, more quota lowers the premium and raises revenue together, cost and
revenue stop conflicting, and the front is the curve of quota against congestion. That holds
when O1 and O3 count the decision categories A, B and C. Counting all five puts a second
dimension back, but only because injection puts about a quarter of its COEs into motorcycles,
whose low premium pulls the mean down by composition.

`theta`, run for comparison, gives a surface on both sides. It is the lever that would have
worked, and no published data ties it to a policy setting.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.model import reference as ref
from src.model.placeholder_objectives import CATEGORIES, PlaceholderModel, Placeholders
from src.optimise import collinearity as col

DECISION = ("A", "B", "C")
ALL = CATEGORIES

# Measured 2026-09-24, NSGA-II 200 generations, seed 0, goods vehicle load 2.0 PCU. Curves came
# out at 0.024 to 0.046 and surfaces at 0.15 upward, so 0.10 separates them with room.
CURVE_BELOW = 0.10
SURFACE_ABOVE = 0.15


@pytest.fixture(scope="module")
def reference():
    return ref.reference_quarter()


def front_ratio(reference, lever_set, b, categories):
    base = Placeholders.defaults()
    placeholders = replace(base, elasticity={c: b for c in CATEGORIES}, categories=categories)
    model = PlaceholderModel(reference, lever_set, placeholders)
    s2, _, _ = col.local_dimension(col.nsga_front(model, generations=200))
    return s2


def test_cost_times_quota_is_revenue(reference):
    """O1 x total quota = O3, by definition. Why cost and revenue can move together."""
    model = PlaceholderModel(reference, "injection", Placeholders.defaults())
    X = col.sample(model, n=64)
    F = model.evaluate(X)
    quota = model.quota(X)
    volume = sum(quota[c] for c in model.placeholders.categories)
    np.testing.assert_allclose(F[:, 0] * volume, -F[:, 2], rtol=1e-9)


def test_unit_elasticity_makes_revenue_flat(reference):
    """At b = -1 premium times quota is constant, so O3 cannot respond to the levers."""
    base = Placeholders.defaults()
    placeholders = replace(base, elasticity={c: -1.0 for c in CATEGORIES})
    model = PlaceholderModel(reference, "injection", placeholders)
    F = model.evaluate(col.sample(model, n=256))
    assert np.ptp(F[:, 2]) <= 1e-6 * abs(F[:, 2].mean())


@pytest.mark.parametrize("b", [-0.5, -0.8])
def test_injection_front_is_a_curve_when_revenue_rises_with_quota(reference, b):
    """The gate's failing side. Decision categories only, elasticity weaker than -1."""
    assert front_ratio(reference, "injection", b, DECISION) < CURVE_BELOW


@pytest.mark.parametrize("b", [-1.2, -2.0])
def test_injection_front_is_a_surface_when_revenue_falls_with_quota(reference, b):
    assert front_ratio(reference, "injection", b, DECISION) > SURFACE_ABOVE


def test_counting_motorcycles_turns_the_curve_back_into_a_surface(reference):
    """The composition effect. Same elasticity, all five categories in O1 and O3."""
    assert front_ratio(reference, "injection", -0.5, DECISION) < CURVE_BELOW
    assert front_ratio(reference, "injection", -0.5, ALL) > SURFACE_ABOVE


@pytest.mark.parametrize("b", [-0.5, -2.0])
def test_theta_would_give_a_surface_on_both_sides(reference, b):
    assert front_ratio(reference, "theta", b, DECISION) > SURFACE_ABOVE

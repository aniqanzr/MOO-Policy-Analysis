"""Stage 5. The quota formula against every Annex A table, and the placeholder model against the
formula.

The formula in `src/model/quota.py` is LTA's arithmetic as Annex A prints it. Given the inputs
a table prints, it has to give back the lines the table prints: growth allowance exactly, and
each category's total to within A-22's tolerance, because Annex A's own replacement line does
not always round the same way.

The stage 5 placeholder model does not call the formula point by point. Only the growth
allowance and the injection line respond to the levers, so it computes those directly and
vectorised. That shortcut is only allowed if it gives the same quota as the formula, which is
the second half of this file.
"""

import numpy as np
import pytest

from src.model import quota as q
from src.model import reference as ref
from src.model.placeholder_objectives import PlaceholderModel, Placeholders, injection_allocation

TABLES = 27
# Measured 2026-09-24: every category total within one COE of the published table.
TOTAL_TOLERANCE = 1


@pytest.fixture(scope="module")
def tables():
    return ref.annex_tables()


@pytest.fixture(scope="module")
def reference():
    return ref.reference_quarter()


def test_formula_reproduces_every_annex_a_table(tables):
    assert len(tables) == TABLES
    for release in tables:
        inputs, published = ref.inputs_from_annex(release)
        out = q.quarterly_quota(inputs, ref.CURRENT_G_AB, ref.CURRENT_G_C)
        for c in q.CATEGORIES:
            assert out.growth[c] == published["growth"][c], (release["period"], c)
            replacement = out.replacement[c] + out.contribution_to_e[c]
            assert abs(replacement - published["replacement_net_of_e"][c]) <= TOTAL_TOLERANCE
            assert abs(out.total[c] - published["total"][c]) <= TOTAL_TOLERANCE, (
                f"{release['period']} Category {c}: formula {out.total[c]:,}, "
                f"published {published['total'][c]:,}"
            )


def test_growth_allowance_is_the_only_place_the_growth_rates_enter(tables):
    """Replacement and every adjustment are the same at any growth rate."""
    inputs, _ = ref.inputs_from_annex(tables[-1])
    low = q.quarterly_quota(inputs, 0.0, 0.0)
    high = q.quarterly_quota(inputs, 0.03, 0.02)
    assert low.replacement == high.replacement
    assert low.contribution_to_e == high.contribution_to_e
    assert low.adjustments == high.adjustments
    assert high.growth["A"] == int(0.03 * inputs.population["A"] / 4)
    assert high.growth["C"] == int(0.02 * inputs.population["C"] / 4)
    assert high.growth["D"] == high.growth["E"] == 0


@pytest.mark.parametrize("lever_set", ["injection", "theta"])
def test_the_model_reproduces_the_reference_quarter_exactly(reference, lever_set):
    model = PlaceholderModel(reference, lever_set, Placeholders.defaults())
    quota = model.quota(model.reference_point())
    for c in q.CATEGORIES:
        assert int(quota[c][0]) == reference.quota[c]


def test_the_vectorised_growth_path_matches_the_formula(reference):
    """Quota change from the growth levers, model against formula, at random policies."""
    model = PlaceholderModel(reference, "theta", Placeholders.defaults())
    base = q.quarterly_quota(reference.inputs, ref.CURRENT_G_AB, ref.CURRENT_G_C)
    rng = np.random.default_rng(3)
    for g_ab, g_c in rng.random((25, 2)) * 0.03:
        formula = q.quarterly_quota(reference.inputs, g_ab, g_c)
        modelled = model.quota(np.array([[g_ab, g_c, model.theta0]]))
        for c in q.CATEGORIES:
            expected = reference.quota[c] + formula.total[c] - base.total[c]
            assert int(modelled[c][0]) == expected, (g_ab, g_c, c)


def test_the_injection_lever_is_an_adjustment_to_the_formula(reference):
    """Moving the injection line changes quota exactly as changing that adjustment would."""
    allocation = injection_allocation()
    model = PlaceholderModel(reference, "injection", Placeholders.defaults(),
                             allocation=allocation)
    reference_total = sum(reference.injection.values())
    for injection in (0.0, 1_000.0, 5_155.0):
        modelled = model.quota(np.array([[ref.CURRENT_G_AB, ref.CURRENT_G_C, injection]]))
        for c in q.CATEGORIES:
            shift = round(injection * allocation[c]) - round(reference_total * allocation[c])
            assert int(modelled[c][0]) == reference.quota[c] + shift

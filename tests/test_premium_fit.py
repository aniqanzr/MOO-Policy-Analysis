"""The premium elasticity grid declared in the decision log on 2026-09-24, run as option 1.

These tests pin what the fit found, not what it was hoped to find.

The declared primary, S1 on the window from May 2022, is a bad fit: Category A's elasticity is
positive, premium rising with quota, and Category B's is indistinguishable from zero. Recorded
as a failed primary rather than replaced by a specification that looks right.

The question it was run to answer does not depend on which specification is right. No estimate
of A, B or C, in any window or specification, is stronger than -1. One, B on the long window
with no controls, has an interval that reaches past -1. Every other interval sits wholly on the
weaker side. That is the side on which stage 5 found the injection fallback's front collapses.
"""

import pytest

from src.fit import premium as pm


@pytest.fixture(scope="module")
def grid():
    return {(e.category, e.window, e.specification): e for e in pm.grid(["A", "B", "C"])}


def test_the_declared_primary_is_wrong_signed_for_category_a(grid):
    a = grid[("A", "W1", "S1")]
    b = grid[("B", "W1", "S1")]
    assert a.low > 0, "Category A's primary elasticity was positive when this was written"
    assert b.low < 0 < b.high, "Category B's primary elasticity was indistinguishable from zero"


def test_no_estimate_is_stronger_than_minus_one(grid):
    for key, estimate in grid.items():
        assert estimate.high > -1, f"{key}: interval wholly below -1, {estimate.high:.3f}"


def test_only_one_interval_reaches_past_minus_one(grid):
    straddling = {key for key, e in grid.items() if e.side == "straddles -1"}
    assert straddling == {("B", "W3", "S1")}


def test_the_specifications_with_a_negative_sign_agree_on_the_side(grid):
    """S2 and S3 in the primary window: negative, and weaker than -1, for all three."""
    for category in "ABC":
        for specification in ("S2", "S3"):
            e = grid[(category, "W1", specification)]
            assert -1 < e.b < 0, (category, specification, e.b)


def test_motorcycles_are_the_exception():
    """Category D, recent windows: every interval reaches -1. Not on the weaker side."""
    for window in ("W1", "W2"):
        for specification in pm.SPECIFICATIONS:
            e = pm.fit("D", window, specification)
            assert e.side == "straddles -1", (window, specification, e.b)


def test_categories_a_b_c_e_never_stronger_than_minus_one():
    for category in "ABCE":
        for window in pm.WINDOWS:
            for specification in pm.SPECIFICATIONS:
                e = pm.fit(category, window, specification)
                assert e.high > -1, (category, window, specification)


def test_no_drift_the_usable_specifications_can_distinguish():
    """The declared drift test. Under S2 and S3, A, B and C show no change either way.

    The only drift in A, B and C is under S1, the specification already reported as a bad fit,
    and it is the same trend confound read a second time.
    """
    for d in pm.drift(["A", "B", "C"]):
        if d.specification == "S1":
            assert d.reading == "premium moves less per unit of quota than before"
        else:
            assert d.reading == "no change the interval can distinguish", (
                d.category, d.specification, d.change)

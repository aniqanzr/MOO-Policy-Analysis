"""Stage 9 of docs/BUILD_SEQUENCE.md. BPR against annual peak-hour speeds. A-09.

Declared in the decision log on 2026-09-25 before it ran. These tests pin what it found: the
published annual data do not identify the BPR exponent under any of the six declared fits. In
the primary fits, and in the pandemic variants, pace falls as stock per lane-km rises, the wrong
direction for a volume-delay curve. With expressway capacity held at 2023, pace rises with load
but only with a negative free-flow speed. No profile interval is bounded.
"""

import pytest

from src.fit import congestion as cg


@pytest.fixture(scope="module")
def results():
    return {(r.road, r.variant): r for r in cg.fits()}


def test_six_fits_as_declared(results):
    assert len(results) == 6


def test_no_fit_identifies_beta(results):
    for key, r in results.items():
        assert not r.identified, key
        assert not r.bounded, key


def test_the_primary_fits_have_pace_falling_with_load(results):
    for road, variant in cg.PRIMARY.items():
        assert not results[(road, variant)].rising, road


def test_the_held_capacity_fits_rise_only_with_a_negative_free_flow_speed(results):
    for key, r in results.items():
        if "held" in r.variant:
            assert r.rising, key
            assert not r.physical, key
        else:
            assert not r.rising, key


def test_offset_moves_the_slope_by_about_nine_percent_at_beta_four():
    low, high = cg.offset_slope_factor(4.0, 0.0287)
    assert low == pytest.approx(0.916, abs=1e-3)
    assert high == pytest.approx(1.089, abs=1e-3)

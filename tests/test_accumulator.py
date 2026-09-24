"""Stage 7 of docs/BUILD_SEQUENCE.md. The accumulator backtest. A-04.

Declared in the decision log on 2026-09-24 before it ran. These tests pin what it found.

The published stock is the published flows accumulated: since 2002, registrations minus
deregistrations reproduce the change in stock to within a quarter of a percent over any five
years, category by category. The brief's accumulator, quota released in place of registrations,
does not. Over five years it misses by 2 to 3 percent of stock at the median and 4 to 6 percent
at worst, against a tolerance of 1.25 percent. The gap is quota against registrations, not the
data: vehicles enter the stock outside the bidding, and motorcycle quota runs ahead of
motorcycle registrations.
"""

import pandas as pd
import pytest

from src.model import accumulator as acc


@pytest.fixture(scope="module")
def cfg():
    return acc.settings()


def test_the_window_matches_the_model_horizon(cfg):
    import tomllib
    with (acc.ROOT / "config" / "placeholders.toml").open("rb") as f:
        years = tomllib.load(f)["horizon"]["years"]
    assert cfg["window_months"] == 12 * years


def test_the_tolerance_is_the_smallest_growth_rate_over_the_horizon(cfg):
    assert cfg["tolerance"] == pytest.approx(1.0025 ** 5 - 1, abs=1e-6)


def test_suspended_months_released_no_quota():
    q = acc.quota()
    assert (q.loc[acc.SUSPENDED] == 0).all().all()
    assert q.loc[pd.Period("2020-03", "M"):pd.Period("2020-08", "M")].notna().all().all()


def test_published_flows_reproduce_the_published_stock_since_2002(cfg):
    P, R, D = acc.population(), acc.registrations(), acc.deregistrations()
    for key in ("A", "B", "C", "D"):
        errors = acc.window_errors(key, P[key], R[key], D[key], cfg["window_months"]).errors
        errors = errors[errors.index >= pd.Period("2002-03", "M")]
        assert errors.abs().max() < 0.0025, key


def test_the_total_reconciles_across_the_whole_record(cfg):
    total = {r.label: r for r in acc.level1(cfg["window_months"])}["total"]
    assert total.max < 0.001


def test_the_accumulator_on_quota_released_fails_the_gate(cfg):
    for result in acc.level2(cfg["window_months"], "Quota"):
        assert not result.passes(cfg["tolerance"]), result.label
        assert result.median > cfg["tolerance"], result.label


def test_successful_bids_do_not_rescue_it(cfg):
    for result in acc.level2(cfg["window_months"], "Successful Bids"):
        assert not result.passes(cfg["tolerance"]), result.label


def test_the_cars_and_goods_error_changes_sign(cfg):
    """Quota runs ahead of the stock in the 2000s and behind it from about 2011."""
    result = {r.label: r for r in acc.level2(cfg["window_months"])}["A+B+C with E"]
    early = result.errors[result.errors.index < pd.Period("2008-01", "M")]
    late = result.errors[result.errors.index >= pd.Period("2013-01", "M")]
    assert (early > 0).all()
    assert (late < 0).all()


def test_the_stock_is_not_a_rolling_decade_of_registrations():
    """A-04 as worded. Since 2000 the ratio runs from 0.77, March 2009, to 1.36, April 2000."""
    ratio = acc.level3()["ratio"]
    ratio = ratio[ratio.index >= pd.Period("2000-01", "M")]
    assert ratio.min() < 0.8
    assert ratio.max() > 1.2

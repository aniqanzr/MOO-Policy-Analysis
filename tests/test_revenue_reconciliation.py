"""Stage 3 of docs/BUILD_SEQUENCE.md. Revenue reconciliation, A-10.

Computed revenue is quota times premium summed across all five categories over a financial
year. The target is the Vehicle Quota Premiums line in the government accounts. The gate asks
whether the two land within a reasonable margin of each other.

They do not, and the tests below pin what was found rather than asserting what was hoped for.
For FY2024 the bidding record produces 79 percent of the published figure. The shortfall is
one-signed, it appears in every financial year from FY2011 onward, and it is not an artefact
of the period alignment or of the choice between quota and successful bids. Those three
statements are what the tests check, because they are what separates a structural gap from
the pipeline bug the brief tells you to suspect first.

The pipeline checks come first below, in the order they would fail: categories, separators,
suspended exercises, period alignment. Only after those pass does the residual mean anything.

Every band in this file was measured before it was written. The measured value sits next to
each one.
"""

import pytest

from src.model import revenue

# The financial year the reconciliation runs against. FY2024 is the latest with actual
# figures. FY2025 is a revised estimate and FY2026 is budgeted, and the module refuses both.
TARGET_FY = 2024

# Measured on the committed files, 2026-09-04. Recorded so a change in either input shows up
# as a failing test rather than as a quietly different number.
FY2024_COMPUTED_MILLION = 5057.4
FY2024_PUBLISHED_MILLION = 6379.2

# The MOF spot check A-17 asks for. Table 2.1 of "Review of Financial Year 2025", in the
# Revenue and Expenditure Estimates for FY2026, gives Vehicle Quota Premiums actual FY2024 as
# 6.38 billion. The PDF is committed at data/raw/mof-review-of-fy2025.pdf.
MOF_FY2024_BILLION = 6.38


@pytest.fixture(scope="module")
def bidding():
    exercises, gaps, columns = revenue.load_bidding()
    return exercises, gaps, columns


@pytest.fixture(scope="module")
def target():
    return revenue.load_target()


@pytest.fixture(scope="module")
def result(reconciliation_recorder):
    result = revenue.reconcile(TARGET_FY)
    reconciliation_recorder.append(
        {
            "fy": result.fy,
            "computed_quota": result.computed["quota"] / 1e6,
            "computed_successful": result.computed["successful"] / 1e6,
            "published": result.published_million,
            "residual": result.residual_million,
            "ratio": result.ratio,
            "exercises": result.exercises,
        }
    )
    return result


def test_period_alignment_is_the_financial_year(target):
    """April to March, not January to December. The published figures are financial years."""
    assert revenue.fiscal_year(2024, 4) == 2024
    assert revenue.fiscal_year(2025, 3) == 2024
    assert revenue.fiscal_year(2024, 3) == 2023

    months = revenue.fiscal_year_months(2024)
    assert len(months) == 12
    assert months[0] == (2024, 4)
    assert months[-1] == (2025, 3)

    footnote = target.meta["table"]["footnote"]
    assert "financial year, which begins on 1 April" in footnote


def test_all_five_categories_are_summed(bidding, result):
    """A-06. The published line covers A, B, C, D and E, so the sum has to as well."""
    exercises, _, _ = bidding
    in_year = [e for e in exercises if e.fiscal_year == TARGET_FY]
    assert {e.category for e in in_year} == set(revenue.CATEGORIES)

    # 12 months, two biddings, five categories, nothing missing.
    assert result.exercises == 24
    assert len(in_year) == 120
    assert result.gaps == []

    # Dropping any one category moves the total, so none of them is a rounding error that
    # could be left out without noticing.
    for category, total in result.by_category.items():
        assert total > 0, f"Category {category} contributed nothing"


def test_thousands_separators_and_missing_markers_are_read_correctly():
    """A-13. A published file changes its own conventions partway through."""
    assert revenue._clean("1,438") == 1438.0
    assert revenue._clean(" 852 ") == 852.0
    for marker in ("-", "", "na", "n.a."):
        assert revenue._clean(marker) is None


def test_suspended_2020_exercises_are_absent_rather_than_zero(bidding):
    """April to June 2020 held no bidding. A zero would be a number nobody published."""
    exercises, gaps, _ = bidding
    suspended = {(2020, 4), (2020, 5), (2020, 6)}

    assert not [e for e in exercises if (e.year, e.month) in suspended]
    gap_months = {(g["year"], g["month"]) for g in gaps}
    assert suspended <= gap_months


def test_target_refuses_years_that_are_not_actual_figures(target):
    """The A-10 constraint. FY2025 is revised and FY2026 is budgeted, so neither is a target.

    The cutoff comes from the table footnote in the committed metadata, not from a constant
    in the code, so a re-pull that moves it moves this too.
    """
    assert target.latest_actual_fy == 2024

    assert target.actual(2024) == pytest.approx(FY2024_PUBLISHED_MILLION)

    for fy in (2025, 2026):
        with pytest.raises(revenue.ReconciliationError, match="actual figure"):
            target.actual(fy)

    with pytest.raises(revenue.ReconciliationError, match="actual figure"):
        revenue.reconcile(2025)


def test_target_agrees_with_the_mof_document(target):
    """A-17. The SingStat line and the MOF document are the same number for FY2024.

    AGD and MOF publish from the same accounts, but that the two figures are identical was an
    assumption until one year was checked. MOF states 6.38 billion to two decimal places, so
    the check is at that precision and no finer.
    """
    assert round(target.actual(2024) / 1000, 2) == MOF_FY2024_BILLION


def test_computed_revenue_matches_the_recorded_figures(result):
    """Pins the arithmetic against the committed files."""
    assert result.computed_million == pytest.approx(FY2024_COMPUTED_MILLION, abs=0.1)
    assert result.published_million == pytest.approx(FY2024_PUBLISHED_MILLION, abs=0.1)


def test_the_reconciliation_falls_short(result):
    """The stage 3 gate result, recorded rather than asserted away.

    Computed revenue is 79 percent of the published line for FY2024 and the residual is
    positive. If this test starts failing, the gap has moved and the reason has to be
    established before anything downstream of it is trusted.
    """
    assert result.residual_million > 0
    assert 0.75 < result.ratio < 0.85  # measured 0.793


def test_the_shortfall_is_not_a_period_alignment_artefact(bidding, result):
    """Shifting the twelve-month window moves the total by far less than the residual.

    Measured: the four windows span 456 million, against a residual of 1,322 million, and the
    best-placed window still falls 1,209 million short of the published figure.
    """
    exercises, _, _ = bidding
    windows = [
        revenue.revenue_in_window(exercises, TARGET_FY, month) / 1e6
        for month in (1, 3, 4, 5)
    ]
    spread = max(windows) - min(windows)

    assert spread < result.residual_million / 2
    assert result.published_million - max(windows) > result.residual_million * 0.8


def test_the_shortfall_is_not_the_choice_of_revenue_basis(result):
    """Successful bids times premium is lower still, so the basis cannot close the gap.

    Measured: successful bids give 98.6 percent of the quota basis.
    """
    quota_basis = result.computed["quota"]
    successful_basis = result.computed["successful"]

    assert successful_basis <= quota_basis
    assert successful_basis / quota_basis > 0.97
    assert successful_basis / 1e6 < result.published_million


def test_the_shortfall_holds_across_recent_years(bidding, target):
    """One-signed from FY2011 onward, which is what makes it structural rather than a slip.

    The years before FY2010 run the other way, by up to a factor of sixteen, and the reason is
    not established from any committed source. A-20 records that, and it is why the target is
    treated as usable only from FY2010.
    """
    exercises, _, columns = bidding
    covered = [
        fy
        for fy in revenue.covered_fiscal_years(columns)
        if 2011 <= fy <= target.latest_actual_fy
    ]
    assert len(covered) >= 10

    for fy in covered:
        computed = sum(e.revenue("quota") for e in exercises if e.fiscal_year == fy) / 1e6
        published = target.values[fy]
        assert computed <= published * 1.02, (
            f"FY{fy}: computed {computed:,.1f} exceeds published {published:,.1f}, "
            "which breaks the one-signed pattern the residual explanation rests on"
        )

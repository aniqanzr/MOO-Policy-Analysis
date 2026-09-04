"""Does the wide bidding table mean the same thing before 2010 as after it. A-21.

`quota-premium-monthly` is the only source for 2002 to 2009. The long table starts at
2010-01, so nothing outside the file itself can check that span value by value, and stage 6
would read any change in what the columns mean as elasticity drift. A-20 gave a reason to ask:
computed revenue runs above the published line before FY2010 and below it after.

These tests are the checks in `src/ingest/verify_quota_premium.py`, held as assertions. They
compare the two eras rather than testing absolute quality, because the question is not whether
the file is good, it is whether it changed.

The sharp one is the prevailing quota premium identity. PQP is published as the moving average
of the quota premium over the latest three months in which bidding was held, so three
published columns have to agree arithmetically. They do, to the dollar, in every category
month of both eras. A file whose premium column changed meaning at 2010 could not do that
without the PQP column having been changed to match.
"""

import pytest

from src.ingest import verify_quota_premium as verify

# Full calendar years only. 2002 starts in February, 2020 lost three months to the bidding
# suspension, and 2026 is the year the file was pulled in.
PART_YEARS = {2002, 2020, 2026}


@pytest.fixture(scope="module")
def wide():
    return verify.load_wide()


def test_two_bidding_exercises_a_month_in_every_full_year(wide):
    """The open bidding system has run two exercises a month since April 2002."""
    counts = {
        year: row["exercises"]
        for year, row in verify.report_shape(*wide).items()
    }

    for year, exercises in counts.items():
        if year in PART_YEARS:
            continue
        assert exercises == 24, f"{year} has {exercises} exercises, expected 24"

    assert counts[2002] == 22  # February onward
    assert counts[2020] == 18  # April, May and June suspended


def test_category_quotas_sum_to_the_published_totals(wide):
    """The parts add up to the file's own totals, in every exercise, in both eras.

    An aggregate written where a per-exercise figure belongs would break this.
    """
    shape = verify.report_shape(*wide)
    differ = sum(row["sums_differ"] for row in shape.values())
    matched = sum(row["sums_match"] for row in shape.values())

    assert differ == 0
    assert matched > 500


def test_premium_is_a_per_exercise_price_not_a_monthly_average(wide):
    """A monthly average would be written identically against both biddings of a month."""
    same, total = verify.report_premium_is_per_exercise(*wide)

    for era in total:
        share = same[era] / total[era]
        assert share < 0.05, (
            f"{era}: the two biddings carry the same premium in {share:.1%} of "
            "category-months, which is what a monthly average would look like"
        )


def test_pqp_identity_holds_in_both_eras(wide):
    """Every published PQP is the three-month moving average of the premium column.

    Measured: exact within a dollar in 100 percent of category-months, worst error 0.83
    dollars, over 93 months per category before 2010 and 199 after.
    """
    results = verify.report_pqp_identity(*wide)
    assert results, "no PQP months were checked"

    eras = {era for era, _ in results}
    assert eras == {"2002-2009", "2010-2026"}

    for (era, category), row in results.items():
        assert row["n"] >= 90, f"{era} {category}: only {row['n']} months checked"
        assert row["within"] == row["n"], (
            f"{era} {category}: {row['n'] - row['within']} of {row['n']} months miss the "
            f"published definition, worst error {max(row['errors']):.2f} dollars"
        )


def test_awarded_coes_track_registrations_in_both_eras(wide):
    """COEs awarded against an independent registration series, in both eras.

    Registrations that need no bid are removed first: Early Turnover Scheme goods vehicles get
    a replacement COE, and taxis have paid the Category A prevailing quota premium rather than
    bidding since August 2012. Both begin after 2010, so leaving them in makes the later era
    look worse for a reason that has nothing to do with the bidding table.
    """
    ratios = verify.report_against_registrations(*wide)

    for era, values in ratios.items():
        # Seven full years before the break, 2003 to 2009, and sixteen after.
        assert len(values) >= 7
        # Measured: 0.99 to 1.05 before the break, 0.96 to 1.08 after.
        assert all(0.9 < ratio < 1.1 for ratio in values), (
            f"{era}: adjusted ratio ranges {min(values):.2f} to {max(values):.2f}"
        )


def test_both_bidding_tables_give_the_same_revenue_over_the_overlap(wide):
    """Same multiplication, two independently published tables, no difference.

    This is what makes the post-2010 arithmetic trustworthy, and the reason the pre-2010 span
    needs the other checks: there is no second table back there to run this against.
    """
    worst = verify.report_cross_table(*wide)
    assert worst < 0.01, f"tables differ by up to {worst:,.1f} million in a financial year"

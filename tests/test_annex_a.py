"""Stage 4 of docs/BUILD_SEQUENCE.md. The deregistration series and the quota arithmetic.

Twenty-nine Annex A tables from LTA's quota releases, February 2020 to August 2026, extracted by
`src/ingest/extract_annex_a.py`. These tests hold what that extraction found, so a re-pull or a
change to the parser that moves any of it fails here rather than downstream in the quota formula.

Three things are established and one is recorded.

M650291 is the formula's deregistration term. B1 in every table matches the SingStat series
exactly, in every category, over whatever window B1 names. A-16's first question.

M650291 does not carry guaranteed deregistrations. Annex A does, as its own line, from the
August 2023 quarter. A-16's second question.

The formula changed twice in 2022 and 2023, and the arithmetic itself says when: a three-month
window through the May 2022 quarter, six months for August and November 2022, twelve from
February 2023. The brief's break table had the second change and not the first. A-11.

Recorded, not asserted away: four published category values that no rounding of their own
formula produces, each off by at most 1.25 COEs.
"""

import pytest

from src.ingest import extract_annex_a as annex

# Measured 2026-09-24 on the committed PDFs.
TABLES = 29
FORMULA_TABLES = 27        # the two mid-quarter revisions carry no formula lines
SUSPENSION_RETURNED = 19_490

# The four category cells whose published value no rounding of share x net deregistrations
# gives. Pinned so a fifth appearing, or one of these changing, is noticed.
KNOWN_DEVIATIONS = {
    ("Feb 2024 to Apr 2024", "C"),
    ("May 2025 to Jul 2025", "B"),
    ("Aug 2025 to Oct 2025", "B"),
    ("Feb 2026 to Apr 2026", "C"),
}


@pytest.fixture(scope="module")
def extracted():
    releases, rows, unread = annex.extract()
    return releases, rows, unread


@pytest.fixture(scope="module")
def deregistrations():
    return annex.load_deregistrations()


def windows(releases):
    """(quota period, window, B1 line) for every table with formula lines, in date order."""
    found = []
    for release in releases:
        parsed, window = annex.deregistration_line(release)
        if parsed is not None:
            found.append((release["period"], window, parsed))
    return found


def test_every_table_is_read_and_nothing_is_guessed(extracted):
    releases, _, unread = extracted
    assert len(releases) == TABLES
    assert unread == [], f"lines left unread: {unread}"
    revisions = [r for r in releases if r["revision"]]
    assert len(revisions) == TABLES - FORMULA_TABLES


def test_b1_is_exactly_the_m650291_series(extracted, deregistrations):
    """A-16, first question. Same numbers, every category, every window, every regime."""
    releases, _, _ = extracted
    checked = 0
    for period, window, parsed in windows(releases):
        (y, m), end = window
        months = set()
        while (y, m) <= end:
            months.add((y, m))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        for category in annex.DEREG_ROWS:
            published = sum(deregistrations[category].get(month, 0) for month in months)
            assert parsed["values"][category] == published, (
                f"{period} Category {category}: Annex A {parsed['values'][category]:,} "
                f"against M650291 {published:,}"
            )
        checked += 1
    assert checked == FORMULA_TABLES


def test_guaranteed_deregistrations_are_only_in_annex_a(extracted):
    """A-16, second question. M650291 has no such split. Annex A has it from August 2023 on."""
    releases, _, _ = extracted
    formula = [r for r in releases if not r["revision"]]
    with_line = [r["period"] for r in formula if annex.guaranteed_line(r)[1]]

    assert with_line[0] == "Aug 2023 to Oct 2023"
    # Present in every formula table from the first one onward, with no gap.
    first = next(i for i, r in enumerate(formula) if r["period"] == with_line[0])
    assert len(with_line) == len(formula) - first


def test_the_arithmetic_dates_the_two_formula_changes(extracted):
    """A-11. Window length in months, read from B1's own label, against the quota quarter.

    Three months at 100 percent through the May 2022 quarter. Six months at 50 percent for the
    August and November 2022 quarters. Twelve months at 25 percent from February 2023.
    """
    releases, _, _ = extracted
    lengths = {period: annex.months_between(window) for period, window, _ in windows(releases)}

    def start(period):
        month, year = period.split(" to ")[0].split()
        return int(year), annex.MONTHS.index(month) + 1

    for period, length in lengths.items():
        if start(period) < (2022, 8):
            assert length == 3, period
        elif start(period) < (2023, 2):
            assert length == 6, period
        else:
            assert length == 12, period

    assert lengths["Aug 2022 to Oct 2022"] == 6
    assert lengths["Feb 2023 to Apr 2023"] == 12


def test_each_table_adds_up(extracted):
    """Total quota equals the table's own subtotal lines, in every table with formula lines."""
    releases, _, _ = extracted
    ok, n = annex.check_table_totals(releases)
    assert n == FORMULA_TABLES
    assert ok == n


def test_the_replacement_line_deviations_are_the_known_four(extracted):
    """Recorded rather than tolerated. Four cells no rounding reproduces, none by more than 1.25."""
    releases, _, _ = extracted
    checked, deviations = annex.check_replacement_share(releases)
    assert checked == FORMULA_TABLES

    found = {(period, category) for period, category, _, _ in deviations}
    assert found == KNOWN_DEVIATIONS
    assert max(abs(got - expected) for _, _, expected, got in deviations) <= 1.25


def test_the_suspended_quota_returned_is_19490(extracted):
    """The brief's figure, from the Annexes rather than from the prose.

    The last return is in the May to July 2021 table and covers May and June only: the June
    2020 release says the quota was returned from July 2020 to June 2021.
    """
    releases, _, _ = extracted
    returned = annex.suspension_returns(releases)
    assert sum(value for _, _, value in returned) == SUSPENSION_RETURNED
    assert returned[0][0] == "Jul 2020 to Jul 2020"
    assert returned[-1][0] == "May 2021 to Jul 2021"

"""Shared fixtures, and the reports the stage gates are read from.

The build sequence asks for the numbers to be reported, not just asserted. Collecting the
measurements and printing them in the terminal summary means they show up on every run rather
than only when something fails. Stage 1 reports benchmark error, stage 3 reports the revenue
residual.
"""

import pytest

_MEASUREMENTS = []
_RECONCILIATIONS = []


@pytest.fixture(scope="session")
def metrics_recorder():
    return _MEASUREMENTS


@pytest.fixture(scope="session")
def reconciliation_recorder():
    return _RECONCILIATIONS


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    _optimiser_summary(terminalreporter)
    _reconciliation_summary(terminalreporter)


def _reconciliation_summary(terminalreporter):
    if not _RECONCILIATIONS:
        return

    write = terminalreporter.write_line
    write("")
    write("Revenue reconciliation, millions of dollars")
    header = (
        f"{'FY':<8}{'quota basis':>14}{'bids basis':>13}{'published':>12}"
        f"{'residual':>11}{'share':>8}"
    )
    write(header)
    write("-" * len(header))
    for r in sorted(_RECONCILIATIONS, key=lambda r: r["fy"]):
        write(
            f"FY{r['fy']:<6}{r['computed_quota']:>14,.1f}{r['computed_successful']:>13,.1f}"
            f"{r['published']:>12,.1f}{r['residual']:>11,.1f}{r['ratio']:>8.1%}"
        )
    write("")
    write(
        "share: computed as a fraction of the published Vehicle Quota Premiums line. "
        "The gate expected agreement and did not get it. See A-10 and A-19."
    )


def _optimiser_summary(terminalreporter):
    if not _MEASUREMENTS:
        return

    rows = sorted(_MEASUREMENTS, key=lambda m: (m["benchmark"], m["seed"]))
    write = terminalreporter.write_line

    write("")
    write("Optimiser validation, error against the analytic fronts")
    header = (
        f"{'benchmark':<10}{'seed':>5}{'pts':>6}{'resid mean':>13}{'resid max':>12}"
        f"{'GD':>12}{'IGD':>12}{'tail mean':>12}"
    )
    write(header)
    write("-" * len(header))
    for m in rows:
        write(
            f"{m['benchmark']:<10}{m['seed']:>5}{m['n_points']:>6}"
            f"{m['residual_mean']:>13.3e}{m['residual_max']:>12.3e}"
            f"{m['gd']:>12.3e}{m['igd']:>12.3e}{m['tail_mean']:>12.3e}"
        )
    write("")
    write(
        "resid: distance to the closed-form front. GD: convergence. "
        "IGD: convergence and coverage."
    )
    write("tail: deviation of the tail decision variables from their known optimal setting.")

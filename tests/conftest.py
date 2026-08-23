"""Shared fixtures, and the error report the stage 1 gate is read from.

The build sequence asks for the benchmark error to be reported, not just asserted. Collecting
the measurements and printing them in the terminal summary means the numbers show up on every
run rather than only when something fails.
"""

import pytest

_MEASUREMENTS = []


@pytest.fixture(scope="session")
def metrics_recorder():
    return _MEASUREMENTS


def pytest_terminal_summary(terminalreporter, exitstatus, config):
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

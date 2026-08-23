"""Stage 1 of docs/BUILD_SEQUENCE.md. Optimiser validation.

Checks the pymoo NSGA-II configuration against two problems whose Pareto fronts are known in
closed form: ZDT1 for two objectives and DTLZ2 for three. It uses no COE data. The point is
that when a COE frontier looks wrong in week two, the optimiser has already been ruled out.

Three things are checked per benchmark, because they fail in different ways.

1. Analytic residual. Distance from each generated point to the front's closed form. Catches a
   run that has not converged.
2. Generational distance and inverted generational distance against an independently generated
   reference set. GD catches non-convergence, IGD also catches a run that converged onto only
   part of the front.
3. Decision-space deviation. Both problems attain their front at a known setting of the tail
   variables, x_i = 0 for ZDT1 and x_i = 0.5 for DTLZ2. This is the one check that does not go
   through objective space at all.

Every tolerance below was set by measuring first. The observed worst case over the five seeds
is recorded next to each one, and the tolerance is that value rounded up with headroom. No
tolerance here was picked to make a test pass.
"""

import numpy as np
import pytest
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

from tests.analytic_fronts import (
    dtlz2_front,
    dtlz2_residual,
    generational_distance,
    inverted_generational_distance,
    zdt1_front,
    zdt1_residual,
)

SEEDS = (0, 1, 2, 3, 4)

BENCHMARKS = {
    # Population and generation counts are the smallest that reached the tolerances below.
    # DTLZ2 gets the larger population because NSGA-II's crowding distance spreads points
    # less evenly in three objectives than in two. See the note in the decision log.
    "zdt1": {
        "pop_size": 100,
        "n_gen": 400,
        "front": zdt1_front,
        "residual": zdt1_residual,
        # tail variables x_2 ... x_n, optimal at 0
        "tail_slice": slice(1, None),
        "tail_optimum": 0.0,
        # tolerance          observed worst over the five seeds
        "max_residual_mean": 5e-3,   # 1.33e-3
        "max_residual_max": 1e-1,    # 2.66e-2
        "max_gd": 5e-3,              # 7.91e-4
        "max_igd": 1e-2,             # 4.79e-3
        "max_tail_mean": 2e-3,       # 1.60e-4
    },
    "dtlz2": {
        "pop_size": 200,
        "n_gen": 400,
        "front": dtlz2_front,
        "residual": dtlz2_residual,
        # tail variables x_M ... x_n, optimal at 0.5
        "tail_slice": slice(2, None),
        "tail_optimum": 0.5,
        # tolerance          observed worst over the five seeds
        "max_residual_mean": 1.5e-2,  # 6.06e-3
        "max_residual_max": 1.5e-1,   # 3.91e-2
        "max_gd": 3e-2,               # 1.41e-2
        "max_igd": 1e-1,              # 5.00e-2
        "max_tail_mean": 5e-2,        # 1.79e-2
    },
}

_CACHE = {}


def _run(name, seed, recorder):
    """Run one benchmark at one seed and measure it. Cached so each run happens once."""
    key = (name, seed)
    if key in _CACHE:
        return _CACHE[key]

    spec = BENCHMARKS[name]
    problem = get_problem(name)
    result = minimize(
        problem,
        NSGA2(pop_size=spec["pop_size"]),
        ("n_gen", spec["n_gen"]),
        seed=seed,
        verbose=False,
    )

    reference = spec["front"]()
    residual = spec["residual"](result.F)
    tail = np.abs(result.X[:, spec["tail_slice"]] - spec["tail_optimum"])

    measured = {
        "benchmark": name,
        "seed": seed,
        "n_points": len(result.F),
        "residual_mean": float(residual.mean()),
        "residual_max": float(residual.max()),
        "gd": float(generational_distance(result.F, reference)),
        "igd": float(inverted_generational_distance(result.F, reference)),
        "tail_mean": float(tail.mean()),
        "tail_max": float(tail.max()),
    }
    _CACHE[key] = measured
    recorder.append(measured)
    return measured


@pytest.fixture(params=SEEDS, ids=lambda s: f"seed{s}")
def seed(request):
    return request.param


@pytest.mark.parametrize("name", sorted(BENCHMARKS))
def test_converges_to_analytic_front(name, seed, metrics_recorder):
    """Generated points sit on the closed-form front."""
    m = _run(name, seed, metrics_recorder)
    spec = BENCHMARKS[name]
    assert m["residual_mean"] < spec["max_residual_mean"], (
        f"{name} seed {seed}: mean analytic residual {m['residual_mean']:.3e} "
        f"exceeds {spec['max_residual_mean']:.3e}"
    )
    assert m["residual_max"] < spec["max_residual_max"], (
        f"{name} seed {seed}: worst point sits {m['residual_max']:.3e} off the front, "
        f"limit {spec['max_residual_max']:.3e}"
    )


@pytest.mark.parametrize("name", sorted(BENCHMARKS))
def test_covers_analytic_front(name, seed, metrics_recorder):
    """Generated points converge to the front and cover its extent."""
    m = _run(name, seed, metrics_recorder)
    spec = BENCHMARKS[name]
    assert m["gd"] < spec["max_gd"], (
        f"{name} seed {seed}: GD {m['gd']:.3e} exceeds {spec['max_gd']:.3e}, "
        "the run has not converged"
    )
    assert m["igd"] < spec["max_igd"], (
        f"{name} seed {seed}: IGD {m['igd']:.3e} exceeds {spec['max_igd']:.3e}, "
        "part of the front was missed"
    )


@pytest.mark.parametrize("name", sorted(BENCHMARKS))
def test_reaches_analytic_optimum_in_decision_space(name, seed, metrics_recorder):
    """The tail decision variables reach the setting that attains the front.

    Independent of the objective-space metrics. A configuration that produced a plausible
    looking front from the wrong part of the decision space would fail here and pass above.
    """
    m = _run(name, seed, metrics_recorder)
    spec = BENCHMARKS[name]
    assert m["tail_mean"] < spec["max_tail_mean"], (
        f"{name} seed {seed}: mean deviation of the tail variables from "
        f"{spec['tail_optimum']} is {m['tail_mean']:.3e}, limit {spec['max_tail_mean']:.3e}"
    )

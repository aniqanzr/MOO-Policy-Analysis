"""Closed-form Pareto fronts and error metrics for the stage 1 benchmarks.

The reference fronts here are built from the published analytic form of each problem, not
from pymoo's own `pareto_front()` tables. The point of stage 1 is to check pymoo's optimiser
against something outside pymoo, so the reference set is generated independently.

Sources for the analytic forms:

ZDT1  Zitzler, Deb and Thiele (2000), "Comparison of Multiobjective Evolutionary Algorithms:
      Empirical Results", Evolutionary Computation 8(2), 173-195. Problem T1. The front is
      f2 = 1 - sqrt(f1) for f1 in [0, 1], attained where g(x) = 1, which requires
      x_2 ... x_n = 0.

DTLZ2 Deb, Thiele, Laumanns and Zitzler (2002), "Scalable Multi-Objective Optimization Test
      Problems", CEC 2002, 825-830. Section 6.2. The front is the unit sphere in the positive
      orthant, sum(f_i^2) = 1, attained where g(x_M) = 0, which requires x_i = 0.5 for every
      variable in the last group.
"""

import numpy as np


def zdt1_front(n_points=2000):
    """Points on the ZDT1 front, evenly spaced in f1."""
    f1 = np.linspace(0.0, 1.0, n_points)
    return np.column_stack([f1, 1.0 - np.sqrt(f1)])


def zdt1_residual(F):
    """Vertical distance from each point to the ZDT1 front, f2 - (1 - sqrt(f1)).

    Vertical distance is never smaller than the perpendicular distance to the curve, so a
    bound on this is a conservative bound on how far the point actually sits off the front.
    """
    return np.abs(F[:, 1] - (1.0 - np.sqrt(np.clip(F[:, 0], 0.0, None))))


def dtlz2_front(n_partitions=60):
    """Points on the three-objective DTLZ2 front.

    A Das-Dennis simplex grid projected onto the unit sphere. Built here rather than imported
    so the reference set does not come from the library under test.
    """
    p = n_partitions
    grid = np.array(
        [(i, j, p - i - j) for i in range(p + 1) for j in range(p + 1 - i)], dtype=float
    )
    grid /= p
    return grid / np.linalg.norm(grid, axis=1, keepdims=True)


def dtlz2_residual(F):
    """Radial distance from each point to the DTLZ2 unit sphere, |‖f‖ - 1|.

    For a sphere the radial distance is the perpendicular distance, so this is exact.
    """
    return np.abs(np.linalg.norm(F, axis=1) - 1.0)


def _pairwise(A, B):
    return np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)


def generational_distance(F, reference):
    """Mean distance from each generated point to the nearest reference point.

    Measures convergence only. A run that lands exactly on one small patch of the front scores
    well here, which is why IGD is reported alongside it.
    """
    return _pairwise(F, reference).min(axis=1).mean()


def inverted_generational_distance(F, reference):
    """Mean distance from each reference point to the nearest generated point.

    Measures convergence and coverage together. Penalises a run that misses part of the front.
    """
    return _pairwise(reference, F).min(axis=1).mean()

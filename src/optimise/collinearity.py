"""Stage 5. Is the front a surface or a curve, under placeholder values. A-08.

Run it:

    python -m src.optimise.collinearity

A-08 is falsified if sampling the decision space finds the front is a curve rather than a
surface, or finds the three objectives near-perfectly explained by total quota alone. Three
measurements, each of which answers part of that and none of which is enough alone.

1. Rank of the map from levers to objectives. The Jacobian of the three objectives with
   respect to the three levers, both scaled to their ranges, at points across the decision
   space. Its singular values say how many independent directions the levers move the
   objectives in. Rank one means every lever does the same thing and the image is a curve.

2. Total quota R squared. Each objective regressed on a cubic in total quota. Near one for all
   three is A-08's second falsification condition: the levers act only through one number.

3. Dimension of the front itself. The NSGA-II front, and a local principal component analysis
   around each front point. A curve has one dominant local direction, a surface two. Reported
   as the ratio of the second local singular value to the first, whose median is near zero on
   a curve.

   The front has to come from the optimiser, not from a random sample. The non-dominated
   points of a random sample sit near the front but not on it, and that scatter reads as a
   second dimension: combinations whose NSGA-II front ratio is 0.02 to 0.05, plainly curves,
   gave 0.09 to 0.14 from the sample, and one gave 0.63 against 0.20. Measured on 2026-09-24
   before the sweep was switched over.

A structural fact the numbers should be read against. O1 is revenue over total quota and O3 is
revenue, so O1 times total quota equals O3 by definition. At a fixed total quota, cost and
revenue move together. The front can only be a surface if something other than total quota
moves one of them: a lever that changes revenue without changing total quota, or road load
that is not proportional to total quota. That is what the sweep's control case, equal road
load per vehicle, is for.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
from pathlib import Path

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from src.model import reference as ref
from src.model.placeholder_objectives import (
    OBJECTIVES,
    LEVER_SETS,
    PlaceholderModel,
    Placeholders,
    injection_allocation,
    load_config,
)

SWEEP_FILE = Path(__file__).resolve().parents[2] / "data" / "processed" / "stage5-sweep.csv"
SAMPLE = 4096
JACOBIAN_POINTS = 300
STEP = 0.01          # finite difference step, as a fraction of each lever's range
NEIGHBOURS = 12      # local PCA neighbourhood size on the front
SEED = 0


class _Problem(Problem):
    def __init__(self, model):
        bounds = model.bounds()
        super().__init__(n_var=3, n_obj=3, xl=bounds[:, 0], xu=bounds[:, 1])
        self.model = model

    def _evaluate(self, X, out, *args, **kwargs):
        out["F"] = self.model.evaluate(X)


def sample(model, n=SAMPLE, seed=SEED):
    rng = np.random.default_rng(seed)
    bounds = model.bounds()
    unit = rng.random((n, 3))
    return bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0])


def scale(F, reference=None):
    reference = F if reference is None else reference
    low, high = reference.min(axis=0), reference.max(axis=0)
    span = np.where(high > low, high - low, 1.0)
    return (F - low) / span, low, span


def jacobian_ratios(model, n=JACOBIAN_POINTS, seed=SEED):
    """Singular value ratios s2/s1 and s3/s1 of the scaled Jacobian at n interior points."""
    rng = np.random.default_rng(seed + 1)
    bounds = model.bounds()
    width = bounds[:, 1] - bounds[:, 0]
    F_all = model.evaluate(sample(model))
    _, _, span = scale(F_all)

    unit = STEP + rng.random((n, 3)) * (1 - 2 * STEP)
    ratios = []
    for u in unit:
        J = np.zeros((3, 3))
        for j in range(3):
            up, down = u.copy(), u.copy()
            up[j] += STEP
            down[j] -= STEP
            F_up = model.evaluate(bounds[:, 0] + up * width)[0] / span
            F_down = model.evaluate(bounds[:, 0] + down * width)[0] / span
            J[:, j] = (F_up - F_down) / (2 * STEP)
        s = np.linalg.svd(J, compute_uv=False)
        ratios.append((s[1] / s[0], s[2] / s[0]) if s[0] > 0 else (0.0, 0.0))
    return np.array(ratios)


def total_quota_r2(model, X, F):
    """R squared of each objective on a cubic in total quota.

    An objective that does not vary at all over the sample, as O3 does at unit elasticity,
    returns nan rather than a number made of floating point noise.
    """
    q = model.total_quota(X)
    q = (q - q.mean()) / (q.std() or 1.0)
    design = np.column_stack([np.ones_like(q), q, q ** 2, q ** 3])
    out = []
    for k in range(3):
        y = F[:, k]
        if np.ptp(y) <= 1e-9 * max(abs(y.mean()), 1.0):
            out.append(np.nan)
            continue
        coef, *_ = np.linalg.lstsq(design, y, rcond=None)
        residual = y - design @ coef
        total = ((y - y.mean()) ** 2).sum()
        out.append(1 - (residual ** 2).sum() / total if total > 0 else 1.0)
    return np.array(out)


def front_of(F):
    index = NonDominatedSorting().do(F, only_non_dominated_front=True)
    return F[index]


def local_dimension(front, k=NEIGHBOURS):
    """Median ratios s2/s1 and s3/s1 of local PCA on the scaled front."""
    if len(front) <= k:
        return np.nan, np.nan, len(front)
    Z, _, _ = scale(front)
    distances = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(axis=2)
    r2, r3 = [], []
    for i in range(len(Z)):
        nearest = np.argsort(distances[i])[: k + 1]
        local = Z[nearest] - Z[nearest].mean(axis=0)
        s = np.linalg.svd(local, compute_uv=False)
        if s[0] > 0:
            r2.append(s[1] / s[0])
            r3.append(s[2] / s[0])
    return float(np.median(r2)), float(np.median(r3)), len(front)


def nsga_front(model, pop=200, generations=300, seed=SEED):
    result = minimize(_Problem(model), NSGA2(pop_size=pop), ("n_gen", generations),
                      seed=seed, verbose=False)
    return result.F


SWEEP_GENERATIONS = 200


def analyse(model, generations=300):
    X = sample(model)
    F = model.evaluate(X)
    jac = jacobian_ratios(model)
    r2 = total_quota_r2(model, X, F)
    return {
        "jacobian_s2_median": float(np.median(jac[:, 0])),
        "jacobian_s3_median": float(np.median(jac[:, 1])),
        "jacobian_s3_p05": float(np.percentile(jac[:, 1], 5)),
        "r2_total_quota": r2,
        "nsga_front": local_dimension(nsga_front(model, generations=generations)),
    }


def placeholder_grid(config):
    """Every combination the sweep covers."""
    b = config["premium"]["elasticity_sweep"]
    pcu = config["road_load"]["goods_vehicle_and_bus_sweep"]
    uppers = config["bounds"]["growth_upper_sweep"]
    categories = [tuple(config["objectives"]["categories_default"]),
                  tuple(config["objectives"]["categories_variant"])]
    base = Placeholders.defaults(config)
    for b_a, b_b, b_c, load, upper, cats in itertools.product(b, b, b, pcu, uppers, categories):
        elasticity = dict(base.elasticity, A=b_a, B=b_b, C=b_c)
        pcu_map = dict(base.pcu, C=load)
        yield Placeholders(
            elasticity=elasticity, pcu=pcu_map, alpha=base.alpha, beta=base.beta,
            base_vc=base.base_vc, years=base.years, categories=cats,
            growth_upper=upper, theta_half_width=base.theta_half_width,
        )


def write_sweep(lever_set, rows, append):
    """Every sweep combination and its measurements, so any row can be looked up later."""
    SWEEP_FILE.parent.mkdir(parents=True, exist_ok=True)
    fields = ["lever_set", "b_A", "b_B", "b_C", "pcu_C", "growth_upper", "categories",
              "jacobian_s2", "jacobian_s3", "r2_O1", "r2_O2", "r2_O3",
              "largest_unexplained", "o3_flat", "front_s2", "front_s3", "front_n"]
    with SWEEP_FILE.open("a" if append else "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not append:
            writer.writerow(fields)
        for p, m in rows:
            r2 = m["r2_total_quota"]
            flat = bool(np.isnan(r2[2]))
            unexplained = np.sqrt(np.clip(1 - r2, 0, 1))
            s2, s3, n = m["nsga_front"]
            writer.writerow([
                lever_set, p.elasticity["A"], p.elasticity["B"], p.elasticity["C"],
                p.pcu["C"], p.growth_upper, "".join(p.categories),
                f"{m['jacobian_s2_median']:.4f}", f"{m['jacobian_s3_median']:.4f}",
                *(("" if np.isnan(v) else f"{v:.5f}") for v in r2),
                "" if flat else f"{np.nanmax(unexplained):.4f}",
                flat, f"{s2:.4f}", f"{s3:.4f}", n,
            ])


def summarise(lever_set, rows):
    flat = [m for _, m in rows if np.isnan(m["r2_total_quota"][2])]
    live = [(p, m) for p, m in rows if not np.isnan(m["r2_total_quota"][2])]
    front = np.array([m["nsga_front"][0] for _, m in live])
    largest = np.array([
        np.nanmax(np.sqrt(np.clip(1 - m["r2_total_quota"], 0, 1))) for _, m in live
    ])
    print(f"   {lever_set}: {len(rows)} combinations, {len(flat)} with O3 flat at unit "
          "elasticity, left out of the figures below")
    print("      front s2/s1, percentiles 0 5 25 50 75 100: "
          + " ".join(f"{v:.3f}" for v in np.percentile(front, [0, 5, 25, 50, 75, 100])))
    print("      largest unexplained share, same percentiles: "
          + " ".join(f"{v:.3f}" for v in np.percentile(largest, [0, 5, 25, 50, 75, 100])))
    for cut in (0.05, 0.10, 0.20):
        print(f"      combinations with front s2/s1 below {cut:.2f}: "
              f"{(front < cut).sum()} of {len(front)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-sweep", action="store_true")
    args = parser.parse_args(argv)

    config = load_config()
    reference = ref.reference_quarter()
    allocations = {
        "pooled": injection_allocation(),
        "reference quarter": injection_allocation(reference.period),
    }
    print(f"\nreference quarter {reference.period}, theta anchor {reference.theta:.3f}")
    print("injection allocation, pooled over Annex A: "
          + ", ".join(f"{c} {v:.1%}" for c, v in allocations["pooled"].items() if v))

    from dataclasses import replace
    print("\n1. Main table, both lever sets, either side of unit elasticity")
    print(f"   {'lever set':<30}{'O1,O3 over':>11}{'b':>6}{'J s2/s1':>9}{'J s3/s1':>9}"
          f"{'unexpl O1':>10}{'unexpl O2':>10}{'unexpl O3':>10}{'front s2/s1':>12}{'s3/s1':>7}")
    base = Placeholders.defaults(config)
    category_sets = [tuple(config["objectives"]["categories_default"]),
                     tuple(config["objectives"]["categories_variant"])]
    for lever_set in LEVER_SETS:
        allocation_names = allocations if lever_set == "injection" else {"": None}
        for name, allocation in allocation_names.items():
            for categories in category_sets:
                for b in config["premium"]["elasticity_main"]:
                    kwargs = {"allocation": allocation} if allocation else {}
                    placeholders = replace(base, elasticity={c: b for c in base.elasticity},
                                           categories=categories)
                    model = PlaceholderModel(reference, lever_set, placeholders, **kwargs)
                    m = analyse(model)
                    s2, s3, _ = m["nsga_front"]
                    unexplained = np.sqrt(np.clip(1 - m["r2_total_quota"], 0, 1))
                    label = f"{lever_set} {name}".strip()
                    print(f"   {label:<30}{''.join(categories):>11}{b:>6}"
                          f"{m['jacobian_s2_median']:>9.3f}{m['jacobian_s3_median']:>9.3f}"
                          + "".join(f"{v:>10.3f}" for v in unexplained)
                          + f"{s2:>12.3f}{s3:>7.3f}")
    print("   J: median singular value ratios of the scaled Jacobian over 300 points.")
    print("   unexpl: share of each objective's spread that a cubic in total quota does not")
    print("   explain, the square root of 1 - R2. front: median local PCA ratios on the NSGA-II")
    print("   front, 12 neighbours. Goods vehicle load 2.0 PCU, growth up to 3 percent.")

    if not args.no_sweep:
        print(f"\n2. Sweep: every placeholder combination, NSGA-II fronts, "
              f"{SWEEP_GENERATIONS} generations")
        for lever_set in LEVER_SETS:
            rows = []
            for placeholders in placeholder_grid(config):
                model = PlaceholderModel(reference, lever_set, placeholders)
                rows.append((placeholders, analyse(model, generations=SWEEP_GENERATIONS)))
            write_sweep(lever_set, rows, append=lever_set != next(iter(LEVER_SETS)))
            summarise(lever_set, rows)
        print(f"   every combination is in {SWEEP_FILE.relative_to(SWEEP_FILE.parents[2])}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

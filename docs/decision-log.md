# Decision log

Choices that could have gone another way, with the option not taken and why. Appended to as
the build goes. This log is a deliverable.

Format: date, what was decided, what else was on the table, why this one.

---

## 2026-08-23. Repo layout follows section 7 literally

Created `data/raw`, `data/processed`, `src/fit`, `src/model`, `src/optimise`, `src/export`,
`tests` and `web` exactly as the brief names them, with `src` and its subpackages as importable
Python packages. Each `__init__.py` carries a docstring saying what belongs in that directory,
so the layout does not drift from the brief silently.

Alternative considered: a flatter `src/` with modules rather than subpackages, which is less
ceremony for a project this size. Rejected because the brief already fixed these names and
matching them keeps the case study, the brief and the tree readable against each other.

`data/raw` and `data/processed` are committed with `.gitkeep` files and nothing under `data/`
is gitignored. Raw downloads are committed on purpose so the pipeline reproduces from a clean
clone.

## 2026-08-23. statsmodels rather than scikit-learn for the fits

The brief allows either. Picked statsmodels.

Section 6 requires perturbing fitted coefficients across their confidence intervals to render
the frontier as a band, and section 4.1 requires plotting the path of a rolling-window
elasticity. statsmodels returns standard errors, confidence intervals and the regression
diagnostics needed to say whether a fit is bad, which section 4 and the working rules both
demand. scikit-learn returns point estimates and would mean bootstrapping the intervals by
hand.

Cost of the choice: scikit-learn would have been the better tool if the premium relationship
turns out to need regularisation or a non-parametric form. If that happens, revisit.

## 2026-08-23. Two dependencies beyond the named stack

The working rules cap dependencies at pymoo, numpy, pandas, a fitting library and Plotly
without a logged reason. Two additions.

`requests`, for scripting the data.gov.sg datastore API pulls named in section 8. The
alternative is `urllib` from the standard library, which works but makes retry and error
handling on a flaky public API more code than it saves. `requests` is already an indirect
dependency of the resolved tree.

`pytest`, to run the section 5.4 validation suite. The alternative is `unittest` from the
standard library. Picked pytest for parametrised cases, which the ZDT1 and DTLZ2 checks and the
sensitivity sweep will both want.

Neither is a modelling dependency. Neither introduces a coefficient or a functional form.

## 2026-08-23. Direct dependencies pinned to resolved versions, no lockfile

`requirements.txt` pins the seven direct dependencies to the versions that resolved on
2026-08-23 under Python 3.11. Transitive dependencies, including scipy and matplotlib pulled in
by pymoo and statsmodels, float.

Alternative considered: a full `pip freeze` lockfile, which is stricter reproduction. Rejected
for now because the direct pins already fix every version a result depends on, and a lockfile
is one more file to keep honest across three weeks. If a numeric result turns out to move
between transitive versions, that is the reason to add one.

## 2026-08-23. Stage 1 measures three errors, not one

The build sequence asks for the error against the analytic fronts. A single number would have
hidden the thing that turned out to matter, so the suite reports three per benchmark per seed.

Analytic residual is the distance from each generated point to the closed form, exact for
DTLZ2 where radial distance is perpendicular distance, and a conservative overestimate for
ZDT1 where it is measured vertically. Generational distance measures convergence alone.
Inverted generational distance measures convergence and coverage together, so it is the one
that catches a run that landed on the front but only covered a slice of it. A fourth check
looks at the tail decision variables, which both problems attain their front at a known
setting of, and is the only check that does not pass through objective space.

Alternative considered: IGD alone against `problem.pareto_front()`, which is the usual way
these benchmarks get reported. Rejected on two counts. It conflates convergence with coverage
in one number, which is exactly the distinction that turned out to be the finding. And it
takes the reference set from the library under test. The reference fronts are generated here
from the published closed forms instead, so the check is on pymoo rather than internal to it.

## 2026-08-23. Stage 1 tolerances measured before they were set

Every tolerance was fixed by running five seeds first, recording the worst case, and rounding
up with roughly two to eight times headroom. The observed worst case sits in a comment beside
each tolerance in `tests/test_optimiser_validation.py`. No tolerance was adjusted to make a
test pass.

Checked in the other direction as well. Dropping both runs from 400 generations to 5 fails
every one of the ten checks, so the gate is not vacuous.

## 2026-08-23. DTLZ2 error under NSGA-II is coverage, not convergence

Stage 1 passed, but it surfaced something that affects stage 11 rather than stage 1.

On DTLZ2 the three-objective error is roughly four times the two-objective error on ZDT1, and
the split between the metrics says why. GD sits at 0.013 and does not move. IGD sits at 0.049.
Quadrupling generations from 400 to 1600 changes IGD by less than a percent, at 0.0487. Raising
population from 200 to 500 to 1000 at fixed generations takes IGD to 0.0312 then 0.0217 while
GD stays flat at 0.012 to 0.014. Averages of three seeds throughout.

So the points reach the front and do not spread evenly across it. This is the known behaviour
of crowding distance in three objectives, and the brief freezes NSGA-II, so it is not a defect
to fix. The consequence is that on the COE problem, which is also three-objective, front
coverage is bought with population size and not with runtime. Stage 11 sizes its population on
that basis, and the reported IGD is the reason.

Alternative not taken: NSGA-III or a reference-direction method, which is the standard remedy
and would spread the points evenly. Not taken because the algorithm is frozen in section 0.1 of
the brief. Recording it here so the case study can state what the freeze cost rather than
presenting NSGA-II as the only option.

## 2026-08-23. Ingestion lives in src/ingest, which section 7 does not name

Section 7 lists `src/fit`, `src/model`, `src/optimise` and `src/export`. The pull script is
none of those. It is the stage before the fits, so it went in `src/ingest` alongside them
rather than in a `scripts/` directory off the root.

The repo layout is a provisional item, not a frozen one, and this touches nothing in the
frozen list. The static architecture stays static: this is a build-time script that writes
files into the repo, not a service.

Alternative considered: `scripts/pull_data.py` at the root, which is the more common
convention for one-off pulls. Rejected because ingestion is a pipeline stage that later stages
depend on and it reads better sitting in the same tree as the stages that consume it.

## 2026-08-23. One registry behind both the pull script and the manual list

`src/ingest/sources.py` holds all fourteen sources from section 8, the eight that have an API
and the six that do not, in one list. The pull script iterates the first group and prints the
second as the hand-download list.

Alternative considered: hardcode the dataset IDs in the pull script and keep the manual list
in prose in `data/raw/README.md`. Rejected because the two would drift. A source added to the
brief and not to the script would be silently missing rather than visibly unfetched.

## 2026-08-23. Stage 2 gate blocked, no network route to any government host

The gate asks for certainty about what has been ingested and what has to be fetched by hand.
Half of that is deliverable and half is not.

This session's egress policy allows package registries and the Anthropic API and nothing else.
`api-open.data.gov.sg`, `data.gov.sg`, `www.lta.gov.sg`, `www.mof.gov.sg`,
`tablebuilder.singstat.gov.sg` and `datamall2.mytransport.sg` all return 403 at the proxy on
CONNECT, as does `example.com`, so this is a blanket policy rather than anything specific to
these hosts. The proxy documentation says to report a 403 rather than route around it, so no
attempt was made to.

What this means for the gate. Not one of the eight dataset IDs in section 8 has been checked
against the live API. They are transcribed and well formed, thirty-two hex characters after a
`d_` prefix, and no two collide, but well formed is not the same as live, and the brief says
explicitly to re-check them because IDs and coverage change. Stage 2 fails.

What was done instead. The pull script is written and tested against a local stub of the
data.gov.sg API covering the paths that matter: a dataset that resolves, one that 404s, an
endpoint that makes you poll before it hands over a URL, and one that 503s before recovering.
Those tests check the script. They say nothing about whether the IDs are live, and the test
module says so at the top so a green run is not mistaken for a passed gate.

What was deliberately not done. No placeholder CSVs were written into `data/raw`. An empty
`data/raw` is an honest record of a blocked gate. Files with plausible-looking contents would
propagate into the fits, and the never-invent-a-number rule exists for exactly this moment.

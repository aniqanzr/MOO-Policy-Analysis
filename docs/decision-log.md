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

## 2026-08-31. No credential in the repo or the environment, DataMall deferred

`data/raw/README.md` was going to tell future sessions to put an LTA DataMall account key in a
`.env` file. That is wrong for this setup and the instruction was removed before it could be
followed.

Three storage options were on the table and all three leak. A committed `.env` publishes the key
the moment the repo goes public, which it will. An uncommitted `.env` does not survive between
sessions, because the build runs in Claude Code on the web where there is no durable local
filesystem, so the only way to make one persist is to commit it. A cloud environment variable is
visible to anyone using the environment, so it is not private either.

Decided: no credential goes in the repo or the environment at all. A source that needs an account
key is deferred rather than authenticated. `src/ingest/fetch.py` reads no environment variable and
touches only open endpoints. `.env` stays in `.gitignore` as a safety net against an accidental
commit, which is not the same as permission to create one. The rule is written into `CLAUDE.md`
so it binds future sessions, and stage 0 in `docs/BUILD_SEQUENCE.md` no longer reads as though a
credential file is expected.

DataMall static data, MVP01 and MVP02, is the one section 8 source affected. It is marked
`deferred` in `src/ingest/sources.py`. Nothing currently depends on it: every other section 8
source is open, and the VQS population and new registration series cover the accumulator's
inputs. Revalidation counts only become load-bearing if stage 7 shows the accumulator cannot
reproduce the published population series without them, which is A-04's falsification test.

Alternative considered: keep the DataMall pull and have each session paste a key at runtime. Not
taken. It makes the pipeline non-reproducible from a clean clone, which is the thing raw data is
committed to preserve, and it puts a live key one careless commit away from a public repo. If the
files turn out to be needed they get downloaded by hand through a browser and committed as data,
which reproduces cleanly and involves no key.

## 2026-08-31. `src/ingest` added to the section 7 layout

Section 7 does not name an ingestion package. Added `src/ingest` with `sources.py`, the section 8
list in machine-readable form, and `fetch.py`, the pull script stage 2 asks for.

Alternative considered: a single script at the repo root, or putting the pull inside `src/fit`
where the data is first consumed. Rejected because the source list is referenced by the pull
script, by `data/raw/README.md` and by stage 4's manual downloads, and one file it can drift away
from is better than three. `sources.py` holds no coefficients and no functional forms, so it does
not blur the boundary section 7 draws between the packages.

## 2026-08-31. Stage 2 gate not passed: every source host is blocked at the egress proxy

The pull script is written and the source list is complete, but not one dataset id has been
verified to resolve and no file has been downloaded. Every host in section 8 is refused at the
network egress proxy with a 403 on CONNECT: `data.gov.sg`, `www.data.gov.sg`,
`api-production.data.gov.sg`, `api-open.data.gov.sg`, `tablebuilder.singstat.gov.sg`,
`www.lta.gov.sg`, `www.mof.gov.sg` and `datamall2.mytransport.sg`. Both the shell and the
fetch tool are refused, so this is the environment's policy rather than a client problem, and
the proxy documentation says not to route around a policy denial.

Recorded rather than worked around. `python -m src.ingest.fetch --check-only` reproduces it and
names each failure. Stage 2's gate is knowing exactly what you have, and right now the answer is
nothing, so stages 3 and 4 do not start. The failed run's `manifest.json` was deleted rather than
committed: a manifest is a record of what was retrieved, and committing one full of proxy errors
would put a false state in a clean clone.

Section 8 warns that ids and coverage change, so the ids are carried forward as unverified. If
one has moved, that surfaces on the first successful run and gets logged then.

## 2026-09-04. Stage 3 reconciles against SingStat M130571, with the MOF PDF as the check

Section 8 names the MOF Analysis of Revenue and Expenditure as the reconciliation target. It is
a PDF. A-17 found the same line published as SingStat table M130571 series 1.2.1, annual, in
millions of dollars, sourced to the Accountant-General's Department, and warned that A-10
should not be run against a target that had itself only been assumed to match.

Decided: pull M130571 as the target, and use the MOF document for the spot check rather than as
the source. `src/ingest/pull_revenue.py` writes `data/raw/vehicle-quota-premiums-annual.csv`
and a metadata sidecar. `www.singaporebudget.gov.sg` turned out to be reachable now, where
stage 2 found it blocked, so the check ran in this session instead of waiting on a human. Table
2.1 of the Review of FY2025 gives 6.38 billion for FY2024 against SingStat's 6379.2 million.
The PDF is committed and the comparison is a test.

Alternative considered: parse the MOF PDF as the target and skip SingStat. Rejected. The PDF is
one financial year per document, so a series means a document per year and a parser that breaks
whenever the layout changes. The machine-readable series reproduces from a clean clone and the
PDF still does the job that only it can do, which is being a second publication to check
against.

Cost of the choice: the check covers one year. If AGD and MOF ever diverge on an earlier year,
this will not notice. A-20 is a reason to think the early years deserve their own look.

## 2026-09-04. The actual-versus-estimate cutoff is read from the footnote, not hardcoded

M130571 publishes FY1997 to FY2026 in one row. FY2026 is budgeted, FY2025 is revised, and
everything up to FY2024 is actual. Reconciling against an estimate measures the estimate.

Decided: `src/model/revenue.py` reads the sentence "Data up to FY2024 are actual figures" out of
the committed table footnote and refuses any later year, with the reason in the error. The pull
script fails loudly if that sentence ever stops appearing, so the two cannot drift apart
silently.

Alternative considered: a `LATEST_ACTUAL_FY = 2024` constant with a comment. Rejected because it
goes stale in March every year, silently, and the failure is a reconciliation against a budget
estimate that looks like a result.

## 2026-09-04. Revenue is computed from the wide table, and both bases are reported

Two choices inside the stage 3 arithmetic, both with a defensible alternative.

Source. Quota, successful bids and premium come from `quota-premium-monthly.csv` rather than
`coe-bidding-results.csv`. A-12 found two conflicting values and settled the wide table as the
reference, and the wide table also reaches back to 2002Feb where the long table starts at
2010-01. The alternative, the long table, is the more convenient shape and is what section 8
calls the spine of the reconciliation. Taking it would have imported a 23-fold error in the
January 2010 Category D premium.

Basis. Section 4.4 specifies quota times premium. What was actually paid is successful bids
times premium, since an undersubscribed exercise issues fewer COEs than it releases. Both are
computed and both are reported. The gap is 1.4 percent in FY2024, so the choice does not matter
for the gate, and reporting both costs nothing and makes the definition explicit.

## 2026-09-04. Stage 3 fails its gate, and the residual is recorded rather than closed

Computed revenue is 79.3 percent of the published line for FY2024. The build sequence says a
failure here is a pipeline bug. Four candidate bugs were checked and ruled out: a missing
category, fiscal versus calendar misalignment, the suspended 2020 exercises, and the source
defects in A-12 and A-13. The shortfall survives all four, is one-signed from FY2011 onward,
and is not sensitive to the choice of basis.

Decided: record the residual and what it most likely is, rather than adding a term to close it.
A renewal or taxi volume that makes the numbers agree would be a fitted plug, and this project
does not put an invented number in a config file and call it calibration. A-19 holds the
explanation and its falsification test, A-10 says what the shortfall costs the model, and O3 is
labelled bid revenue rather than government revenue everywhere it appears.

Alternative considered: proceeding as though the gate passed on the grounds that 79 percent is
close enough for a demonstration. Rejected. The gate exists to catch exactly this before
anything is built on top of it, and the honest version is more interesting than the clean one.

Second alternative considered: stopping the build here until renewal counts are obtained. Not
taken. The counts sit behind LTA DataMall, which needs an account key and is deferred under the
no-credential rule, and A-04 already needs the same files for the accumulator at stage 7. If
they get downloaded by hand for that, this row is answerable at the same time. Blocking week
one on a manual download that stage 7 will force anyway costs more than it buys.

## 2026-09-04. Stage 3 code sits in src/model, the gate sits in tests

Section 7 puts the revenue reconciliation under `/tests`. The arithmetic it runs on is O3,
total premium collected, which section 7 puts under `/src/model`.

Decided: split them. `src/model/revenue.py` computes revenue from the bidding record and
compares it against the published line, and is runnable so the numbers can be read without
running pytest. `tests/test_revenue_reconciliation.py` is the gate, and pins both the result
and the four pipeline checks that make the result mean anything.

Alternative considered: putting the whole thing in `tests/`, which is what section 7 says.
Rejected because O3 needs this arithmetic at stage 10 and importing it from the test package
would be worse. A new `src/validate` package was also considered and rejected: section 7 fixes
the layout and one more package for one file is not worth the drift.


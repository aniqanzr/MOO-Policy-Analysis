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

## 2026-08-31. Stage 2 pulls the portal's own CSV, not the datastore API

Section 8 says the datastore search API makes pulls scriptable, which is true, but it is not
what `src/ingest/pull_datagov.py` saves. It calls `initiate-download` and `poll-download` on
`api-open.data.gov.sg` and stores the CSV those hand back, which is the same file a person gets
by clicking Download on the portal.

The reason is provenance. Stage 3 reconciles computed revenue against a published government
figure, and if that fails the first question is whether the ingestion is faithful. Bytes that
match the published file answer it. A table reassembled from paginated JSON, with column order
and value formatting chosen by this code, does not.

The datastore path is kept as a fallback and used automatically if the download endpoints fail,
since they sit on a different host and hand out short-lived S3 links, either of which a network
policy can block while still allowing the datastore. Which path produced a file is recorded per
file in `data/raw/manifest.json`, because a reconstruction and a published file should not be
indistinguishable after the fact.

Alternative considered: datastore pagination only, which is simpler and one host instead of
three. Rejected for the provenance reason above. Two independent pulls produced identical
checksums on all eight files, so the recorded sha256 is worth comparing against on a re-pull.

## 2026-08-31. Section 8 coverage claims are encoded, not just read

`src/ingest/sources.py` carries what section 8 claims about each source's coverage as a field,
and the pull script checks the pulled file against it and prints the mismatches.

This was going to be a paragraph in a report. Making it a check means the next re-pull catches
a coverage change instead of relying on someone noticing. It found the thing it was written to
find: section 8 says the COE bidding results run from April 2002 and the file starts at
2010-01.

That date was not invented. It is when open bidding fully replaced closed bidding, which the
SingStat footnote for the same table states. Someone recorded the regime start as the dataset
start during the day one scan. Section 8 now carries the file's actual coverage and A-11 carries
the regime date, which is where it belonged.

## 2026-08-31. The two COE sources are cross-checked, and the wide one wins

`src/ingest/crosscheck_coe.py` compares every overlapping value between the two sources section
8 lists for COE bidding. 7,840 values, 152 disagreements, of which 150 are the same number
written two ways.

The two real conflicts both sit in `coe-bidding-results` and both repeat the value from the row
above. `quota-premium-monthly` is taken as the reference, on evidence rather than preference:
its five category quotas sum to its own published total for the exercise in question and the
long table's do not. The script prints that sum so the reasoning is visible rather than
asserted.

Alternative considered: correcting the two values in `data/raw` and moving on. Rejected. Raw
means raw, and a silent edit to a committed download is exactly the kind of thing that is
impossible to find six weeks later. The correction belongs downstream where it is visible in
the code and the diff.

Alternative also considered: dropping the long table and using only the wide one, which covers
2002 onward and has fewer defects. Not taken because the long table is the tidier shape and
extends one month further, and because two sources that can be checked against each other are
worth more than one that cannot.

## 2026-08-31. SingStat metadata is pulled and committed alongside the data

`src/ingest/pull_singstat.py` fetches TableBuilder metadata for the four section 8 sources that
are republished SingStat tables, and commits it to `data/raw/singstat-metadata.json`.

data.gov.sg serves the numbers without the units or the footnotes. Neither is recoverable from
the CSV: the public roads file gives 10,265 for 2025 and says nothing about what is counted.
The working rules say never invent a number, and reading a unit off a magnitude is a soft way
of doing exactly that. A-15 was opened on that basis and closed by the `uoM` field this script
saves.

It paid for itself beyond the unit. The same pull produced primary-source confirmation of four
A-11 break dates, the definition of prevailing quota premium that A-04 needs, and the fact that
the data.gov.sg republications lag their originals by up to six months.

Alternative considered: recording the unit by hand in the assumptions register with a link.
Rejected because a committed artifact survives and is re-checkable, and because the metadata
turned out to carry a good deal more than the one field it was fetched for.

## 2026-08-31. Two discovered sources are pulled as metadata only, not adopted

SingStat publishes a monthly deregistration series (M650291) and the Vehicle Quota Premiums
revenue line (M130571). Section 8 assumes the first does not exist and sources the second from
a PDF. Between them they remove the stage 4 bottleneck and unblock stage 3.

Only their metadata is committed. No series values are pulled and nothing reads them.

Adding a data source to section 8 changes what stages 3 and 4 do, and stage 2 was told to stop
at its gate. The evidence that these sources exist is committed so the decision can be made
with the files in hand, and the decision itself is left alone.

Alternative considered: pulling both series now, on the grounds that they are obviously wanted
and the cost is a minute. Rejected. The point of a gate is that discoveries which look
obviously good are exactly the ones that should stop at it. A-16 also lists two open questions
about the deregistration series that decide whether it replaces the Annex A extraction or only
cross-checks it, and neither is answered yet.

## 2026-08-31. `src/ingest` added to the layout in section 7

Section 7 lists `fit`, `model`, `optimise` and `export` under `src`. The pull scripts are none
of those. They are added as `src/ingest`, with the package docstring saying that nothing in it
cleans or interprets anything.

Alternative considered: a top-level `scripts/` directory, which is the usual home for
run-once tooling. Rejected because these are not run-once. The manifest exists so the pull can
be repeated and compared, and A-12 has to be re-run after any re-pull. Alternative also
considered: putting them in `src/fit`, which is where the data is consumed. Rejected because
ingestion and fitting failing for the same reason would then be indistinguishable.

The architecture is unchanged. Python still computes offline and writes JSON, and there is
still no server.

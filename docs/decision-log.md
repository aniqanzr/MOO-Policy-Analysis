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

## 2026-08-31. Both discovered sources adopted into section 8

M650291 becomes the primary source for deregistrations and M130571 the primary target for the
A-10 revenue reconciliation. Section 8 carries both, and the two claims they contradict are
struck from it.

Adoption of M650291 was made conditional on reconciling against Annex A first, and the
condition has been met rather than deferred. Four consecutive quarters straddling February
2023, two under each regime, twenty comparisons, all exact.

What the reconciliation actually settled is narrower than the headline. The published series is
Annex A row B1, gross deregistrations. It is not the effective figure net of guaranteed
deregistrations that the formula has used since August 2023, because that netting row is
constructed inside Annex A and published nowhere. So stage 4 drops the bulk extraction for the
series and keeps Annex A for rows B2 and C4, the growth allowance and the named adjustments.

The gap between gross and net is currently 1 vehicle in 44,612. That is not a reason to ignore
it. B2 counts five-year non-extendable COEs, first issued May 2023, so it grows as they near
expiry. Recorded in A-16 as a condition with an expiry date rather than as a settled fact.

Alternative considered: adopting M650291 outright on the strength of the exact match and
dropping Annex A from stage 4 entirely. Rejected because the match is on B1, and B1 is not what
the formula consumes. An exact reconciliation on the wrong quantity is more dangerous than an
approximate one on the right quantity, because nothing downstream would ever flag it.

## 2026-08-31. Annex A reference values are transcribed into code, with their row labels

`src/ingest/annexa.py` carries the B1 figures from four annexes as data, each with the row
label and the window that row states, beside the committed PDF it came from.

Transcribing numbers out of a PDF by hand is exactly what the never-invent-a-number rule is
about, so the transcription is checked rather than trusted: every quarter's four category
figures sum to the total that same annex prints, independently, and the cross-check then
compares all of it against a series pulled from a different agency.

Alternative considered: parsing the PDFs programmatically, which removes the transcription step
altogether. Rejected for now on dependency grounds, since no PDF library is in the stack and
adding one to read four files that are already committed buys little. If stage 4 needs many
more quarters, that is the point to add `pypdf` and log it.

## 2026-08-31. Reference values kept separate from model inputs

The Annex A figures in `src/ingest/annexa.py` are test fixtures. Nothing in `src/model` or
`src/fit` reads that module, and the docstring says so.

Worth stating because the file looks like a data source and is not one. Its numbers exist to
falsify a claim about another series. If a coefficient ever needs one of them, it should come
from the committed PDF through a documented extraction, not by importing a test fixture.

## 2026-08-31. The quota a quarter ran on is the later annex's figure

A-19 records that a quarter's published quota gets restated. The May 2023 annex gives 9,575 for
its own quarter and the August 2023 annex gives 10,431 for the same one, the difference being a
cut-and-fill injection made after the first annex went out.

Decision: take the ex-post figure, the later annex's comparison row, and say so wherever a
historical quota appears.

The alternative is defensible and is the reason this is logged rather than just done. The
ex-ante figure is what the policy actually decided at the time, and stage 13 recovers implied
weights from a policy position, so an argument exists for using what the decision-maker set
rather than what the quarter ended up with. Taking ex-post because the objectives are computed
from realised outcomes: realised revenue, realised population, realised congestion. Pairing an
ex-ante quota with ex-post objectives would be the actual error.

## 2026-08-31. DataMall deferred rather than chased

MVP01 and MVP02 are out of week one. Two independent reasons, either sufficient: the claim that
they carry COE revalidation counts has never been checked against the tables, and DataMall
needs an account key nobody has.

Recorded so it does not read as an open blocker. If A-04 turns out to need renewal counts that
nothing else supplies, it comes back at stage 4 with the content claim verified first.

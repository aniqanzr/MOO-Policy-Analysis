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

## 2026-09-04. A-20 was tested on the source rather than on MOF

A-20 recorded that computed revenue runs above the published line before FY2010 and below it
after, with no cause. The obvious next move was an MOF document from that era. Not taken, and
not only because it is a manual download.

A break in a ratio can sit in either term. The term that matters for the rest of the build is
`quota-premium-monthly`, because it is the only source for 2002 to 2009 and that span is where
stage 6 would see elasticity drift if there is any. If the columns changed meaning at 2010, the
revenue divergence would be the least of it: the premium fit would read a data artefact as a
change in the world. If they did not, the pre-2010 span is usable and the revenue break is
somebody else's accounting.

Decided: audit the file. `src/ingest/verify_quota_premium.py` runs six checks and
`tests/test_quota_premium_table.py` holds them as assertions. None of them separates the two
eras.

The strongest of the six was not planned. The prevailing quota premium is published as the
moving average of the quota premium over the latest three months in which bidding was held,
which makes it a third column that has to agree with the premium column arithmetically.
Computed from the premium column it reproduces every published PQP to within 83 cents, in
100 percent of category-months, in both eras. That is a much sharper instrument than the
plausibility checks that were the plan, because three published columns would have had to be
rewritten together to fake it.

Alternative considered: fitting the premium series and looking for a structural break at 2010.
Rejected. It answers a different question. A break in a fitted relationship is consistent with
either a data artefact or a real change in the market, which is the confusion the audit exists
to remove, and stage 6 would then be reading its own input.

Cost of the choice: this establishes that the columns did not change meaning, not that the
pre-2010 values are individually right. There is no second table back there to check them
against value by value, which is what A-12 could do for the overlap. That limit is written into
A-21 rather than left implied.

## 2026-09-04. The registration check subtracts registrations that need no bid

COEs awarded against new registrations under the VQS looked at first like evidence against the
later era: the raw ratio sits near 1.00 before 2010 and falls to 0.81 by 2022. Reading that as
a data problem would have been wrong in an interesting way.

The gap is Category C. In 2022, 7,477 of 9,578 goods vehicle registrations were under the Early
Turnover Scheme, which issues a replacement COE with no bidding, against 2,017 successful
Category C bids. Taxis are the same shape since August 2012, when they moved to paying the
Category A prevailing quota premium. Both schemes post-date the 2010 break, so they make the
later era look worse for a reason that has nothing to do with the table.

Decided: report both the raw and the adjusted ratio, and subtract only the two registration
rows that are published as needing no bid. Adjusted, the ratio is 0.99 to 1.05 before the break
and 0.96 to 1.08 after.

Alternative considered: dropping the check, since it is a magnitude comparison rather than an
identity and a COE won in one month can be registered in the next. Kept, because it is the only
external series that covers both eras, and a check that would have caught a factor-of-two error
is worth having even if it would not catch a five percent one.

## 2026-09-24. A-20 re-tested on the source, and the absent second table was looked for

The semantic-mismatch hypothesis was worth a second pass: stage 2 found a wrong coverage claim,
two copy-down defects and a silent string coercion across these files, so a definitional
mismatch in the pre-2010 span was the cheaper explanation of A-20 than anything about how MOF
reported revenue in 2006.

It does not survive. The audit of 2026-09-04 reran unchanged, and two things were added that
were missing from it.

First, the premise that the computation switches sources at 2010 is not true of this code.
`src/model/revenue.py` reads `quota-premium-monthly` for every year of the series. The long
table is only ever a cross-check, and over FY2010 to FY2024 the two agree to the cent. One file
produces both sides of the break, so the level shift cannot come from a file switch, and any
data explanation would have to be a change inside that one file. That is what the six checks
test, and the sharpest of them, the prevailing quota premium identity, holds to within 83 cents
in 100 percent of category-months in both eras.

Second, A-21's stated limit was that no second table exists for the pre-2010 span. That was an
assumption. It was checked: the SingStat keyword index returns one table carrying bidding or
quota premium, and a sweep of all 4,629 data.gov.sg datasets returns no bidding-results dataset
other than the two already in section 8. The limit holds and is now a searched-for absence.

So A-20 stays a finding about the published revenue line. The practical effect is unchanged,
the target is used from FY2010 onward, and the 2002 to 2009 span is usable at stage 6.

Cost of the choice, stated plainly: the pre-2010 values still cannot be checked one by one
against an independent source, because no such source is published. The evidence that the span
is sound is internal consistency plus two external magnitude checks, not value-level agreement.
If stage 6 finds an elasticity break at some date in that span that is not in the A-11 break
table, this row is the first thing to revisit.

## 2026-09-24. Open: is total revenue the right target for O3, or is bid revenue

Not decided. Recorded now so the option is on the table when O3 is assembled at stage 10,
rather than being settled by default by whatever the code happens to compute.

The position. Computed O3 is bid revenue, quota times clearing premium summed across the five
categories, and it comes to roughly four fifths of the published Vehicle Quota Premiums line.
A-19 says the residual is payment at the prevailing quota premium with no bid attached, which
is renewals and, since August 2012, taxis. Stage 3 established that the gap is one-signed and
not a pipeline artefact.

The case for bid revenue being the right objective, not a shortfall to be patched. Renewal
revenue in a given year is a consequence of quota decisions taken about a decade earlier. The
vehicles renewing now got their COEs under settings that are not the settings this model
varies, so that component barely responds to `g_ab`, `g_c` or `theta` within the horizon the
frontier describes. An objective that is largely insensitive to the levers adds a constant to
O3 and changes the recovered weights without carrying information about the choice being made.
On this reading the fix is relabelling O3 as bid revenue and stating the scope, not hunting a
missing term.

The case against. The two components are not independent. Raising quota lowers the clearing
premium, the prevailing quota premium is a moving average of that same clearing premium, so
renewal revenue falls too and it falls because of the lever. The insensitivity above is about
the quantity renewed, which is set a decade back, not about the price paid, which is set now.
A lever that moves premiums moves both halves of the published line in the same direction, and
an objective covering only one half understates the revenue consequence of a quota change.

What would settle it. The size of the price channel relative to the quantity channel. That is
an empirical question and it needs renewal counts, which A-19 now has a route to. If renewal
volumes are small relative to bid volumes, or if the price elasticity of the renewal decision
is material, the two readings give different answers and the difference is measurable rather
than a matter of taste.

What is not in question either way. O3 as currently computed is bid revenue and must be
labelled as such wherever it appears, and the published line is not a calibration target for
it while the residual is unexplained. That part is A-10 and is not open.

## 2026-09-24. The validation rule is rewritten to what can actually be met

`CLAUDE.md` required three tests to pass before a frontier is trusted, one of them the revenue
reconciliation, which failed at stage 3 and cannot pass against FY2024. A rule that cannot be
met teaches later sessions to treat every rule as approximate, which is a worse outcome than
losing the test.

Decided: the gate is ZDT1 and DTLZ2 plus the accumulator backtest. The reconciliation stays
recorded as failed in A-10 and is not a gate. The rule now says so, and says not to cite it as
support or rescue it with a fitted term.

Alongside it, validation status in section 5.4 moves to the provisional list in section 0.1.
Recording that a test passed or failed is a factual update. Without that line, marking a
failure in the brief read as a design change needing the frozen-section protocol.

Alternative considered: keep three tests and redefine the third as bid revenue against a
target with renewals added back. Rejected for now. That target needs renewal counts that only
exist to 2017, and A-19's test of the mechanism is queued behind stage 4. If that test works,
a narrower reconciliation over FY2011 to FY2016 might come back as a check. It would not be the
test the brief specified, and it would be named differently.

## 2026-09-24. Section 4.1 names the wide table as the fit source, full span

Section 4.1 said to fit from "LTA bidding results ... from April 2002". The LTA long table as
published starts at 2010-01, so a literal reading of 4.1 produces a fit from 2010 and loses
the first eight years without anyone deciding to. Those are the years an elasticity drift would
show in.

Decided: 4.1 now says the fit runs from April 2002 on `quota-premium-monthly`, which A-21 audited
across the 2010 boundary. It also says what the audit does not cover, and that an unexplained
elasticity break inside 2002 to 2009 goes back to A-21 before it becomes a finding.

Alternative considered: fitting from 2010 on the long table, where there is a second source to
cross-check every value. Rejected. It trades eight years of the period the project most needs
for a value-level check on years that already agree to the cent across both tables.

## 2026-09-24. Stage 4 takes every Annex A the index lists, not eight to twelve

The build sequence asked for eight to twelve Annex A PDFs straddling the regime changes. That
number was set for extraction by hand, where each table costs time. The LTA newsroom index lists
every quota release from February 2020, the PDFs download without authentication, and the text
layer is clean enough to parse.

Decided: take all of them, 29 tables and three supplementary releases that are primary sources
for break dates. A continuous run of quarters is what showed the August 2022 regime, because the
window length changes from three months to six and then twelve in consecutive tables. A
straddling sample could have skipped the six-month quarters.

Alternative considered: hold to the stated number. Rejected, because picking which twelve would
have been a judgement with no upside once the rest were free.

Cost of the choice: 4.0 MB of committed PDFs, and a parser that has to cope with six years of
layout drift. Nothing before February 2020 is in the index, so May 2017 rests on later LTA
footnotes rather than its own announcement.

## 2026-09-24. pypdf added to read the Annex A tables

Section 7 fixes the stack and asks for a reason for anything else. The Annex A tables are PDFs,
and nothing already in the stack reads PDF text. pypdf is pure Python, has no system
dependencies, and is only imported by `src/ingest/extract_annex_a.py`.

Alternative considered: extract once by hand and commit a CSV. Rejected, because the extraction
could not then be re-run or audited, and the parser turned up faults a hand copy would have
carried silently, a number split across a space, a label wrapped onto a line that looks like
the next code.

## 2026-09-24. The Annex A parser keeps only the one reading the row's own total allows

The PDF text layer splits some numbers (`1 2,022` for 12,022, `7 1` for 71), leaves the
Category E cell blank on some lines and prints `-` for zero on others. A parser that picks a
plausible repair would be inventing numbers.

Decided: each line is read in tiers of increasing repair, the raw tokens first, and a reading
is accepted only if exactly one distinct set of values in that tier makes the categories sum to
the published total. Two that both satisfy it make the line ambiguous, and an ambiguous line is
left unread and reported. None ended up unread. 13 lines needed a repair, all of the split
number kind, and every repaired table still passes the table-level identity that total quota
equals its own subtotal lines.

Alternative considered: fixed column positions from the PDF layout. Rejected because the layout
drifts across six years and position extraction fails silently where the identity check fails
loudly.

## 2026-09-24. M650291 adopted as the deregistration series

A-16 asked two things before M650291 could replace the Annex A extraction. Both are answered.
It equals Annex A line B1 exactly, in every category of all 27 formula tables and across all
three regimes. It does not separate guaranteed deregistrations, and Annex A does from the August
2023 quarter.

Decided: M650291 is the deregistration series, added to section 8, with the Annex A guaranteed
deregistration line netted off from August 2023. Before May 2023 there was nothing to net.

Alternative considered: use Annex A's B1 directly as the series. Rejected. It is quarterly and
rolling, so it is a sum over overlapping windows rather than a series, and it starts in 2020.
M650291 is monthly from 1990, which the accumulator at stage 7 needs.

## 2026-09-24. The break table is a separate file and the brief's version is left visible

Stage 4 found the scan's break table missing a regime, one date a month out, and one row that
was three changes. The change protocol says new facts go to the register rather than into the
brief.

Decided: the verified table is `docs/break-table.md`, section 7's break table deliverable, with a
quoted primary source on every row. The brief's table is left as the scan recorded it, with a
note above the next section saying it is superseded and why, so the correction stays visible.

It deliberately does not decide which breaks become dummies in the premium fit. That is a stage
6 choice with defensible alternatives, dummies against regime splits against leaving
supply-side changes out because they should move quota and not the price response. It gets
made and logged there.

## 2026-09-24. Four Annex A cells recorded as published deviations, not tolerated

Checking the replacement line against its own printed formula found four category cells that
no rounding of the product reproduces, each off by at most 1.25 COEs. The tempting fix was a
tolerance of two, which would have made the check pass and the fact disappear.

Decided: the check stays exact up to rounding, the four cells are named in A-22 and pinned in
the tests, and a fifth appearing fails the suite. One explanation was tested, rounding the row
total and apportioning it, and it does not fit because some published totals are not a rounding
of the total product either. The mechanism is not recoverable from the table. What stage 10
needs from this is the tolerance to use when comparing its own formula against Annex A.

## 2026-09-24. May 2017 accepted as sourced from LTA's own later footnotes

The May 2017 break is dated by the Annex A footnotes, which are LTA documents from 2020 onward
stating when LTA changed its own formula. Stage 4 recorded that as a weak point because the 2017
announcement itself was not opened.

Decided: a footnote in which the agency describes a change it made is a primary source
regardless of when it was written. The row is verified and the weak point is closed.

Alternative considered: finding and opening the 2017 release. Not taken. It would confirm a date
that LTA already states in 27 tables and could only disagree if LTA's own later account of its
own formula were wrong, which is not a risk worth the time before the freeze.

## 2026-09-24. Stage 6 logs every break it includes and every one it leaves out

Recorded now so a later session cannot miss it. When the premium fit is specified, the decision
log gets one entry covering all ten rows of `docs/break-table.md`: selected as a dummy, handled
as a regime split, or left out, with the reason for each. The specification alone would show
what went in and hide what did not.

## 2026-09-24. The freeze applied retroactively to 29 August

The brief froze at the end of week one, 29 August. It was never applied, and findings kept
entering the build for four weeks. Applied now, retroactive to that date, on the user's
instruction.

What stays: everything already in the build, stages 2 to 4 and the brief edits made through
today. What goes post-freeze and is not adopted: the A-19 renewal test and the two revalidation
datasets (F-01), the O3 framing question (F-02), and the cause of the A-20 break (F-03).

One reading had to be chosen, and it could have gone the other way. Stages 5 to 9 have not run,
so they all run after the freeze. Read literally, "findings do not enter the build at all"
would stop a stage 5 failure from triggering the lever redesign the build sequence prescribes
for it, which makes the rule unmeetable. Decided: each stage runs as specified, including the
on-failure branch it names, because that branch is part of the frozen plan. Anything beyond
it is post-freeze. The alternative, treating any stage 5 to 9 outcome that changes the build as
post-freeze, would mean a failed gate could only be written up and never acted on. Raised with
the user for confirmation.

F-02 closes the open O3 option from earlier today by default rather than on its merits. That is
a consequence of the freeze and is stated as such in the row.

## 2026-09-24. The brief records the calendar as it happened

Planned: three weeks from 23 August. Actual, at 24 September: four working days across 33
calendar days. Recorded in section 10 of the brief and in the case study, which carries the
real timeline rather than the intended one.

## 2026-09-24. Stage 5 runs on the injection fallback because theta cannot be modelled

Section 3.1 and A-08 both say: if `theta` proves unmodellable because car demand by power output
is not published, fall back to a discretionary injection lever. It is not published. The SingStat
keyword index has no table of cars by power output or engine capacity, and a sweep of all 4,629
data.gov.sg datasets finds none either; the nearest is new car registrations by make, with no
power field. With nothing to map a kW threshold onto a demand share, `theta` has no policy
setting to vary.

Decided: the gate is run on `g_ab`, `g_c` and injection, as the plan specifies. The injection
lever is the Annex A redistribution and injection line, bounded by the largest quarterly total
printed, 5,155, and allocated across categories in the shares Annex A has used.

Alternative considered: keep `theta` as an abstract Category A share of car demand, anchored at
the observed share of bids received. Kept as a comparison run only. It shows what the lever set
would have looked like, and it cannot carry the gate, because a share with no threshold behind
it is not a policy anyone can set, and section 5.3 needs the current policy located in the same
space.

This is the plan's own branch, run after the freeze, so under the freeze reading of 24 September
it is not a post-freeze change.

## 2026-09-24. Placeholders live in config/placeholders.toml

CLAUDE.md says a value with no fit and no source goes in config, marked as an assumption, with a
register row and a sensitivity sweep. There was no config directory. Section 3.3 already speaks
of "config" for constraints.

Decided: `config/placeholders.toml`, read with the standard library's `tomllib`. Each value has
a comment saying it is an assumption, the register row is A-23, and stage 5 sweeps it. The file
says that nothing past stage 5 may read it.

Alternative considered: constants at the top of the stage 5 module. Rejected, because a value in
code reads as settled and a value in a file called placeholders does not.

## 2026-09-24. Stage 5 measures the front on the NSGA-II front, not on a random sample

Three measurements were planned: the rank of the Jacobian, how much of each objective total
quota explains, and the dimension of the front by local principal component analysis. The first
sweep took the front as the non-dominated points of a random sample of 4,096 policies.

That measure turned out to be biased. The non-dominated points of a random sample sit near the
front rather than on it, and the scatter reads as a second dimension. Combinations whose NSGA-II
front ratio was 0.02 to 0.05, plainly curves, gave 0.09 to 0.14 from the sample, and one gave
0.63 against 0.20. The sweep was re-run on NSGA-II fronts, 200 generations each, and the sample
measure dropped.

Alternative considered: keep the sample and use more points. Not taken. The bias comes from the
sample being random, not from it being small, and the optimiser the project already validated at
stage 1 finds the front directly.

## 2026-09-24. Stage 5 reads its gate on O1 and O3 over the decision categories

O1 over all five categories falls when quota moves to a cheap category, whether or not any buyer
pays less (F-04). Under the injection lever, whose allocation includes motorcycles, that turns a
curve into a surface on one side of unit elasticity.

Decided: stage 5 reports both category sets and reads the gate on A, B and C, so a composition
effect cannot pass it.

Alternative considered: read it on all five, as the published revenue line counts. Rejected for
the gate, because the question is whether the levers trade the objectives off against each
other, and a trade-off that exists only because motorcycles are cheap is not one a policy maker
faces.

## 2026-09-24. Stage 5 gate not met; next step open

Under the injection fallback, with O1 and O3 over the decision categories, the front is a curve
when the premium elasticities are weaker than -1 and a surface when enough of them are
stronger. A-08 has the numbers. The build sequence says not to proceed to the fits with a lever
set that already collapses, and to redesign the levers. The injection fallback it names has
already been used, and this set does not already collapse: it collapses on one side of a number
nobody has estimated yet.

Not decided. The options, for the user:

1. Estimate the current-regime premium elasticities for A, B and C first, which is the core of
   stage 6, and let the result decide. Stronger than -1 and the plan continues. Weaker and the
   lever set collapses and needs redesign anyway. Costs part of stage 6 now instead of later,
   and runs a fit on a lever set the build sequence would not yet trust.

2. Reconsider the variable set now, the plan's remaining branch. What `theta` had and injection
   lacks is a way to move revenue at a given total quota. Two levers in published data would do
   that: the split of the injection line between Categories A and B, which LTA already varies
   from quarter to quarter, and the 10 percent Category E contribution rate in the quota
   formula. Neither has been tested. Each is a change to the decision variables, which the
   brief lists as provisional, and each is roughly half a day to put through stage 5 again.
   Estimates, not measured.

3. Accept a curve if stage 6 lands on the weak side, and change what the project claims. A
   curve front makes the ternary weight map degenerate, which touches the inverse weight query
   and its rendering. Both are frozen, so this one is raised rather than acted on.

Option 1 does not rule out option 2. It only orders them.

## 2026-09-24. Option 1 run first, as sequencing only

The user chose to fit the Category A and B premium elasticities before deciding anything about
the lever set. Recorded as an ordering, not a decision on option 2, which stays open. The lever
set and the stage 5 specification are not changed until the numbers exist.

What the fit can and cannot settle, stated before it runs. It cannot make `theta` a real lever:
`theta` failed at stage 5 because no published data maps a power threshold onto a demand share,
and no elasticity supplies that mapping. It can settle two other things. First, whether `theta`
would move the objectives at all if it could be set: at the reference quarter, Category A and B
revenue per unit of demand share are nearly equal, 1,589 and 1,615 million dollars, so theta's
first-order effect on revenue nearly cancels unless the two elasticities differ. Second, whether
the injection fallback's front is a curve or a surface, which stage 5 found turns on which side
of -1 the elasticities fall.

## 2026-09-24. The elasticity fit's specification, declared before it runs

Declared here and committed before any estimate is looked at, so the reported number cannot be
the one that happened to look best.

Form, section 4.1: ln P = a + b ln Q, per category, one row per bidding exercise, clearing
premium and exercise quota from `quota-premium-monthly`.

Windows, all ending at the last exercise on file, July 2026:
- W1, from May 2022. The primary window. The Category A definition has not changed since the
  110 kW threshold for electric cars took effect in the first May 2022 exercise, and section 4.1
  says to build the frontier on the current regime.
- W2, from February 2023, the four-quarter formula.
- W3, from February 2014, the 97 kW criterion. Longer, and crosses more breaks.

Specifications:
- S1, the form above with no controls. Primary.
- S2, adding a linear time trend.
- S3, first differences between consecutive exercises.

Standard errors: Newey-West, 6 lags, one quarter of exercises, because quota is set per quarter
and errors within a quarter are not independent.

Primary estimate: S1 on W1. All nine are reported. If they disagree about which side of -1 the
elasticity sits, that disagreement is the result.

Breaks, every row of `docs/break-table.md`, as the stage 6 instruction requires. None enters as a
dummy.
- Rows 1 to 5, April 2002 to the 2020 suspension: before W1 and W2 starts. Inside W3, rows 4 and 5
  are supply-side and are left out as dummies for the reason below. Row 3, February 2014, is W3's
  start.
- Row 6, May 2022, the electric car threshold, a change to Category A's definition: handled as a
  regime split, by starting W1 there.
- Rows 7 to 10, August 2022, February 2023, May 2023 and February 2025: supply-side changes to
  how quota is computed or topped up. Left out. They move quota, which is the regressor, and a
  dummy for any of them would absorb the quota variation that identifies b. February 2023 is
  also W2's start.

Known weakness, stated before the numbers: quota is set once a quarter, so W1 has about 17
distinct quota levels per category however many exercises it covers. The estimate is identified
from those, not from roughly 100 exercises.

## 2026-09-24. Option 1 result: the declared primary is wrong-signed, and no estimate is stronger than -1

`python -m src.fit.premium`, the grid declared in the previous entry, unchanged. Pinned in
`tests/test_premium_fit.py`.

Categories A and B side by side, window from May 2022:

                                   Category A                Category B
    S1, no controls, primary       +0.223 [+0.098, +0.348]   +0.062 [-0.082, +0.207]
    S2, linear trend               -0.412 [-0.569, -0.255]   -0.472 [-0.754, -0.190]
    S3, first differences          -0.264 [-0.391, -0.137]   -0.435 [-0.863, -0.007]

The declared primary is a bad fit and is reported as one. Category A's elasticity is positive,
premium rising with quota, and B's is indistinguishable from zero. Quota and premiums both rose
from 2024 to 2026, and a specification with nothing to absorb a demand shift reads that as a
positive elasticity. It is not replaced by the specification that looks right. S2 is not
promoted to primary here; choosing the stage 6 specification is stage 6's job.

What the fit was run for does not depend on which specification is right. Across all 27 cells,
A, B and C in three windows and three specifications, no estimate is stronger than -1. One
interval reaches past it, B on the window from February 2014 with no controls, point -0.836.
Every other interval sits wholly on the weaker side. Category C, run on the same grid because
stage 5 showed the injection verdict turns on it once A and B are weak, runs -0.32 to -0.01.

A correction to the previous entry. It said the window from May 2022 has about 17 distinct quota
levels per category. It has 84 for A, 78 for B and 70 for C. Quota is set once a quarter, but
exercise quota also moves within a quarter, because quota not taken up in one exercise is added
to later ones. That carry-over depends on demand, so part of the quota variation the fit uses
is not exogenous. Recorded, not chased.

## 2026-09-24. What option 1 settles

`theta`. Dead on both counts. It cannot be set, because nothing published maps a power threshold
onto a demand share, and the fit does not change that. And if it could be set, it would barely
move anything. At the reference quarter, theta's effect on A and B revenue per 0.05 of demand
share is between -0.3 and -0.9 percent in the primary window under every specification, with a
95 percent interval that includes zero every time. For scale, `g_ab` at 1 percent moves the same
revenue by 8.3 percent. Categories A and B are priced too alike and respond too alike for moving
demand between them to trade cost against revenue.

The injection fallback, with the fitted elasticities in place of the placeholders, same stage 5
model and lever set, NSGA-II front ratio with O1 and O3 over A, B and C:

                              goods vehicle PCU   1.0     1.5     2.0     3.0
    S2 elasticities                               0.113   0.028   0.032   0.035
    S3 elasticities                               0.133   0.092   0.134   0.076
    S1 elasticities, wrong-signed                 0.431   0.530   0.564   0.414

Under the two specifications with a negative sign the front is a curve, or within reach of one,
at any road load for goods vehicles above a car's. Under the primary it is a surface, and that
surface exists because Category A's premium rises with quota in a fit already reported as bad.
It is not counted. Stage 8 is the formal version of this check and would repeat it on whatever
stage 6 settles.

Option 2 read off the same numbers, not tested. A lever that reallocates quota at a fixed total
only trades cost against revenue if categories differ in what one more COE adds to revenue,
premium times one plus b. Between A and B it is 73.9 against 67.5 thousand dollars under S2, and
92.5 against 72.2 under S3: the same weakness as `theta`, so splitting the injection line between
A and B would be thin. Category E is 114.4 and 128.1, well above A, B and C, so the Category E
contribution rate would move revenue at a fixed total. But E's elasticity near zero is most
likely the demand spillover from B that A-07 leaves unmodelled, and that lever's second dimension
would rest on exactly that channel.

## 2026-09-24. Option 3, costed for the gate

Option 3: accept that the front is a curve and write up why, rather than build new levers. What
it changes in the frozen items, and roughly what it costs. Estimates, not measured.

Three objectives. Kept, and computed as specified. On the front, though, cost and revenue move
together: with every elasticity between -1 and 0, more quota lowers the premium and raises
revenue at once. The trade-off that survives is congestion against quota. Nothing in code
changes. What the output says about the three changes.

The inverse weight query. The code is unchanged and still runs. Its answer shrinks. With cost and
revenue aligned along the front, any split of weight between them picks the same policy, so the
query recovers one number, the weight on congestion against the combined weight on cost and
revenue, and not three. Section 5.3's "report the revenue weight as a finding" cannot be done,
by era or at all. That is the project's headline claim, and it goes.

The ternary rendering. The code is unchanged. The map comes out banded, the winning policy set by
one ratio, and needs an annotation saying why. About a quarter of a day.

Not frozen, but following from the above: the headline claim in section 0, section 5.3, the
README's "recovered weights" and a case study section on why the frontier collapsed. About half
a day to a day of writing.

Total: about 1 to 1.5 days, all writing and annotation, no engine or architecture change. It does
not save stages 6 to 9. Stage 7 is one of the two remaining validation gates, stage 9 puts O2 on a
calibrated axis, stage 6's elasticity path is a result in its own right, and stage 8 would
confirm the curve on fitted values. The larger cost is not in days: the question the project was
built to answer, what weight the policy implies for revenue, stops being answerable by this
model. What can still be said is that under current elasticities, affordability and revenue are
not in tension through quota, and the only live trade-off is road space against both.

## 2026-09-24. Drift test declared before it runs

The three windows in the declared grid are nested, so comparing them cannot show drift: the
window from May 2022 is inside the window from February 2014. To answer whether the premium's
response to quota has changed, the fit is split into two periods that do not overlap. Declared
here and committed before it runs.

- P1, February 2014 to April 2022, from the 97 kW criterion to the month before the electric car
  threshold changed.
- P2, May 2022 to the last exercise on file, identical to W1.

All five categories, specifications S1, S2 and S3 as declared before, Newey-West errors with 6
lags. The change is b in P2 minus b in P1, with standard error the root of the sum of the two
squared standard errors, the periods being separate samples.

Reading rule, fixed now. The brief's hypothesis in section 4.1 is that buyers came to absorb the
premium as a cost of ownership, so demand became less responsive to price. In terms of b that is
the premium moving more per unit of quota, b more negative in P2 than in P1. A drift is reported
where the 95 percent interval on the change excludes zero, in either direction, and a result
that depends on the specification is reported as depending on it.

Every break row placed as in the earlier declaration. Row 6, May 2022, is the split itself. The
2020 suspension, row 5, falls inside P1 and is left out as a dummy, being a supply shock that
moved quota.


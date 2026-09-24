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


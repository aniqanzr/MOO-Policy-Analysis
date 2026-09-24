# Build sequence

Ordered stages with gates. A gate is a point where you stop, look at the result, and decide
whether to continue. Several of these can kill or reshape the project, and they are ordered so
the cheapest fatal checks run first.

**The rule: do not proceed past a gate that failed.** Code will want to build the whole
pipeline in one pass. Stop it at each gate.

Week one covers stages 0 through 9. The brief freezes at the end of stage 9.

---

## Week one

### Stage 0. Setup
Repo, `docs/` in place with the brief, assumptions register and this file, `CLAUDE.md` at root,
dependencies installed, `.env` gitignored as a safety net. No credential is stored in the
repo or the environment; see the rule in `CLAUDE.md`.

**Gate:** none. Housekeeping.

---

### Stage 1. Optimiser validation
ZDT1 for two objectives, DTLZ2 for three. Compare generated points against the analytically
known fronts, report the error, commit as tests.

**Why first.** It needs no COE data at all, so it has zero dependencies and runs in minutes.
More importantly, doing it now means that when something looks wrong in week two, you already
know the optimiser is not the cause. Debugging a suspect frontier without this is guesswork.

**Gate:** both benchmarks reproduce their known fronts within a reported tolerance.
**On failure:** the pymoo configuration is wrong. Fix before touching anything else.

---

### Stage 2. Ingestion
Verify every dataset ID in section 8 resolves. Write the pull script for the data.gov.sg
sources, save raw files to `/data/raw`, commit them. Produce a list of what could not be reached
automatically.

**Gate:** you know exactly what you have and exactly what you must download by hand.
**On failure:** a dataset ID has moved. Find the current one, update section 8, note it in the
decision log.

---

### Stage 3. Revenue reconciliation
Sum historical quota times premium across all five categories for several years and compare
against the MOF Vehicle Quota Premiums line. Align fiscal years first.

**Why this early.** It looks like a model test but it is not. It uses only raw published data,
so it needs nothing from the fits. What it actually checks is whether you have ingested and
understood the bidding results correctly. Running it now catches ingestion errors before
anything is built on top of them.

**Gate:** A-10. Computed revenue lands within a reasonable margin of the published figure.
**On failure:** a pipeline bug, not a finding about MOF. Common causes are missing categories,
fiscal versus calendar year misalignment, or double-counting the suspended 2020 exercises.

---

### Stage 4. Deregistration extraction and the break table
Pull eight to twelve Annex A PDFs straddling the regime changes plus recent quarters. Extract
deregistration counts. Verify each of the nine structural break dates against a primary source.

**Why here.** This is the week-one bottleneck. Deregistrations are the critical input to the
quota formula and there is no clean published series.

**Gate:** A-11, and you have a usable deregistration series.
**On failure:** if extraction proves painful, the honest fallback is backing deregistrations out
of the published quota and growth allowance. Do not construct a plausible series. This is the
exact moment the never-invent-a-number rule exists for.

---

### Stage 5. Structural collinearity pre-check
Implement the quota formula and the three objectives using **placeholder elasticities**, not
fitted ones. Sample the decision space. Look at whether the front is a surface or a curve.

**Why before the fits.** This is the cheapest possible answer to the biggest structural risk. If
the three levers push the objectives the same direction, the frontier collapses regardless of
how good the fits are. Placeholder values are enough to reveal that, and finding out here costs
an afternoon instead of a week.

**Gate:** A-08, provisionally. The front is a surface under plausible placeholder values.
**On failure:** redesign the levers now. Fall back to a discretionary injection lever in place of
`theta`, or reconsider the variable set entirely. Do not proceed to the fits with a lever set
that already collapses.

---

### Stage 6. The premium fits
Log-log per category, rolling window or time-varying elasticity, break dummies. Plot the
elasticity path. Compare specifications and report the comparison rather than the winner alone.

**Gate:** A-01. You know whether the elasticity is stable, and if not, what the current regime
looks like.
**On failure:** if no specification fits acceptably, that is a serious finding and it changes
what the project can claim. Stop and raise it rather than searching for a specification that
looks good.

---

### Stage 7. Accumulator and backtest
Population accumulator, run forward over the historical record, compare against the published
series. Handle renewals, five-year COEs and early deregistration.

**Gate:** A-04. The accumulator reproduces history.
**On failure:** the population model is wrong and the congestion objective is built on sand.

---

### Stage 8. Collinearity check, for real
Re-run stage 5 with the fitted values in place of placeholders.

**Gate:** A-08, confirmed.
**On failure:** same remedies as stage 5, but you now know it costs more to fix. This is why
stage 5 exists.

---

### Stage 9. Congestion calibration
Calibrate BPR against the annual speed series and lane-km capacity. Report confidence intervals
on the fitted exponent honestly.

**Why last in week one.** It is expected to be the weakest link, and everything else is more
informative per hour spent.

**Gate:** A-09, which will most likely resolve to accepted-as-limitation rather than verified.
**On failure:** this is an expected outcome, not a blocker. Record the limitation, give the
congestion parameters extra weight in the sensitivity sweep, and flag the axis in the UI.

---

### FREEZE
End of week one. The brief is now fixed. Everything found from here goes to the post-freeze
section of the assumptions register and becomes the limitations section of the case study.

Applied on 24 September 2026, retroactive to 29 August, with stages 5 to 9 still to run. How
they run under it is set out in "The freeze date" in `docs/PROJECT_BRIEF.md`.

### Critical path from 24 September 2026, after option 3
The front is a curve (A-08) and O2 is the only axis left trading against anything (A-09). The
order of what remains in week one changes. The stages themselves do not.

1. **Stage 7**, the accumulator backtest. A validation gate, and O2 is built on it.
2. **Stage 9**, congestion calibration. Moved ahead of everything optional because the recovered
   weight now depends directly on O2's scale. Its on-failure branch is unchanged, and a band is
   an acceptable output.
3. **Stage 6, the rest.** The break-dummy specification, with the breaks selected and left out
   reported in the log, and the elasticity path. The option 1 grid and the drift test already
   answer the part of A-01 that decided option 3.
4. **Stage 8**, confirmatory. The fitted elasticities were already run through the stage 5 check
   under option 1. Stage 8 re-runs it on the final stage 6 values. It is the first thing cut if
   time runs short.

Stage 13 changes with this. It recovers one ratio, congestion against cost and revenue
together, and reports it as a band from stage 14. It does not report a revenue weight, because
none can be separated. See section 5.3 of the brief.

---

## Week two

### Stage 10. Problem definition
Assemble the quota formula, objectives and constraints into the pymoo problem. Constraints stay
separate from dominance in the data structures.

### Stage 11. Front generation and cloud sampling
NSGA-II run, dense feasible-space sampling, retain the full cloud. Tag each sampled point as on
the front, dominated, or constraint-excluded.

### Stage 12. Weight simplex map
Grid-sample the simplex, record the winning front point for each weight vector. Detect and mark
concave-region points that win under no weight vector.

### Stage 13. Headline recovery
Locate the current policy position, recover the implied weight region, report the revenue weight.
Repeat per historical growth-rate regime and look for drift.

Amended 24 September 2026 under option 3: the revenue weight cannot be separated from the cost
weight on a curve. Recover the congestion weight against the other two combined, as a band.

### Stage 14. Sensitivity and export
Perturb fitted coefficients, regenerate repeatedly, produce bands. Extra attention on the
congestion parameters. Write all JSON artifacts.

**Gate:** by the end of week two the headline claim is either supported or it is not. If it is
not, week three writes that up rather than hiding it.

---

## Week three

### Stage 15. Frontend
Views in priority order: the space, the ternary map, the point inspector. Ship fewer views well
rather than three badly.

### Stage 16. Deploy

### Stage 17. Case study
Edit the running document into shape. The day one scan and the section 3.1 rebuild belong near
the front of it.

---

## Opening prompt for the session

> Read docs/PROJECT_BRIEF.md, docs/ASSUMPTIONS.md, docs/BUILD_SEQUENCE.md and CLAUDE.md.
> Start at stage 1 and stop at the stage 1 gate. Do not continue past it without me.

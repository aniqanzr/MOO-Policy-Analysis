# Working rules

Read `docs/PROJECT_BRIEF.md` and `docs/ASSUMPTIONS.md` before starting anything. This file is
the standing rules for every session.

## Change protocol

New information arrives constantly on this project. Route it by what it touches. Do not edit
the brief casually.

**Touches an assumption.** Update the row in `docs/ASSUMPTIONS.md`. Note what happened.
Continue. Do not touch the brief.

**Touches something provisional** (decision variables, a functional form, bound, constraint
value, coefficient, normalisation choice, frontend detail). Change it, append to
`docs/decision-log.md`, continue.

**Touches something frozen** (the argument, the COE scenario, NSGA-II, the inverse weight
query, static architecture, three objectives). Stop. Write down what changing it costs in
days. Raise it rather than acting on it.

**After the week one freeze date**, findings do not enter the build at all. They go in the
post-freeze section of `docs/ASSUMPTIONS.md` and become the limitations section of the case
study. This applies even when the finding is correct and the fix looks quick.

## Non-negotiable

**Never invent a number.** Every coefficient, parameter and constant either comes from fitted
data or a cited source. If neither exists, put it in config with a comment marking it an
assumption, add a row to the register, and include it in the sensitivity sweep. Do not
hardcode a plausible-looking value.

**Quota is computed, not chosen.** Implement the LTA formula as published in Annex A: growth
allowance, plus a quarterly slice of the rolling four-quarter deregistration average net of
guaranteed deregistrations, plus the named adjustments. The decision variables are the policy
parameters that feed it, never the quota itself. The 25 percent replacement term is arithmetic
converting annual to quarterly, not a policy rate, and must not be modelled as a lever.

**Never present a fitted relationship as a known one.** Anything downstream of a fit carries
that uncertainty and the output must show it. The congestion objective carries a stronger
caveat than the other two, because it is identified from roughly twenty annual observations
with very little variation in the volume-capacity ratio.

**Dominated and constraint-excluded are different things.** A dominated policy failed. A
constraint-excluded policy was ruled out by a value judgement. Separate in the data structures,
visually distinct in the UI. Collapsing them destroys the distinction the whole project rests
on.

**Validation before trust.** Three tests pass before any COE frontier is taken seriously:
ZDT1 and DTLZ2 against their analytic fronts, the population accumulator reproducing the
historical series, and computed revenue reconciling against the MOF Vehicle Quota Premiums
line. The reconciliation sums all five categories and aligns fiscal years first.

**Run the collinearity check early.** Assumption A-08. Sample the decision space and confirm
the front is a surface, not a curve. If the three levers turn out to push total quota the same
direction, the frontier collapses and the project has a problem that no amount of frontend work
fixes. Do this immediately after the fits, before building anything on top.

**Do not assert the revenue-motive claim.** No official statement frames COE as a revenue
instrument, and this was searched for specifically. The documented purpose from 1990 through
2025 is vehicle population allocation under land scarcity. Ministers have described what the
revenue funds, which is not the same as describing what it is for. Present the revenue critique
as commentary, or leave it to the recovered weight. Also do not claim the revenue is
hypothecated or earmarked.

## Scope discipline

Do not add a database, a backend server, Category D as a decision dimension, user data upload,
or a fourth objective. Category E supply is derived mechanically and is not a decision
dimension either. If something looks like it needs one of these, stop and raise it.

No dependencies beyond pymoo, numpy, pandas, a fitting library and Plotly without a reason in
the decision log.

## Sourcing

Nothing enters the assumptions register on the authority of a research report or a summary.
Every claim carries a link to a primary source. Government documents where they exist, LTA
Annex A and MOT Parliamentary replies for policy mechanics, MOF Analysis of Revenue and
Expenditure for revenue figures.

Where a fact is currently backed only by secondary sources, the register says so and the row
stays medium confidence. Verify before that fact enters a regression as a dummy.

## Process

Commit in small pieces with real messages. Append to `docs/decision-log.md` whenever a choice
gets made that could have gone another way, including the option not taken and why. That log
is a deliverable.

Raw data downloads are committed so the pipeline reproduces from a clean clone.

When a modelling choice has a defensible alternative, name the alternative rather than silently
picking one.

## Writing

Any prose for this project, including the case study, README, tooltips and chart annotations:

- Plain direct sentences. No polish, no rhetorical wrap-ups, no closing flourishes.
- No dashes as punctuation.
- Do not oversell. The tool has real limitations and stating them is the point.
- Say what was done and what it cost. Skip adjectives about how powerful or innovative anything
  is.

## When something goes wrong

If a fit is bad, say so rather than trying specifications until one looks good. If the frontier
comes out degenerate, or the current policy sits far off it, that is a finding about the model
and gets reported as one. A negative result honestly reported is worth more here than a clean
picture that does not hold up.

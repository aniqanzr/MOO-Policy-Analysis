# Working rules

Read `docs/PROJECT_BRIEF.md` before starting anything. This file is the standing rules
that apply to every session.

## Non-negotiable

**Never invent a number.** Every coefficient, parameter and constant either comes from
fitted data or from a cited source. If neither exists, put it in the config file with a
comment marking it as an assumption and add it to the sensitivity sweep. Do not quietly
hardcode a plausible-looking value.

**Never present a fitted relationship as a known one.** Anything downstream of a fit
carries that uncertainty and the output must show it.

**Dominated and constraint-excluded are different things.** A dominated policy failed. A
constraint-excluded policy was ruled out by a value judgement. Keep them separate in the
data structures and visually distinct in the UI. Collapsing them destroys the distinction
the whole project rests on.

**Validation before trust.** The ZDT1 and DTLZ2 tests must pass before any COE frontier is
taken seriously. The population accumulator must reproduce the historical series before it
is used forward.

## Scope discipline

Do not add:

- A database. There is nothing to persist.
- A backend server. Everything is computed at build time and shipped as JSON.
- Categories D or E.
- User data upload.
- A fourth objective.

Do not add dependencies beyond pymoo, numpy, pandas, a fitting library and Plotly without
recording the reason in `docs/decision-log.md`.

If something looks like it needs one of the above, stop and raise it rather than building
it.

## Process

Commit in small pieces with real messages. Append to `docs/decision-log.md` whenever a
choice gets made that could have gone another way, including the option not taken and why.
That log is a deliverable, not housekeeping.

Raw data downloads are committed to the repo so the pipeline reproduces from a clean
clone.

When a modelling choice has a defensible alternative, name the alternative rather than
silently picking one.

## Writing

Any prose generated for this project, including the case study, README, tooltips and chart
annotations:

- Plain direct sentences. No polish, no rhetorical wrap-ups, no closing flourishes.
- No dashes as punctuation.
- Do not oversell. The tool has real limitations and stating them is the point.
- Say what was done and what it cost. Skip adjectives about how powerful or innovative
  anything is.

## When something goes wrong

If a fit is bad, say so rather than trying specifications until one looks good. If the
frontier comes out degenerate or the actual COE policy sits far off it, that is a finding
about the model and it gets reported as one. A negative result honestly reported is worth
more here than a clean picture that does not hold up.

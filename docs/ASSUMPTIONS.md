# Assumptions Register

Every parameter that is not fitted from data and not cited to a published source gets a
row here before it enters the model, per the non-negotiable rule in `CLAUDE.md`. Findings
that touch an existing row update that row in place; they do not touch `PROJECT_BRIEF.md`.

## How to read this table

- **Confidence** - high: primary source, verified. medium: secondary source, or a primary
  source with a single observation. low: no source yet, placeholder pending data.
- **Status** - active: currently used in the build. superseded: replaced, kept for the
  record. post-freeze: logged after the week one freeze date, does not enter the build.
- Every row must eventually cite a primary source per the sourcing rules in `CLAUDE.md`.
  A row backed only by a secondary source stays medium confidence until verified.

| ID | Assumption | Value | Source | Confidence | Status | Notes |
|----|------------|-------|--------|------------|--------|-------|
| A-08 | The three quota levers (q_a, q_b, q_c) do not all move total quota in the same direction across the sampled decision space, so the frontier is a surface rather than a curve. | not yet checked | n/a - to be established by sampling the decision space, see `PROJECT_BRIEF.md` section 6 | low | active | Collinearity check required before any downstream engine work, per the standing rule in `CLAUDE.md`. This row exists to hold the ID; fill in the result as soon as the check runs. |

## Post-freeze findings

Findings that arrive after the week one freeze date go here, not into the build, and
become the limitations section of the case study. See `CLAUDE.md`.

| ID | Finding | Date | Disposition |
|----|---------|------|-------------|
| | | | |

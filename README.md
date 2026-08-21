# Modeling Wicked Problems

A multi-objective optimisation model that recovers the implicit value weights behind a real
public policy, using Singapore's Certificate of Entitlement system as the case study.

## What this is

Public argument about policy usually treats disagreement as error. One side's preferred
outcome looks to the other like proof the system is broken. Often it is not. It is the same
problem with a different weighting.

This project takes that claim and makes it operational. It models a policy as a
multi-objective problem, generates the Pareto front, and then runs the question backwards:
given a policy someone actually chose, what would you have to value for that choice to be
optimal?

The goal is not to solve the problem. It is to move the argument from "who is right" to
"which trade-off do we choose," and to put a number on the distance between two positions.

## Why the COE

Singapore allocates the right to own a vehicle through a quota and a bidding system. The
public argument about it is exactly the confusion described above. A tradesman who needs a
van, a family that wants a car, and a commuter who wants clear roads all read the others'
preferred settings as evidence the system has failed. They are describing three different
points on the same frontier.

It is also tractable. The quota formula is published, the bidding results go back to 2002,
vehicle population and road speed data are open, and the revenue appears as a named line in
the national Budget. Almost nothing in the model has to be invented.

And it is live. The zero vehicle growth rate is legislated only until 31 January 2028, so
the parameter this model varies is one that comes up for decision inside two years.

## What it produces

Three objectives: cost of ownership, road congestion, and government revenue. Three policy
levers: the growth rate for cars, the growth rate for commercial vehicles, and the power
output threshold that separates the two car categories.

From those:

**The feasible space.** Every possible policy sampled and plotted at once, with the Pareto
front along its boundary. The dominated interior is what a genuinely failed policy looks
like, as distinct from one you simply disagree with.

**The preference map.** With three objectives the weight vector is a triangle, so the entire
space of possible value systems renders as a single ternary plot, coloured by which policy
each value system would choose.

**The recovered weights.** Locating the current policy on the front and reading off the
weight region that makes it optimal. The result is a ratio nobody published, inferred from
what was actually chosen.

## What it does not claim

This matters more than the feature list.

It does not predict COE prices, and is not built for that.

The recovered weights are what the policy implies under this specific model. They are not
anyone's internal reasoning.

The congestion objective is the weakest of the three. It is calibrated from roughly twenty
annual observations across a period when the vehicle population barely varied, which is close
to the worst case for identifying a volume-delay relationship. The uncertainty is reported
rather than hidden.

Most fundamentally, multi-objective optimisation assumes a fixed mapping from decisions to
outcomes. Rittel and Webber's wicked problems do not have one, partly because intervening
changes the problem. There is good reason to think the COE altered the very demand behaviour
it was measuring. So this does not model a wicked problem. It forces one into a tame
formulation and tries to make every choice involved in that forcing visible and contestable.

## Status

Research and specification complete. Build in progress.

- [x] Scenario selection and scoping
- [x] Policy mechanism research and data source verification
- [x] Specification, assumptions register, build sequence
- [ ] Data pipeline and fitted models
- [ ] Front generation and preference mapping
- [ ] Frontend and deployment
- [ ] Case study writeup

## Documentation

The reasoning behind this project is a deliverable, not scaffolding.

| Document | What it covers |
|---|---|
| [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) | Full specification, model design, data sources, and what may not be claimed |
| [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) | Every belief the model rests on, with a status and a falsification condition |
| [`docs/BUILD_SEQUENCE.md`](docs/BUILD_SEQUENCE.md) | Ordered stages with gates, cheapest fatal checks first |
| [`docs/decision-log.md`](docs/decision-log.md) | Choices made, alternatives rejected, and why |
| [`docs/case-study.md`](docs/case-study.md) | The writeup, including what the research overturned |

The assumptions register is the load-bearing one. An early version of this specification
treated the COE quota as a policy lever. It is not. It is computed by a published formula, and
finding that out on day one rebuilt the core of the model. That rebuild is documented rather
than quietly corrected.

## Stack

Python with pymoo for the optimisation, pandas and statsmodels for the fitted relationships,
Plotly for the visualisation. The frontier and preference map are computed offline and shipped
as static JSON, so the deployed site needs no backend and no database.

## Data

All sources are Singapore government open data: LTA bidding results and vehicle statistics via
data.gov.sg, LTA quarterly quota press releases for the formula and deregistration counts, and
Ministry of Finance revenue tables. Raw downloads are committed so the pipeline reproduces from
a clean clone.

## Companion paper

**"The Problem with your Solution"** argues that competing ideologies can be internally coherent
and mutually incommensurable, in Kuhn's sense, and that the first step is translation rather than
victory. This repository is the attempt to build the translator.

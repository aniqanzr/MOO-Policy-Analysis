# Modeling Wicked Problems: A Multi-Objective Optimization Approach
A Multi-Objective Optimization (MOO) model in Python that maps the trade-offs behind a real public policy and asks what a chosen setting implies about what was valued, using Singapore's Certificate of Entitlement (COE) system as the case study.

## Findings so far
Three, as of 24 September 2026. They come from a reduced-form fit of the premium on quota and an early check on the shape of the front, not from the finished model. Detail and caveats are in section 5.3 of the brief.

1. **The COE premium moves less than proportionally with quota.** In Categories A, B, C and E, in every window and specification tested between 2014 and 2026, a 1 percent rise in quota lowers the premium by less than 1 percent. In standard terms, demand is price-elastic. Motorcycles, Category D, are the exception since 2022. No change in the response over time can be distinguished.
2. **Affordability and revenue are not in tension through quota.** More quota lowers the premium and raises bid revenue at the same time. A framing that sets the two against each other does not hold under these estimates. This covers bid revenue only, not renewals.
3. **The front has no third dimension.** With cost and revenue moving together, the policies the available levers reach form a curve, road space against quota, not a surface. The lever that could have added a dimension cannot be modelled from published data.

The project was built to recover a revenue weight from the current policy. Finding 3 means that weight cannot be separated from the weight on affordability, so it is not recovered. What is still recovered is one ratio, congestion against the other two, and it depends heavily on the congestion objective, which is the least well identified of the three.

## The Goal
The purpose of this project is not to solve 'Wicked Problems', but to build a tool that translates conflicting perspectives into a shared, mathematical language.

Public argument about policy usually treats disagreement as error. One side's preferred outcome looks to the other like proof that the system is broken. Often it is not. It is the same problem with a different weighting.

By visualizing the exact, *data-driven trade-offs* between competing priorities, this framework aims to move public discourse from a "who is right/wrong?" debate to a more productive "which trade-off do we choose?" negotiation. The model then runs the question in reverse: given a policy that someone actually chose, what would you have to value for that choice to be the "correct" one?

### 1. The Thesis (Philosophical Paper)
* **Title:** "The Problem with your Solution"
* **Concept:** A philosophical analysis of why "wicked problems" cannot be solved by a single "correct" solution. It argues that competing ideologies are "incommensurable" (like Kuhn's paradigms) and that the first step to a solution is not "winning," but "translation".

### 2. The Proof (The Model)
* **Method:** A **Multi-Objective Optimization (MOO)** model built in Python using Pymoo.
* **Function:** The model acts as the "translator". It ingests conflicting objectives as mathematical functions and outputs a **Pareto front**, a visual graph showing all the "optimal" possible compromises. It then maps every possible set of value weights to the compromise that each one would choose.

## The Case Study: Singapore's COE
Singapore allocates the right to own a vehicle through a quota and a bidding system, and the public argument about it is exactly the confusion described above. A tradesman who needs a van, a family that wants a car, and a commuter who wants clear roads all read the others' preferred settings as evidence that the system has failed. They are describing three different points on the same Pareto front.

I picked it over the alternatives (public health, urban housing) for three reasons:
* **It is tractable.** The quota formula is published, bidding results go back to 2002, vehicle population and road speed data are open, and the revenue appears as a named line in the national Budget. Almost nothing in the model has to be invented.
* **It has not already been done.** The public health version would have reproduced a Pareto front that already exists in published economics literature. That is replication, not analysis.
* **It is live.** The zero vehicle growth rate is legislated only until 31 January 2028, so the parameter this model varies is one that comes up for a real decision inside two years.

## What the Model Produces
Three objectives (cost of ownership, road congestion, government revenue) against three policy levers (the growth rate for cars, the growth rate for commercial vehicles, and a third lever). The third was meant to be the power output threshold separating the two car categories. It cannot be modelled from published data, and the plan's fallback, a discretionary quota injection, is used instead.

* **The feasible space.** Every possible policy sampled and plotted at once, with the Pareto front along its boundary. The dominated interior is what a genuinely failed policy looks like, as opposed to one you simply disagree with. This distinction is the entire point of the project.
* **The preference map.** With three objectives the weight vector is a triangle, so the whole space of possible value systems renders as one ternary plot, colored by which policy each value system would pick. Because cost and revenue pick the same policies, the map comes out in bands rather than regions, and it is annotated to say so.
* **The recovered weight.** Locating the current policy on the front and reading off the weight that makes it optimal. With the front a curve, that is one ratio, congestion against cost and revenue together, reported as a band because it depends on how the congestion objective is calibrated.

## What I Am Not Claiming

* This does not predict COE prices and was not built to.
* The recovered weight is what the policy implies under this specific model. It is not anybody's internal reasoning.
* No Singapore minister has ever framed the COE as a revenue instrument (verified). The stated purpose from 1990 onward is vehicle population control under land scarcity, and the "revenue motive" reading is commentary. Revenue stays in the model as an objective. It was meant to be tested by its recovered weight, and on the current evidence that weight cannot be separated from affordability.
* The congestion objective is the weakest of the three, and it is now the only one that trades against anything. It is calibrated from roughly twenty annual observations over a period when the vehicle population barely moved, which makes the fitted exponent poorly identified. The uncertainty is reported rather than hidden.
* The premium fits are reduced form. Part of the quota within a quarter depends on demand, because unused quota carries forward.
* Computed bid revenue is 79 percent of the published revenue line for FY2024. The reconciliation failed and is reported as failed.
* Most importantly, MOO assumes a fixed mapping from decisions to outcomes, and wicked problems do not have one, partly because intervening changes the problem. There is good reason to think the COE altered the very demand behavior it was measuring. So this does not model a wicked problem. It forces one into a tame formulation, and tries to make every choice involved in that forcing visible and contestable.

## Project Status (Work in Progress)
This is an active, self-directed research project.

* [x] **Philosophy:** The philosophical paper is in the drafting stage.
* [x] **Scenario:** Locked to Singapore's COE, with the alternatives documented and rejected.
* [x] **Research:** Policy mechanism verified against primary sources, data sources confirmed live.
* [x] **Specification:** Brief, assumptions register and build sequence complete.
* [x] **Data:** Pipeline, deregistration series and break table.
* [ ] **Fits:** Premium response fitted and tested for drift. Accumulator backtest and congestion calibration to go.
* [ ] **Model:** Front generation and preference mapping.
* [ ] **Frontend:** Visualization and deployment.
* [ ] **Writeup:** Case study.

## Running It
Python 3.11.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Raw data downloads are committed, so the pipeline runs from a clean clone without fetching
anything. Layout follows section 7 of the brief: `src/fit` holds the fitted relationships,
`src/model` the quota formula, objectives and constraints, `src/optimise` the pymoo runs and
the weight simplex map, `src/export` the JSON writers, and `web` the static frontend that
reads that JSON.

## Documentation
The reasoning behind this project is a deliverable, not scaffolding.

* [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) - Full specification, model design, data sources, and what may not be claimed.
* [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) - Every belief the model rests on, with a status and a falsification condition.
* [`docs/BUILD_SEQUENCE.md`](docs/BUILD_SEQUENCE.md) - Ordered build stages with gates, cheapest fatal checks first.
* [`docs/decision-log.md`](docs/decision-log.md) - Choices made, alternatives rejected, and why.
* [`docs/case-study.md`](docs/case-study.md) - The writeup, including what the research overturned.

The assumptions register is the one that does the work. An early version of this specification treated the COE quota as a policy lever. It is not one. It is computed by a published formula, and finding that out on day one rebuilt the core of the model. I documented that rebuild instead of correcting it.

## Tech & Concepts
* **Core Tech:** Python, Pymoo, pandas and statsmodels for the fitted relationships, Plotly for visualization.
* **Architecture:** The front and the preference map are computed offline and shipped as static JSON, so the deployed site needs no backend and no database.
* **Data:** Singapore government open data. LTA bidding results and vehicle statistics via data.gov.sg, LTA quarterly quota press releases for the formula and deregistration counts, Ministry of Finance revenue tables. Raw downloads are committed so the pipeline reproduces from a clean clone.
* **Core Concepts:** Multi-Objective Optimization (MOO), Pareto efficiency, Decision Science, Public Policy Analysis, Perspectivism, Wicked Problems.

# Case study

A running document, edited into shape at stage 17.

## Timeline

Planned: three weeks from Sunday 23 August 2026. Scan and data and fits in week one, with the
brief frozen at the end of it on 29 August. The engine in week two. Frontend, deployment and
this write-up in week three, ending 12 September.

Actual: four working days across 33 calendar days, to Thursday 24 September.

| Date | Work |
|---|---|
| 23 August | Stage 0, setup. Stage 1, optimiser validated against ZDT1 and DTLZ2. |
| 31 August | Stage 2, ingestion. |
| 4 September | Stage 3, revenue reconciliation, which failed. Audit of the pre-2010 bidding data. |
| 24 September | Stage 3 follow-ups. Stage 4, deregistration series and break table. Freeze applied, retroactive to 29 August. Stage 5, which found the front is a curve on one side of unit elasticity. Premium fits, which put it on that side. Option 3 adopted. |
| 25 September | Stage 7, accumulator backtest, which failed and was accepted as a limitation. Stage 9, congestion calibration, which found nothing to calibrate. |

The freeze date passed with stage 2 not yet run and was not applied for four weeks. Findings
from those weeks entered the build when the plan said they should not have. Applied on 24
September, the freeze kept what was already built and moved everything else to the post-freeze
list below.

## Findings, from 24 September 2026

Three. Wording and caveats as in section 0 and section 5.3 of the brief.

1. The COE premium moves less than proportionally with quota in Categories A, B, C and E, in every
   window and specification tested from 2014. Demand is price-elastic. Category D is the
   exception since 2022. No change over time can be distinguished.
2. Because of that, more quota lowers the premium and raises bid revenue together. Affordability
   and revenue are not in tension through quota. Bid revenue only.
3. The front is a curve, road space against quota, not a surface. This was the risk stage 5 was
   built to catch, and it caught it. Reported as a result about the policy space the published
   levers reach.

What it cost the project. The headline claim was that the current policy implies a recoverable
weight on revenue. On a curve where cost and revenue move together, that weight cannot be
separated from the weight on cost. The inverse weight query now recovers one ratio, and that
ratio depends on the congestion objective, which the brief expected to be the weakest. The
amendment to the frozen items is logged as a post-freeze change.

Before this section names anyone who holds the framing in finding 2, it needs a primary source
showing them holding it.

## Limitations recorded so far

From the assumptions register. The full wording is there.

- The revenue reconciliation failed. Computed bid revenue is 79 percent of the published line
  for FY2024. A-10.
- O3 is bid revenue, not total revenue from the COE system. Whether it should be total revenue
  was left undecided by the freeze. F-02.
- The leading explanation of the revenue gap, renewals paid at the prevailing quota premium, is
  untested. Open data that could test it for 2006 to 2017 was found after the freeze. F-01.
- The published revenue line behaves differently before FY2010 and the reason is unknown. F-03.
- The 2002 to 2009 bidding data is internally consistent but cannot be checked value by value
  against a second source, because none is published. A-21.
- LTA's own quota arithmetic does not reproduce exactly from the inputs it prints, by at most
  1.25 COEs per category. A-22.
- The lever meant to reallocate demand between the two car categories, `theta`, could not be
  modelled, because demand by power output is not published. Under the fallback lever the
  three objectives only form a surface if the premium falls faster than quota rises, and the
  brief expected the opposite. A-08.
- The premium fits are reduced form. The specification with no controls is wrong-signed in the
  recent window and is reported as failed. Quota within a quarter partly depends on demand
  through carried-forward unused quota. A-01.
- The congestion objective, calibrated on about twenty annual observations, carries the only
  live trade-off. A-09.
- The accumulator, quota released in and deregistrations out, misses the 5-year change in vehicle
  stock by 2 to 3 percent at the median and up to 6.4 percent, against a tolerance of 1.26
  percent. The published flows themselves reconcile. Vehicles appear to enter outside the bidding.
  A-04, F-06.
- The congestion curve could not be calibrated. Against 22 years of annual peak-hour speeds, no
  declared fit identifies the BPR exponent, and in the main fits speed rises as vehicles per
  lane-km rise. O2's shape comes from assumed values, and O2 is the only axis that trades against
  anything. A-09.


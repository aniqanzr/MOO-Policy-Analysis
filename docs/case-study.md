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
| 24 September | Stage 3 follow-ups. Stage 4, deregistration series and break table. Freeze applied, retroactive to 29 August. |

The freeze date passed with stage 2 not yet run and was not applied for four weeks. Findings
from those weeks entered the build when the plan said they should not have. Applied on 24
September, the freeze kept what was already built and moved everything else to the post-freeze
list below.

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

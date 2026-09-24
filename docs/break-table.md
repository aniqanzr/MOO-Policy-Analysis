# Break table

The structural breaks the premium fit at stage 6 has to handle, each dated against a primary
source that is committed in this repo. Verified at stage 4 on 2026-09-24. This table supersedes
the one compiled during the day one scan in section 4.1 of the brief.

Three changes from the scan's version. One regime was missing, August 2022. One date was wrong,
the end of the 2020 quota return. One row was three changes rather than one, May 2023.

How to read the source column. `M651121` is the SingStat table footnote committed at
`data/raw/singstat-metadata.json`. A dated file name such as `2022-07-...` is an LTA release
under `data/raw/lta-annex-a/`, either its page text (`.txt`) or its Annex A (`.annex-a.pdf`).
Every quoted line below can be found in the named file.

---

## The table

| # | Effective | Break | Kind | Status |
|---|---|---|---|---|
| 1 | April 2002 exercise | Closed to open bidding. February and March 2002 ran one of each. Left-truncate here. | Auction mechanism | Verified |
| 2 | 6 August 2012 | Taxis stop bidding. New taxi COEs are drawn from Category E and paid at the Category A prevailing quota premium. | Category composition | Verified, date refined to the day |
| 3 | February 2014 exercise | Category A adds a 97kW maximum power criterion to the 1,600cc limit. | Category definition | Verified |
| 4 | May 2017 | Category D deregistrations stop feeding Category E. Category E receives 10 percent of A, B and C deregistrations. | Supply formula | Verified |
| 5 | April to June 2020 | Bidding suspended. The accumulated 19,490 COEs were returned over the 24 exercises from **July 2020 to June 2021**, one third in July to September 2020, two thirds after. | Supply shock | Verified, end month corrected |
| 6 | May 2022, first exercise | Category A threshold for fully electric cars raised from 97kW to 110kW. | Category definition | Verified |
| 7 | **1 August 2022** | **Quota based on a rolling two-quarter average of deregistrations, 50 percent of six months, replacing one quarter at 100 percent.** | Supply formula | **Added. Missing from the scan's table** |
| 8 | 1 February 2023 | Rolling four-quarter average, 25 percent of twelve months. | Supply formula | Verified |
| 9 | May 2023 | Three supply changes in one month, see note. Cut-and-fill starts from the **second** exercise of May 2023. | Supply formula | Verified, split into its parts |
| 10 | February 2025 | Discretionary injection of up to about 20,000 COEs over several years, announced October 2024. | Supply level | Verified |

---

## Sources and notes, row by row

**1. April 2002.** `M651121`: "February and March 2002 1st bidding refers to closed bidding
system, 2nd bidding refers to open bidding system. From April 2002 bidding exercise, the COE
Open Bidding System fully replaced the Closed Bidding System."

**2. August 2012.** `M651121`, series footnote on Category A: "From 6 Aug 2012 onwards, all taxis
pay for COEs based on the PQP of Category A." The Annex A tables date it the same way in two
wordings: "Taxis were moved from Cat A to Cat E from 6 Aug 2012" in the 14 tables to May 2023, and
"From 6 Aug 2012, COEs for new taxi registrations are drawn from Cat E" in the 13 from August
2023. Before that date a taxi operator could bid or pay the
prevailing quota premium, so taxis are partly inside the bidding data before the break and
wholly outside it after.

**3. February 2014.** `M651121`: "From Feb 2014 bidding exercise onwards, Category A will add a
new engine power criterion of up to 97kW to the existing engine capacity threshold of up to
1600cc."

**4. May 2017.** All 27 formula tables, `2020-01-...annex-a.pdf` to `2026-07-...annex-a.pdf`: "From May 2017, Cat E
receives 10% of the deregistrations from Cat A, B and C." and "From May 2017, Cat D
deregistrations no longer contribute to Cat E." This is LTA stating when LTA changed its own
formula, which makes it primary regardless of when it was written. The 2017 announcement was not
opened and does not need to be.

**5. April to June 2020.** `M651121`: "COE bidding exercises were suspended in the months of
April, May and June 2020". `2020-06-resumption-of-coe-bidding-exercises-from-6-july.txt`: "The
accumulated COE quota of 19,490 from the suspended bidding exercises from April to June will be
returned to the market over the next 12 months from July 2020 to June 2021", with "6,494 COEs
across all categories for the period from July to September 2020; and 12,996 COEs across all
categories for the period from October 2020 to June 2021."

The Annex A tables reconcile to that figure exactly. The return lines are 2,162 for July 2020,
4,332 for August and September, 1,441 for October, 4,332 for November to January, 4,333 for
February to April, and 2,890 for May and June 2021. They total 19,490. The scan's table said the
return ran to July 2021. It ran to June 2021.

**6. May 2022.** `2022-04-...may-2022-to-july-2022.txt`: "the Category A Maximum Power Output
threshold for electric cars will be revised from 97kW to 110kW ... This change will take effect
from the first COE bidding exercise in May 2022, which will take place from 4 to 6 May".

**7. August 2022, added.** `2022-07-...august-2022-to-october-2022.txt`: "With effect from 1
August 2022, the number of COEs available for bidding in each quarter will be based on a rolling
average of deregistrations over the last two quarters." The February 2023 release restates it.
The arithmetic shows it without the prose: the deregistration window in Annex A is three months
through the May 2022 quarter, six months for the August and November 2022 quarters, and twelve
from February 2023. `tests/test_annex_a.py` holds that. The scan recorded the move to four
quarters and missed the six-month step before it.

**8. February 2023.** `2023-01-...february-2023-to-april-2023.txt`: "With effect from 1 February
2023, the number of COEs available for bidding in each quarter will be the rolling average of
the number of vehicles deregistered over the previous four quarters."

**9. May 2023, three changes.** All from Annex A footnotes. The Early Turnover Scheme and
Category D changes first appear in `2023-04-...annex-a.pdf`, the May to July 2023 table.
Cut-and-fill first appears in `2023-07-...annex-a.pdf`, the August to October 2023 table, which
is also the first with a guaranteed deregistration line.

- Cut-and-fill: "From May 2023 2nd bidding exercise, guaranteed deregistrations with 5-year COEs
  which are due to expire in the next projected supply peak will be redistributed" (August and
  November 2023 Annexes). From February 2024 the wording drops "with 5-year COEs".
- Early Turnover Scheme: "From May 2023, the deduction for ETS registrations will be the rolling
  average of ETS registrations in the previous four quarters." Category C only.
- Category D: "Cat D COEs issued from 1st bidding exercise of May 2023 (inclusive), will be
  returned for bidding earlier than the current practice of the next quarter."

Cut-and-fill also produced two mid-quarter revisions that sit outside the regular quarterly
arithmetic. `2023-09-...txt`: 700 additional Category A COEs for August to October 2023, then 300
more for October, "drawing upon the same pool of COEs from guaranteed deregistration of cars
with 5-year non-extendable COEs". `2023-11-...annex-a.pdf`: an additional 1,614 for November 2023
to January 2024.

**10. February 2025.** `2024-10-injection-of-additional-coe-quota-...txt`: "LTA will progressively
inject up to about 20,000 additional COEs across the vehicle categories from February 2025, over
the next few years." The February 2025 Annex A footnote restates it, and its line C4 is where the
injection enters the arithmetic.

---

## Considered and not added as rows

**February 2018, growth rate to zero.** Annex A footnote: "The vehicle growth rate from Feb 2018
has been set at 0% per annum for Cat A, B and D, while that of Cat C will remain at 0.25% per
annum." Its stated end date changes across the tables: "until further review in 2020" in the three
2020 tables, "until Jan 2025" in the thirteen from November 2021 to November 2024, and "until Jan
2028" in the four from February 2025 to November 2025. The other seven word it differently and
were not needed for the date. This is a setting of `g_ab` and
`g_c`, the decision variables themselves, not a change in how the premium responds to quota. It
belongs to the growth-rate regime history stage 13 needs, not to the fit's break dummies.

**Pre-2002 dates.** A-11 carried the 1991 non-transferability change and the bid deposit history
at medium confidence. Both fall before the April 2002 left-truncation, so neither enters the fit
and neither was verified.

---

## What this table does not decide, and what stage 6 owes

Which breaks enter the premium fit as dummies, which as regime splits for the rolling
elasticity, and which are left out as supply-side changes that should move quota rather than
the price response. That is a stage 6 specification choice with defensible alternatives. The
Kind column is there to inform it, not to make it.

When stage 6 makes it, the decision log records every row of this table, not only the ones
chosen: which were selected as dummies, which were handled as regime splits, which were left
out, and the reason for each. A break left out of the specification without a log entry is a
decision nobody can see, and this table exists to prevent that.

# Assumptions register

Every belief about how COE actually works lives here, not in the brief. New facts update a
row. They do not edit `PROJECT_BRIEF.md`.

Each row needs a status and a falsification condition. If you cannot write what would prove
an assumption wrong, you do not understand it well enough to build on it.

Statuses: `unverified`, `verified`, `falsified`, `accepted-as-limitation`.

**Updated after the day one scan.** Three rows falsified, two resolved, three new rows added.

**Updated after the stage 2 pull, 2026-08-31.** Seven new rows, A-12 to A-18. Six are
falsifications, and mostly of things nobody had thought to doubt: that two official sources of
the same numbers agree, that a published file keeps its own formatting conventions, that a
dataset listed in section 8 is current, that a republication keeps up with its original. Two go
the other way and remove work rather than adding it, A-16 and A-17. A-05 and A-11 amended.
A-15 was opened and closed the same day.

**Updated after the stage 3 reconciliation, 2026-09-04.** A-10 ran and did not pass. Computed
revenue from the bidding record is 79 percent of the published Vehicle Quota Premiums line for
FY2024, the shortfall is one-signed from FY2011 onward, and the four pipeline causes the brief
tells you to suspect first were checked and ruled out. A-10 is rewritten, A-17's spot check is
done, and two rows are added: A-19 for what the residual is likely to be, A-20 for the years
where the published line and the bidding record disagree in the other direction.

**Updated after the A-20 source audit, 2026-09-04.** The pre-2010 break was tested against
`quota-premium-monthly` rather than against MOF. Six checks, none of which separates the two
eras, so the columns mean the same thing across 2010 and the 2002 to 2009 span is usable for
the stage 6 fits. A-21 is the new row and holds the evidence. A-20 keeps its status and now
says where the break is not.

**Updated 2026-09-24.** A-20 was re-tested on the source and the absent second table was
searched for rather than assumed. A-10 now says plainly that it is a failed validation, and
section 5.4 of the brief says the project runs on two validations rather than three. A-19 is
corrected: renewal counts are published openly after all, for 2006 to 2017, which makes the
mechanism testable without closing A-10.

**Updated after stage 4, 2026-09-24.** A-11 falsified as stated and corrected: the break table
missed the August 2022 two-quarter regime, dated the end of the 2020 quota return a month late,
and described May 2023 as one change rather than three. The verified table is
`docs/break-table.md`. A-16 resolved: M650291 is exactly the formula's deregistration term, and
guaranteed deregistrations come from Annex A. A-22 is new: Annex A's own arithmetic does not
reproduce exactly from its printed inputs, by at most 1.25 COEs.

**Freeze applied, 2026-09-24, retroactive to 29 August.** Findings after that date that were not
already in the build are post-freeze rows F-01 to F-03 at the end of this file: the A-19 renewal
test and its two datasets, the O3 framing question, and the cause of the A-20 break. None is
adopted. Stages 5 to 9 still run as specified. See "The freeze date" in the brief.

Everything below carries a source note. Where a source is secondary, that is stated and the
row is medium-confidence until a primary document is opened.

---

## Format

```
### A-nn. <the assumption, stated as a claim>
Status:       unverified | verified | falsified | accepted-as-limitation
Source:       where it came from
Falsified by: what evidence would kill it
Touches:      which section of the brief or which part of the code depends on it
Notes:        what happened when you checked
```

---

## Rows

### A-01. Quota released and clearing premium have a stable relationship over the sample
Status:       unverified
Source:       original brief assumption
Falsified by: rolling-window elasticity showing a significant trend or break
Touches:      4.1, the entire frontier
Notes:        Still the highest-risk row and still the first thing to test. The scan did
              improve the odds: the auction is uniform price, so every winner in a category
              pays the same clearing premium. That means the observed premium is a genuine
              market-clearing quantity rather than an average across heterogeneous payments,
              which is what makes a reduced-form quantity-price relationship defensible at all.
              It says nothing about whether the elasticity is stable over time.

### A-02. Quota is a policy lever that can be set freely
Status:       falsified, and more comprehensively than first recorded
Source:       LTA quarterly quota press releases, Annex A
Falsified by: n/a
Touches:      3.1, rebuilt entirely
Notes:        Not merely constrained. Computed. LTA publishes the full arithmetic each
              quarter: growth allowance, plus a quarterly slice of a rolling four-quarter
              deregistration average net of guaranteed deregistrations, plus named adjustments
              for taxi population change, expired TCOEs, the Early Turnover Scheme,
              guaranteed-deregistration redistribution and discretionary injection. The
              decision variables were rebuilt as the policy parameters feeding the formula
              rather than its output. See A-08 for the risk that introduces.

              **Sub-note, do not lose this.** The 25 percent in the replacement term is one
              quarter of the trailing annual figure. It is arithmetic, not a policy rate. Do
              not model it as a lever.

### A-03. Revenue is one of the objectives the government optimises for
Status:       verified as officially denied, deliberately unresolved as a modelling question
Source:       1990 Parliamentary Select Committee on Land Transport; 1996 White Paper "A
              World Class Land Transport System"; MOT ministerial statements 2023 and 2025
Falsified by: recovered revenue weight near zero across eras
Touches:      3.2, 5.3
Notes:        The factual question is settled. No Singapore minister has framed COE as a
              revenue instrument. The stated purpose is consistent across thirty-five years:
              allocation of a fixed vehicle quota under land scarcity. The nearest any
              minister comes is describing what the revenue funds, which is a statement about
              spending, not purpose.

              The modelling question stays open on purpose. Revenue remains an objective and
              the recovered weight is the test, not an input. Do not resolve this row before
              the model runs.

              Do not assert the revenue-motive claim anywhere in the project. It is
              commentary.

### A-04. The ten-year COE term makes vehicle stock a rolling decade of registrations
Status:       unverified, and known to be more complicated than first written
Source:       COE scheme design
Falsified by: accumulator backtest failing to reproduce the published population series
Touches:      4.2
Notes:        Three complications confirmed by the scan. COEs can be renewed by paying the
              prevailing quota premium, which breaks the clean window. Five-year
              non-extendable COEs exist and were the first source drawn on by cut-and-fill
              from May 2023. Early deregistration is what the "guaranteed deregistration"
              term in the quota formula refers to, so it is large enough that LTA accounts
              for it explicitly. The backtest is the arbiter.

              2026-08-31. Renewal counts would be easiest to read straight off the LTA
              DataMall MVP01 and MVP02 tables, which include COE revalidation counts. DataMall
              needs an account key and this project stores no credential, so that source is
              deferred and the backtest runs without it. See the decision log entry of the same
              date. If the accumulator cannot reproduce the published series and renewals are
              the reason, the files get downloaded by hand and committed. That is the point at
              which this row's falsification test would otherwise be answered by a data gap
              rather than by the model.

### A-05. The BPR volume-delay function adequately maps vehicle population to congestion
Status:       unverified
Source:       standard transport literature
Falsified by: calibrated capacity producing speeds far from published LTA figures
Touches:      4.3, O2
Notes:        Data exists and is better than expected: annual average peak-hour speeds from
              2004, split expressway and arterial, peak hour defined as 8 to 9am and 6 to 7pm
              weekdays. Capacity available by road category from 1990, described in section 8
              as lane-km, though the unit is not stated in the file itself and is now A-15. But
              see A-09 for why having the data does not make this objective safe. BPR is also a
              link-level function being applied at network level, which is a known
              simplification and may end as accepted-as-limitation rather than verified.

### A-06. Categories A, B and C capture enough of the system to be meaningful
Status:       verified with a caveat
Source:       LTA Annex A; MOT ministerial statements
Falsified by: Cat D or E volumes large enough to materially change congestion or revenue
Touches:      scope, all objectives
Notes:        Cat D is under zero growth like A and B, so excluding it as a decision dimension
              is defensible. Cat E cannot be excluded outright because its supply is derived
              from A, B and C (see A-07), so it is included as a derived quantity. The caveat:
              the MOF revenue line covers all five categories, so the reconciliation in 4.4
              must sum all of them even though only three are decision dimensions.

### A-07. Category premiums are independent enough to model separately
Status:       falsified
Source:       LTA Annex A, notes on Category E supply derivation
Falsified by: n/a
Touches:      4.1, 3.1
Notes:        Cat E supply is set at 10 percent of the summed A, B and C replacement quotas,
              a published mechanical linkage. Cat E is almost always used for larger cars, so
              it functions as an arbitrage channel transmitting demand pressure back into A
              and B. No official spillover coefficient exists. Decision: model Cat E supply
              mechanically, treat demand-side spillover as an acknowledged limitation rather
              than estimating it. Any spillover coefficient that does end up in the model is
              yours and must be labelled as such.

### A-08. The three chosen policy levers are not collinear in their effect on the objectives
Status:       unverified — NEW, and now the second-highest risk row
Source:       consequence of the A-02 rebuild
Falsified by: sampling the decision space and finding the front is a curve rather than a
              surface, or finding the three objectives are near-perfectly explained by total
              quota alone
Touches:      3.1, and by extension the entire frontier
Notes:        The rebuild replaced quota counts with policy parameters. The danger is that
              growth rate, replacement adjustments and injections all push total quota the
              same direction, in which case all three objectives become functions of one
              number and the frontier collapses into a traced line. This is exactly the
              failure that killed the housing scenario.

              The chosen set (`g_ab`, `g_c`, `theta`) is designed to avoid it: total volume,
              private versus commercial reallocation, within-car reallocation. Verify before
              building on it.

              If `theta` proves unmodellable because car registrations by power output are not
              published, fall back to a discretionary injection lever and record that the
              frontier will be flatter as a consequence.

### A-09. The congestion objective can be identified from available data
Status:       unverified — NEW, and expected to end as accepted-as-limitation
Source:       consequence of examining the speed dataset's granularity
Falsified by: wide confidence intervals on the fitted BPR beta, or the sensitivity sweep
              showing the frontier moves substantially with congestion parameters alone
Touches:      4.3, O2, section 6
Notes:        The speed series is annual from 2004, so roughly twenty observations, over a
              period when the vehicle population moved slowly and mostly in one direction. The
              volume-capacity ratio barely varies across the sample, which is the worst
              possible case for identifying an exponent.

              Expect O2 to be the weakest of the three objectives. Do not hide this. State it
              in the case study, flag it on the congestion axis in the UI, and give the
              congestion parameters extra attention in the sensitivity sweep.

              Secondary note: published lane-km shows a large single-year jump between 2023
              and 2024 that looks like reclassification rather than construction. Flag it,
              do not smooth it. Published road length also covers only LTA-maintained roads.

### A-10. Computed revenue can be reconciled against published government figures
Status:       falsified as stated. **This is not a passing test and must not be counted as
              one.** The residual is accepted as a limitation, not closed
Source:       SingStat table M130571 series 1.2.1, the Vehicle Quota Premiums line, spot
              checked against the MOF document under A-17. Computation in
              `src/model/revenue.py`, tests in `tests/test_revenue_reconciliation.py`
Falsified by: computed revenue diverging from the published figure by more than a reasonable
              margin after period alignment
Touches:      4.4, 5.4, O3, stage 3, stage 10
Notes:        Run 2026-09-04 against FY2024, the latest financial year with actual figures.
              FY2025 is a revised estimate and FY2026 is budgeted, so both are excluded, and
              the module refuses them rather than leaving it to whoever runs it. The cutoff is
              read from the table footnote in the committed metadata, so a re-pull that moves
              it moves the refusal too.

              FY2024, April 2024 to March 2025, millions of dollars:

                  computed, quota times premium            5,057.4
                  computed, successful bids times premium  4,987.6
                  published                                6,379.2
                  residual                                 1,321.8
                  computed as a share of published            79.3%

              The brief says a failure here is a pipeline bug rather than a finding about the
              published figure. Four candidate bugs were checked and none of them accounts for
              it.

              Categories. All five are summed, per A-06. FY2024 has 24 of 24 exercises and
              120 of 120 category cells, none missing, and every category contributes.

              Period alignment. Shifting the twelve-month window to the calendar year, one
              month early and one month late moves the total across a range of 456, against a
              residual of 1,321.8. Every window falls short of the published figure.

              Suspended exercises. April to June 2020 are absent rather than counted as zero.
              FY2024 has no suspended exercises in any case.

              Source defects. Quota, successful bids and premium come from the wide table,
              which A-12 settled as the reference where the two bidding sources conflict, and
              thousands separators are stripped on read per A-13.

              The choice of basis does not close it either. Successful bids times premium is
              98.6 percent of quota times premium, so it moves the wrong way and by too
              little.

              The residual is one-signed from FY2011 onward and its share sits between 78 and
              92 percent. That pattern is what makes it structural rather than a slip.
              A-19 records the leading explanation and what would settle it. A-20 records the
              years before FY2010, where the two run the other way and the reason is not
              established.

              What this costs the model. O3 computed from the bidding record is bid revenue,
              which is roughly four fifths of the published line in FY2024. It is not
              government revenue from the COE system and must not be described as such, and
              the published line is not a calibration target for it while the missing term is
              missing.

              2026-09-24, said plainly because the brief assumed otherwise. This is a failed
              validation, not a validation with a caveat. Section 5.4 specified three tests
              and the project now has two, of which one is still unrun at stage 7. A residual
              of 20 percent with an explanation attached is wide enough to hide a moderate
              error in the premium handling or the quota accounting, and nothing else in the
              build would surface one: A-12 compares the two bidding sources only from 2010
              and A-21 audits the wide table against itself, so neither is external and
              neither would catch an error the two published tables share. Anywhere this test
              is cited as support, it supports less than it appears to.

              On whether it can ever close. Not against FY2024. Closing it needs renewal and
              taxi volumes for the target year priced at the prevailing quota premium, and no
              published series carries renewal counts that recently. What can be done is
              weaker and worth doing: the mechanism in A-19 is testable on the years where
              renewal counts do exist, which would turn the explanation from plausible to
              measured without making the FY2024 number reconcile. See A-19.

### A-11. The structural break table is complete and correctly dated
Status:       falsified as stated, then corrected and verified. The verified table is
              `docs/break-table.md`
Source:       compiled during the day one scan, mixed primary and secondary. Verified at stage 4
              against LTA releases and Annex A tables committed under `data/raw/lta-annex-a/`
Falsified by: a primary LTA or MOT document contradicting a date, or an unexplained
              discontinuity in the fitted series at a date not on the table
Touches:      4.1
Notes:        Nine breaks currently listed in the brief. Some dates came from primary LTA and
              MOT sources and some from trade press or encyclopaedic secondary sources,
              specifically the 1991 non-transferability change and the bid deposit history.
              Treat the secondary-sourced dates as medium confidence and verify against LTA
              archives before they enter a regression as dummies. An unexplained break in the
              residuals is the practical falsification test.

              Stage 2 update. The SingStat footnotes for table M651121, now committed at
              `data/raw/singstat-metadata.json`, are a primary source and confirm four dates
              without opening a PDF. Open bidding fully replaced closed bidding from the April
              2002 exercise, with February and March 2002 running one of each. Category A added
              the 97kW criterion from the February 2014 exercise. From 6 August 2012 all taxis
              pay the Category A prevailing quota premium rather than bidding. Bidding was
              suspended in April, May and June 2020, and the April 2020 PQP applied through
              July 2020. Check these against the nine rows in the brief at stage 4.

              The same footnotes define PQP as a moving average of the quota premium over the
              last three months in which bidding was actually held, which is the definition
              A-04 needs for renewals and is not the same as a plain three-month average.

              Stage 4, 2026-09-24. Every row now has a committed primary source, quoted in
              `docs/break-table.md`. The scan's table was not complete and not all correctly
              dated, so the claim as stated is falsified. Three corrections.

              Missing: from 1 August 2022 the quota used a rolling two-quarter average, 50
              percent of six months of deregistrations, before the four-quarter average of
              February 2023. The Annex A arithmetic shows it without the prose: three-month
              windows through the May 2022 quarter, six for August and November 2022, twelve
              from February 2023.

              Wrong: the 19,490 COEs from the 2020 suspension were returned from July 2020 to
              June 2021, not to July 2021. The June 2020 release says so, and the Annex A
              return lines sum to 19,490 exactly.

              Under-described: May 2023 was three supply changes. Cut-and-fill from the second
              exercise of the month, the Early Turnover Scheme deduction moving to a
              four-quarter average, and Category D COEs returning to bidding earlier.

              May 2017 is dated by LTA's own Annex A footnotes, in all 27 formula tables. They
              were written from 2020 onward, but a footnote in which LTA describes a change LTA
              made is primary whenever it was written. Accepted as sourced on 2026-09-24; the
              2017 announcement was not opened. The pre-2002 dates this row once carried fall
              before the left-truncation and were not verified, because nothing uses them.

              The falsification test that remains is the practical one: an unexplained break in
              the stage 6 residuals at a date not on the table.

### A-12. The two COE bidding sources agree where they overlap
Status:       falsified
Source:       `src/ingest/crosscheck_coe.py` against the two committed raw files
Falsified by: n/a
Touches:      4.1, 4.4, stage 3, stage 6
Notes:        They overlap from 2010-01 and disagree on two of 7,840 compared values. Both
              are in `coe-bidding-results` (`d_69b3380ad7e51aff3a7dcc84eba52b8a`) and both
              have the same signature, a value repeated from the row above.

              2010-01 bidding 2 Category D premium reads 20090, which is Category C's premium
              from the line above. The wide table says 852, and 852 is what a motorcycle COE
              cost in January 2010.

              2010-02 bidding 1 Category B quota reads 1154, which is Category A's quota from
              the line above. The wide table says 693. The tie-break is arithmetic: the wide
              table's five category quotas sum to 2984, which is its own published total for
              that exercise. The long table's sum to 3445.

              So `quota-premium-monthly` (`d_22094bf608253d36c0c63b52d852dd6e`) is the
              reference where the two conflict. Two values is small, but the Category D one is
              a 23-fold error sitting in a series whose real range is under 1000, which would
              dominate a log-log fit on Category D and misstate stage 3 revenue for that
              exercise. Correct downstream, visibly. Do not edit the committed raw file.

              Re-run the cross-check after any re-pull. A third conflict appearing means the
              upstream table changed and this row needs revisiting.

              2026-09-04. Both defects fall in FY2009, January and February 2010, so neither
              touches a reconciliation from FY2010 onward. Priced out, the Category D premium
              error is 7.3 million and the Category B quota error is 10.7 million, both in the
              long table and both absent from the wide one. Over FY2010 to FY2024 the two
              tables give revenue figures that agree to the cent, which is the check in
              A-21.

### A-13. Published series are internally consistent enough to parse numerically without inspection
Status:       falsified
Source:       the committed raw files
Falsified by: n/a
Touches:      every fit, stage 3 onward
Notes:        Two separate problems, both silent under a naive read.

              `coe-bidding-results` writes thousands separators in `bids_success` and
              `bids_received` from 2023-05 onward, and only in those two columns. `quota` and
              `premium` are clean across the whole file. A default `read_csv` gives two numeric
              columns and two object columns with no error raised.

              `vehicle-population-monthly` renames its own categories mid-series, `Cars` and
              `Rental Cars` to 2017-07, then `Car` and `Rental cars` from 2017-08. Grouping by
              the raw label splits each series in two.

              The general form of this is the thing to carry forward: a published file changing
              its own conventions partway through. Check the distinct values of every key column
              against period before grouping on it.

### A-14. The monthly vehicle population dataset covers the modelling period
Status:       falsified
Source:       `d_2ecb009f1e1ec5a816a454944dec4022`, coverage read off the pulled file
Falsified by: n/a
Touches:      4.2, A-04, stage 7
Notes:        It runs 2012-01 to 2018-02 and stops. Seventy-four months, eight years stale.
              Section 8 lists it without a coverage claim, so nothing in the brief was wrong,
              but it cannot carry the accumulator backtest.

              `vqs-population-monthly` (`d_ede1a559013d10f234d209ac5e9fd9b4`) replaces it.
              It runs 1990May to 2026Jun and is broken out on the VQS categories the model
              actually uses, A, B, C, D, taxis, weekend cars and VQS-exempt vehicles, rather
              than the body-type split. That is the better source for stage 7 on both counts.

              The annual companion `d_2873f3b1b2a836103f51f696350b98fa` covers 2005 to 2024,
              which is also short of the 1990 record. Same remedy.

### A-15. The lane-km figure means lane-kilometres
Status:       verified
Source:       SingStat TableBuilder metadata for table M650321, `uoM` field on all five series.
              Committed at `data/raw/singstat-metadata.json`.
Falsified by: n/a
Touches:      4.3, O2, A-05, A-09
Notes:        Opened because the CSV states no unit and section 8 asserted one. Closed the same
              day from the upstream table's own metadata, which gives `Lane-Kilometres` for all
              five series and names LTA as the source.

              Worth keeping as a row rather than deleting. It mattered more than a units
              footnote usually does: BPR capacity scales directly with this number, so a wrong
              unit rescales the volume-capacity ratio by roughly a factor of three, and A-09
              says that ratio barely varies across the sample. A constant scale error on a
              near-constant regressor is close to unidentifiable from the fit itself, so this
              was not something the model would have caught later.

              The table footnote also confirms the coverage caveat A-09 carries from a
              secondary source: LTA-maintained roads only, excluding other agencies and
              privately-owned areas.

### A-16. Deregistration counts are not published as a standalone series
Status:       falsified
Source:       SingStat TableBuilder table M650291, "Motor Vehicles De-Registered Under Vehicle
              Quota System, Monthly". Metadata committed at `data/raw/singstat-metadata.json`.
Falsified by: n/a
Touches:      3.1, 4.2, A-04, stage 4
Notes:        Section 8 states these counts are not published standalone and that they have to
              be extracted from Annex A PDFs and LTA Annual Vehicle Statistics. Stage 4 budgets
              that extraction as the week-one bottleneck.

              The series exists. Monthly, from 1990 May to 2026 Jul, sourced to LTA, broken out
              as Category A cars, Category B cars, weekend and off-peak cars, Category C goods
              vehicles and buses, Category D motorcycles, taxis, and VQS-exempt vehicles. That
              is the same category split as the population and new-registration series already
              in section 8, so it lines up with them directly.

              Only the metadata is pulled so far. The series values are not committed and
              nothing reads them, because adding a source to section 8 is a decision for the
              stage 2 gate rather than one to make while pulling.

              Two things to check before it replaces the Annex A extraction rather than
              cross-checking it. Whether this series is the same quantity the quota formula's
              rolling four-quarter deregistration average is computed from, and whether it
              separates guaranteed deregistrations, which the formula nets out and which A-04
              says are large enough for LTA to account for explicitly. If it does not separate
              them, some Annex A extraction is still needed and this series becomes a check on
              it. That would still be a large saving.

              Stage 4, 2026-09-24. Both questions answered from 27 Annex A tables, February 2020
              to August 2026, extracted by `src/ingest/extract_annex_a.py`.

              Same quantity: yes, exactly. Line B1 of every table equals the M650291 sum over
              the window B1 names, in every category, in 27 of 27 tables and across all three
              formula regimes. Not close, equal.

              Guaranteed deregistrations: M650291 does not separate them and Annex A does, as a
              line of its own from the August 2023 quarter. Before May 2023 there were none to
              separate, since cut-and-fill began then. Annex A flips the sign it prints them
              with in February 2024; the quantity is the same.

              So the usable deregistration series is M650291, monthly from 1990, with the
              Annex A guaranteed deregistration line netted off from August 2023. The week of
              Annex A extraction stage 4 budgeted became a scripted pull and a parser, and the
              manual part is gone.

### A-17. The MOF Vehicle Quota Premiums line is only available as a PDF
Status:       falsified
Source:       SingStat TableBuilder table M130571, "Government Operating Revenue, Annual",
              series 1.2.1 "Vehicle Quota Premiums", in millions of dollars, 1997 to 2026.
              Sourced to the Accountant-General's Department.
Falsified by: n/a
Touches:      4.4, A-10, stage 3
Notes:        Section 8 sources the reconciliation target from the MOF Analysis of Revenue and
              Expenditure. That document is a PDF and is not reachable from this environment.
              The same line is available from SingStat as a machine-readable annual series.

              The table footnote confirms the alignment problem A-10 already flags: the figures
              are financial years beginning 1 April, and FY2026 is a budgeted estimate rather
              than an outturn, so the most recent year must be excluded from the reconciliation
              or labelled as an estimate.

              Do not treat this as settled. AGD and MOF publish from the same accounts and the
              line carries the same name, but that the two figures are identical is an
              assumption until one year is checked against the MOF document by hand. A-10 is
              the reconciliation test and it should not be run against a target that has itself
              only been assumed. Spot-check one year first.

              2026-09-04, done for one year. `www.singaporebudget.gov.sg` is now reachable from
              this environment, where stage 2 found it blocked. Table 2.1 of "Review of
              Financial Year 2025", in the Revenue and Expenditure Estimates for FY2026, gives
              Vehicle Quota Premiums as 6.38 billion actual FY2024. SingStat gives 6379.2
              million for the same year. The two agree to the precision MOF publishes at. The
              PDF is committed at `data/raw/mof-review-of-fy2025.pdf` and the check is a test,
              not a note. One year is one year: this says the two publications carry the same
              number for FY2024, not that they do for every year, and A-20 is a reason to be
              careful about the early ones.

### A-18. data.gov.sg republications are current with their SingStat originals
Status:       falsified
Source:       end periods in `data/raw/manifest.json` against `data/raw/singstat-metadata.json`
Falsified by: n/a
Touches:      section 8, any series cut-off
Notes:        Every wide source in section 8 is a republished SingStat table, and each lags its
              original. Quota and premium by one month, VQS population by one month, public
              roads not at all, and new registrations under the VQS by six months, ending
              2026 Jan on data.gov.sg against 2026 Jul upstream.

              Small for a model fitted on decades. It matters for two things: stating the
              sample period honestly, and not reading a republication lag as a real gap in
              registrations. If the most recent months turn out to matter, pull the wide
              sources from SingStat instead of data.gov.sg.

### A-19. The stage 3 residual is payment made at the prevailing quota premium without a bid
Status:       unverified, and frozen: moved to F-01 on 2026-09-24 and not tested. Still the
              leading explanation of the A-10 shortfall
Source:       consequence of the stage 3 run. Scheme mechanics from the SingStat M651121
              footnotes committed at `data/raw/singstat-metadata.json`, which define the
              prevailing quota premium and record that from 6 August 2012 taxis pay the
              Category A prevailing quota premium rather than bidding
Falsified by: a published count of COE renewals over a financial year that, priced at the
              prevailing quota premium, leaves the residual substantially unexplained; or the
              residual persisting after such counts are added
Touches:      4.4, O3, A-04, A-10, stage 3, stage 10
Notes:        A COE renewal is a payment of the prevailing quota premium with no bid attached.
              The bidding record cannot contain it, by construction. Taxis have been in the
              same position since August 2012. Both are vehicle quota premiums and both are
              missing from anything computed off quota and clearing price, which is the shape
              the residual has: one-signed, present in every year from FY2011, and largest in
              the years when premiums are highest.

              Size. FY2024's residual of 1,321.8 million is 16,582 COEs at that year's
              quota-weighted mean premium of 79,714. That is an arithmetic restatement of the
              residual, not a renewal count, and it is not evidence for anything on its own.

              No committed source gives renewal counts. LTA DataMall MVP01 and MVP02 do,
              according to the day one scan, and they are deferred under the no-credential
              rule with the files to be downloaded by hand if they become load-bearing. A-04
              already names the same gap for the accumulator. If those files are fetched for
              stage 7, this row is answerable at the same time and for no extra cost.

              Until then the residual stays unexplained rather than explained-by-assumption,
              and O3 stays labelled as bid revenue.

              2026-09-24. The paragraph above is wrong about where renewal counts live, found
              while sweeping the data.gov.sg catalogue for something else. Two open LTA
              datasets publish them, no credential and no DataMall:

                  d_71ce745d4e4ea9cd2fea0fdf46412fc8  annual, 2006 to 2017, 96 rows
                  d_11af4cacfdd459f8712fb903b1639d98  monthly, 2015-01 to 2018-01, 296 rows

              Both are LTA-managed, split by 5-year and 10-year COE and by category, and both
              state that the count refers to revalidations using the prevailing quota premium
              applicable in that period, which is exactly the quantity this row is about. The
              monthly one also notes a two-month reporting lag from the one-month grace period.

              What that changes. The falsification test is runnable now for the years both
              series cover, which overlap the residual years FY2011 to FY2016. Priced at the
              prevailing quota premium and added to bid revenue, renewals either account for
              the residual in those years or they do not, and either answer is worth having.

              What it does not change. Coverage stops in 2017 and 2018, so this cannot close
              A-10 for FY2024 and the reconciliation stays failed. Neither series covers
              taxis, which are the other half of the mechanism from August 2012. Adopting
              these as sources is a section 8 decision rather than one to take while sweeping
              a catalogue, and nothing reads them yet.

### A-20. The published revenue line is comparable with computed bid revenue across the sample
Status:       falsified. The unexplained cause is frozen as F-03
Source:       `python -m src.model.revenue --series`, FY2002 to FY2024 against M130571
Falsified by: n/a
Touches:      4.4, stage 3, any use of the revenue line before FY2010
Notes:        From FY2002 to FY2009 the computed figure runs above the published one, not
              below it. FY2002 is 129 percent of the published line, FY2005 is 563 percent and
              FY2006 is 1,601 percent, which is 1,497.2 million computed against 93.5 million
              published. FY2010 sits just above parity at 105 percent and FY2011 just below at
              99 percent. From FY2011 the sign is stable the other way and stays there.

              The bidding arithmetic is not obviously wrong in those years. Quotas were large
              and premiums were low, and the computed totals are of a size the exercises
              support. Something about the published line changed, and no footnote on M130571
              says what. A netting-off of rebates paid on deregistration would produce this
              shape in a period of heavy deregistration, but that is a guess and this register
              does not carry guesses as facts.

              Practical effect. Treat the target as usable from FY2010 onward. Do not
              reconcile against a pre-2010 year, and do not use the pre-2010 line as a revenue
              series or in any long-run claim about COE revenue. Settling it needs an MOF
              document from that era, which is a manual download and is not worth the time
              before the freeze.

              2026-09-04, the other side of it was tested instead. A break in a ratio can sit
              in either term, and the bidding table is the term that matters for the rest of
              the build, because it is the only source for 2002 to 2009. It was audited
              against the checks in A-21 and nothing separates the two eras. So the break is
              in the published revenue line and not in `quota-premium-monthly`. That does not
              explain the line, it locates the thing that needs explaining, and the practical
              effect above is unchanged.

              2026-09-24, re-run and pushed further, because a source mismatch is the cheaper
              hypothesis and deserved more than one pass. Three things to record.

              The reconciliation does not switch sources at 2010. `src/model/revenue.py` reads
              `quota-premium-monthly` for every financial year in the series, FY2002 to
              FY2024, and the long table is only ever a cross-check. One file produces both
              sides of the break, so a file switch cannot be what shifts the ratio. If the
              level shift came from the data it would have to be a change inside that one
              file, which is what A-21 tests and does not find.

              The long table's start is the publisher's, not a short pull. The data.gov.sg
              metadata for `d_69b3380ad7e51aff3a7dcc84eba52b8a` gives coverageStart
              2010-01-01. Section 8's claim of April 2002 was wrong, which A-12 already
              recorded, and the file is not truncated at our end.

              There is no second pre-2010 bidding source to check against. The SingStat
              keyword index returns exactly one table carrying bidding or quota premium,
              M651121, which is this file. A sweep of all 4,629 datasets in the data.gov.sg
              catalogue returns no bidding-results dataset other than the two already in
              section 8. So A-21's stated limit is now a searched-for absence rather than an
              assumed one, and it does not move: the pre-2010 values cannot be checked one by
              one against anything.

### A-21. The wide bidding table's columns mean the same thing across the whole span
Status:       verified, with the limits below
Source:       `python -m src.ingest.verify_quota_premium`, tests in
              `tests/test_quota_premium_table.py`. Column definitions from the SingStat
              M651121 metadata committed at `data/raw/singstat-metadata.json`
Falsified by: any of the six checks separating the two eras on a re-pull, in particular the
              PQP identity failing in one era and holding in the other
Touches:      4.1, 4.4, stage 3, stage 6, A-12, A-20
Notes:        Opened because A-20 found a break at 2010 and the break has two possible homes.
              `quota-premium-monthly` is the only source for 2002 to 2009, the long table
              starts at 2010-01, and stage 6 would read a change in what the columns mean as
              elasticity drift. So the file was tested rather than the revenue line.

              What the publisher says. Quota, successful bids and bids received are counts.
              Quota premium and prevailing quota premium are dollars. The period is the month
              of the bidding exercise. Two exercises are held each month under open bidding,
              which fully replaced closed bidding from the April 2002 exercise, with February
              and March 2002 running one of each. "Quota premium is the successful bid price
              paid by all successful bidders", so it is a per-exercise clearing price, not an
              average of anything.

              What the file shows. Twenty-four exercises in every full year, eighteen in 2020
              for the suspension, twenty-two in 2002 because it starts in February. The five
              category quotas sum to the file's own published total in all 582 exercises,
              both eras. The two biddings of a month carry the same premium in 1.7 percent of
              category-months before 2010 and 0.5 percent after, so the premium column is not
              a monthly figure written twice in either era.

              The sharp check. The prevailing quota premium is published as the moving average
              of the quota premium over the latest three months in which bidding was held.
              That makes PQP a function of the premium column. Computed from the premium
              column, it reproduces every published PQP to within 83 cents, in 100 percent of
              category-months, 93 per category before 2010 and 199 after. Three published
              columns would have had to be rewritten together for that to survive a change in
              meaning.

              Two external checks. COEs awarded track new registrations under the VQS once
              registrations that need no bid are removed, which are Early Turnover Scheme
              goods vehicles and taxis paying the prevailing quota premium from August 2012.
              The adjusted ratio runs 0.99 to 1.05 before the break and 0.96 to 1.08 after.
              And over FY2010 to FY2024 the wide and long tables give identical revenue under
              the same multiplication.

              Limits, and they matter. This says the columns did not change meaning, not that
              the pre-2010 values are individually correct. There is no second table to check
              them against value by value, which is exactly what A-12 could do for the
              overlap. The registration check is a magnitude check rather than an identity,
              since a COE won in one month can be registered in the next. And before August
              2012 a taxi could bid instead of paying the prevailing quota premium, so the
              early years subtract a few registrations that did involve a bid.

              2026-09-24. The missing second table was looked for rather than assumed away.
              The SingStat keyword index returns one table carrying bidding or quota premium,
              which is this one, and a sweep of all 4,629 data.gov.sg datasets returns no
              bidding-results dataset beyond the two in section 8. The limit stands and is now
              known to be a property of what is published, not of what was pulled. The checks
              above are therefore the whole of the evidence for the pre-2010 span, and the
              re-run on 2026-09-24 reproduced every one of them unchanged.

              For stage 6. The 2002 to 2009 span is usable in the premium fits on the same
              terms as the rest of the sample. Read a break in the fitted elasticity there as
              a break in the world, not as a change in the file. The regime changes that do
              sit in that span are in A-11 and belong in the break table.

### A-22. The Annex A quota arithmetic can be reproduced exactly from its own printed inputs
Status:       falsified — NEW, by at most 1.25 COEs per category
Source:       `python -m src.ingest.extract_annex_a`, check 3, and `tests/test_annex_a.py`
Falsified by: n/a
Touches:      3.1, stage 10, any test that compares the implemented formula with Annex A
Notes:        The replacement line is printed as a share of deregistrations: 25 percent of B1
              net of guaranteed deregistrations under the current regime. Computed from the
              B1 and B2 printed beside it, each category's published value is a rounding of
              that product in all but four cells across 27 tables:

                  Feb 2024  Category C  published 1,780  product 1,779.00
                  May 2025  Category B  published 3,910  product 3,911.00
                  Aug 2025  Category B  published 4,583  product 4,582.00
                  Feb 2026  Category C  published 2,227  product 2,228.25

              Rounding is also not in a fixed direction: some quarters round every category
              up, others down, so a row total can sit up to two COEs from the rounded product
              of the totals. Rounding the total first and apportioning it across categories was
              tested as an explanation and does not fit, because some published totals are not
              a rounding of the total product either.

              Small, and it matters for one reason. Stage 10 implements this formula and will
              want to check it against Annex A. An exact-match test would fail on these cells
              and send someone looking for a bug in their own code. The honest tolerance is
              about 1.25 COEs per category per quarter, and the four cells are known.

              Separately, section 3.1 writes the formula in its February 2023 form. It had a
              one-quarter window at 100 percent until July 2022 and a two-quarter window at 50
              percent from August 2022. Anything that runs the formula over history needs the
              regime that applied at the time. See A-11 and `docs/break-table.md`.

### A-23. Stage 5's placeholder values are plausible enough to test the lever geometry
Status:       accepted as placeholders, stage 5 only. Replaced by fitted values at stages 6 and
              9, and nothing past stage 5 reads them
Source:       `config/placeholders.toml`, every value marked there as an assumption
Falsified by: the fitted values landing outside the swept ranges, which would mean stage 5
              tested geometry the real model does not have
Touches:      stage 5, A-08, and stage 8, which repeats the check on fitted values
Notes:        Assumed, and swept rather than set:

                  premium elasticity b per category   -0.5, -1.0, -2.0, in every combination
                                                      across A, B and C
                  road load of a goods vehicle or bus 1.0, 1.5, 2.0, 3.0 PCU against 1.0 for
                                                      a car. 1.0 is the control where road
                                                      load is proportional to quota
                  growth rate upper bound             1 and 3 percent a year
                  categories O1 and O3 sum over       all five, or A, B and C

              Assumed and not swept, because they cannot change which policies are on the
              front: the BPR alpha and beta (0.15 and 4, the conventional Bureau of Public
              Roads values, cited in the config), the base volume to capacity ratio 0.9, and
              the five-year horizon. O2 is monotone in road load for any of them, and dominance
              does not change under a monotone rescaling of one objective.

              Not assumed, read from committed data: the reference quarter's quota, premiums,
              populations, deregistrations and adjustments; the quota formula; the injection
              lever's range, 0 to 5,155 COEs a quarter, and its allocation across categories,
              both off the Annex A redistribution lines; the theta anchor, 0.588, the Category A
              share of A and B bids received in the reference quarter.

              The unit elasticity is a knife-edge. At b = -1 premium times quota is constant, so
              O3 cannot move with quota at all. It stays in the sweep and is kept out of the
              main table, because it would make any lever set look two-objective for a reason
              that belongs to the placeholder and not to COE.

---

## Post-freeze findings

After the week one freeze, new findings go here rather than into the build. They become the
limitations and future work section of the case study.

```
### F-nn. <the finding>
Found:     date
Would have changed: what in the model
Cost to chase: rough estimate in days
Decision: not chased, documented
```

The freeze took effect on 24 September 2026, retroactive to 29 August. The rows below are the
findings surfaced after 29 August that were not in the build when it was applied.

### F-01. Whether renewals explain the revenue residual is untested
Found:     2026-09-04, sharpened 2026-09-24
Would have changed: A-19 from plausible to measured, and possibly a narrower revenue check over
           FY2011 to FY2016 using the two open LTA revalidation datasets,
           `d_71ce745d4e4ea9cd2fea0fdf46412fc8` (annual, 2006 to 2017) and
           `d_11af4cacfdd459f8712fb903b1639d98` (monthly, 2015 to 2018). Neither is adopted.
           Neither covers taxis, and neither reaches FY2024, so A-10 would stay failed either way.
Cost to chase: half a day, the timebox set on 2026-09-24
Decision: not chased, documented. A-10 stays a failed validation with an unverified mechanism.

### F-02. Whether O3 should be total revenue rather than bid revenue is not decided
Found:     2026-09-24, from the stage 3 residual
Would have changed: the definition of O3 at stage 10. Bid revenue leaves out payments at the
           prevailing quota premium with no bid. The case for keeping it: renewal volumes follow
           quota decisions made about a decade earlier and barely respond to the levers. The case
           against: the renewal price is the clearing premium averaged, so a lever that lowers
           premiums lowers renewal revenue too. Both sides are in the decision log.
Cost to chase: one to two days, since it needs F-01's data and a model of the renewal price
           channel. An estimate, not measured.
Decision: not chased, documented. O3 stays bid revenue as built, labelled as bid revenue
           wherever it appears. The freeze closes the option by default, not on its merits.

### F-03. The cause of the pre-2010 break in the published revenue line is unknown
Found:     2026-09-04
Would have changed: any long-run claim about COE revenue before FY2010. Nothing in the build
           reads the published line before FY2010, so no model result depends on it. A-21 ruled
           out the bidding data as the cause.
Cost to chase: about half a day, for an MOF document from that era, downloaded by hand
Decision: not chased, documented. The line is treated as usable from FY2010 onward.

### F-04. O1 averaged over all five categories moves by composition as well as by price
Found:     2026-09-24, stage 5
Would have changed: the definition of O1 at stage 10. O1 is the quota-weighted mean premium.
           Counted over all five categories, moving quota towards a cheap category lowers it
           even if no buyer pays less: a motorcycle COE clears at about 10,000 dollars and a
           car COE at about 125,000. The injection lever puts about a quarter of its COEs into
           motorcycles, so under it, O1 over all five categories falls partly by composition.
           At stage 5 this is what turns a curve into a surface on one side of unit elasticity.
           Counting A, B and C only removes it.
Cost to chase: under an hour to redefine and re-run stage 5. The redefinition is the choice,
           not the work.
Decision: not chased, documented. Stage 5 reports both category sets and reads its gate on
           A, B and C, the decision categories, so the composition effect cannot pass it.

### F-05. The brief's 30,813 injection anchor is not reproduced from Annex A
Found:     2026-09-24, stage 5
Would have changed: the calibration anchor section 3.1 gives for an injection lever's bounds,
           "30,813 COEs redistributed and injected in total between May 2023 and November
           2025". The Annex A redistribution lines sum to 31,894 over the quarters from August
           2023 to January 2026, plus 1,914 in two mid-quarter revisions in 2023. The window the
           figure was taken over is not stated, so it cannot be matched.
Cost to chase: about an hour, if the original source can be found
Decision: not chased, documented. Stage 5 bounds the injection lever by the largest quarterly
           line Annex A prints, 5,155, which does not depend on the 30,813 figure.

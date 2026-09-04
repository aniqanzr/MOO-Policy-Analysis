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
Status:       falsified as stated. The residual is accepted as a limitation, not closed
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

### A-11. The structural break table is complete and correctly dated
Status:       unverified — NEW
Source:       compiled during the day one scan, mixed primary and secondary
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
Status:       unverified — NEW, and the leading explanation of the A-10 shortfall
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

### A-20. The published revenue line is comparable with computed bid revenue across the sample
Status:       falsified — NEW
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

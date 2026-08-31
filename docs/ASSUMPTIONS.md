# Assumptions register

Every belief about how COE actually works lives here, not in the brief. New facts update a
row. They do not edit `PROJECT_BRIEF.md`.

Each row needs a status and a falsification condition. If you cannot write what would prove
an assumption wrong, you do not understand it well enough to build on it.

Statuses: `unverified`, `verified`, `falsified`, `accepted-as-limitation`.

**Updated after the day one scan.** Three rows falsified, two resolved, three new rows added.

**Updated after the stage 2 pull, 2026-08-31.** Eight new rows, A-12 to A-19. Seven are
falsifications, and mostly of things nobody had thought to doubt: that two official sources of
the same numbers agree, that a published file keeps its own formatting conventions, that a
dataset listed in section 8 is current, that a republication keeps up with its original, that a
published quota stays published. Two go the other way and remove work rather than adding it,
A-16 and A-17, both now adopted into section 8. A-05 and A-11 amended. A-15 was opened and
closed the same day.

**A-16 is the one that changes the plan.** The deregistration series reconciles exactly against
four Annex A quarters, so stage 4 no longer needs bulk PDF extraction for it. Read the row
before acting on that: the published count is gross, the formula from August 2023 runs on a net
figure that is not published, and the gap is currently negligible for a reason that expires.
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
Status:       unverified — NEW
Source:       MOF Analysis of Revenue and Expenditure, "Vehicle Quota Premiums" line
Falsified by: computed revenue diverging from the published figure by more than a reasonable
              margin after period alignment
Touches:      4.4, 5.4
Notes:        This is a validation test the project did not previously have, and it is the
              only one that checks the premium series handling and quota accounting against
              external ground truth. Two things to get right: the MOF line covers all five
              categories, and the figures are fiscal years, so align periods before comparing.
              A failure here is a bug in the pipeline, not a finding about MOF.

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

              The four committed Annex A PDFs pin the February 2023 break more precisely than
              the brief's table row does. The window and the slice changed together: before,
              row B1 covered six months and B2 took 50 percent of it; after, B1 covers twelve
              months and the slice is 25 percent. Both yield one quarter of the trailing
              average, so this is a change in the averaging window, not in the replacement
              rate. The 25 percent is arithmetic either way, exactly as the working rules say.
              The annexes also date the growth rate freeze to February 2018 at 0 percent for
              Cat A, B and D and 0.25 percent for Cat C, stated as running until January 2025.

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

              Re-run the cross-check after any re-pull. It exits nonzero only when the set of
              conflicts changes, not on these two, so a third conflict appearing or one of
              these disappearing is the signal. A check that always fails is a check nobody
              reads.

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
Status:       falsified. The series exists, and it has been reconciled against Annex A.
Source:       SingStat M650291, committed at `data/raw/vqs-deregistrations-monthly.json`.
              Four Annex A PDFs at `data/raw/annex-a`. Check reproduced by
              `python -m src.ingest.crosscheck_deregistrations`.
Falsified by: n/a
Touches:      3.1, 4.2, A-04, stage 4
Notes:        Section 8 held that these counts are not published standalone and that stage 4
              would extract them from Annex A. The series exists: monthly, 1990 May to 2026
              Jul, LTA-sourced, on the VQS categories.

              Adopted as primary, and the condition attached to that adoption has been met.
              Twenty comparisons across four consecutive quarters straddling February 2023,
              two quarters under each regime, reconcile exactly. Not approximately. Every
              category in every quarter.

              **What the series is.** M650291 on the four VQS category lines is Annex A row
              B1, total vehicle deregistrations, gross, over whatever window that annex names.

              **What it is not, and this is the answer to the open question.** It is not
              effective deregistrations net of guaranteed deregistrations. From the August 2023
              annex the formula runs on B1 minus B2, where B2 is the guaranteed deregistration
              subset. B2 is not in the published series and is not derivable from it. Before
              August 2023 no netting row exists at all, so the net quantity the brief describes
              is something Annex A constructs rather than something published.

              **Why that is survivable now and may not stay so.** B2 was 1 vehicle against a
              B1 of 44,612 in the window tested, 0.002 percent. The scheme had just started.
              It identifies Category A and B vehicles holding five-year non-extendable COEs, and
              those were first issued from May 2023, so B2 grows as they approach expiry. Do not
              read the current gap as a permanent one. Re-run the check on recent quarters
              before assuming gross still approximates net.

              **Two traps.** Sum the four category lines. M650291's own total row also counts
              taxis and VQS-exempt vehicles, which Annex A's total column excludes, and it runs
              about 2,400 a year higher, over 5 percent. Separately, row C4, redistribution from
              guaranteed deregistrations, is material where B2 is not: 1,025 in the August 2023
              quarter against a total quota of 11,019. C4 is Annex A only.

              **Consequence for stage 4.** The bulk PDF extraction is no longer needed for the
              deregistration series itself. Annex A is still needed for B2 and C4 in the
              cut-and-fill era, and for the growth allowance and named adjustments, which were
              never in this series. The saving is large. It is not the whole of stage 4.

### A-17. The MOF Vehicle Quota Premiums line is only available as a PDF
Status:       falsified. Adopted as primary. Verification against MOF still outstanding.
Source:       SingStat M130571, series 1.2.1 "Vehicle Quota Premiums", millions of dollars,
              FY1997 to FY2026, sourced to the Accountant-General's Department. Committed at
              `data/raw/government-operating-revenue-annual.json`.
Falsified by: n/a
Touches:      4.4, A-10, stage 3
Notes:        Adopted as primary for the A-10 reconciliation target. Machine-readable, so
              stage 3 is unblocked.

              **Bound the window before running A-10.** The table footnote is explicit that
              actual figures run to FY2024 only. FY2025 are revised estimates and FY2026 are
              budgeted estimates. Reconciling against an estimate and reporting the gap as a
              pipeline error would be a self-inflicted finding. The usable window is FY1997 to
              FY2024. Figures are financial years beginning 1 April, so align first.

              **The verification is still open.** AGD and MOF publish from the same accounts
              and the line carries the same name, but that the two figures are identical is
              still an assumption. One financial year spot-checked against the MOF Analysis of
              Revenue and Expenditure settles it, and A-10 should not be treated as passed
              until that is done.

              The MOF document could not be fetched. `singaporebudget.gov.sg` was added to the
              environment allowlist, but the apex host redirects every request to
              `www.singaporebudget.gov.sg`, which is not on the list, so the redirect is denied.
              Adding the `www` host is the whole fix. See `docs/manual-downloads.md`.

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

### A-19. The quota published for a quarter is the quota that quarter ran on
Status:       falsified
Source:       comparison rows across the committed Annex A PDFs at `data/raw/annex-a`
Falsified by: n/a
Touches:      3.1, 5.3, stage 13
Notes:        The May 2023 annex gives a total quota of 9,575 for May to Jul 2023. The August
              2023 annex, printing the same quarter as its comparison row, gives 10,431.
              Category A moves from 2,798 to 3,358 and Category B from 2,367 to 2,663.

              The difference is the cut-and-fill redistribution, which began at the second
              bidding exercise of May 2023, after that quarter's annex was published. So the
              quarter was reopened mid-flight rather than misprinted.

              Two consequences. A quarter's quota has no single published value, and which one
              is correct depends on the question: the ex-ante figure is what the policy
              intended, the ex-post figure is what was actually bid for. Stage 13 locates the
              current policy position on the frontier, and that position moves depending on
              which is used. Take the ex-post figure, since the objectives are computed from
              what happened, and say so.

              This also means an annex is not a durable record of its own quarter. When
              extracting, prefer the later annex's comparison row over the earlier annex's
              headline row, and record which was used.

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

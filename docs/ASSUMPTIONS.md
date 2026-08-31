# Assumptions register

Every belief about how COE actually works lives here, not in the brief. New facts update a
row. They do not edit `PROJECT_BRIEF.md`.

Each row needs a status and a falsification condition. If you cannot write what would prove
an assumption wrong, you do not understand it well enough to build on it.

Statuses: `unverified`, `verified`, `falsified`, `accepted-as-limitation`.

**Updated after the day one scan.** Three rows falsified, two resolved, three new rows added.
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
              weekdays. Capacity available as lane-km by road category from 1990. But see
              A-09 for why having the data does not make this objective safe. BPR is also a
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

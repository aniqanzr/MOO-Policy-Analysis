# Manual downloads

What stage 2 could not pull, and what it turned out not to need. Written 2026-08-31 at the
stage 2 gate.

Reachability below is from this build environment, which sits behind an egress proxy with an
allowlist. A host marked blocked here is blocked by that policy, not necessarily down. If you
are running from an unrestricted network, try it before doing anything by hand.

---

## Nothing is blocking stage 3 or stage 4

That is the short version, and it is not what was expected going in. Two sources section 8
assumed had to be extracted from PDFs turned out to be published as machine-readable series.
The list of things needing a human is shorter than the brief implies, and none of it gates the
next two stages.

---

## Please download by hand

### 1. MOF Analysis of Revenue and Expenditure, Vehicle Quota Premiums line

Wanted for: A-10, the revenue reconciliation, stage 3.
Why not scripted: `www.singaporebudget.gov.sg`, where `www.mof.gov.sg` redirects for revenue
and expenditure, is blocked by egress policy. `www.mof.gov.sg` itself is reachable.

**Not urgent, and not a blocker.** The same line is published as SingStat table M130571, series
1.2.1 "Vehicle Quota Premiums", annual in millions of dollars from FY1997, sourced to the
Accountant-General's Department. Stage 3 can run against that.

What is wanted from you is a **spot check of one year**, not the whole document. AGD and MOF
publish from the same accounts and the line carries the same name in both, but that the two
figures are identical is currently an assumption, and A-10 should not be run against a target
that has itself only been assumed. One year from the MOF PDF, against the SingStat figure for
the same financial year, settles it. See A-17.

### 2. LTA DataMall, MVP01 and MVP02 static tables

Wanted for: COE revalidation and renewal counts, which A-04 needs for the accumulator.
Why not scripted: `datamall.lta.gov.sg` and `datamall2.mytransport.sg` are both blocked by
egress policy. DataMall also requires an account key sent as an `AccountKey` header, and this
project does not have one. Registering for that key is the part only you can do.

Lowest confidence item on this page. Whether MVP01 and MVP02 actually carry revalidation counts
was recorded during the day one scan and has not been checked against the tables themselves,
because they could not be opened. Confirm before spending time on it.

### 3. NLB Infopedia, 1990 Select Committee history

Wanted for: policy context and the case study, not the model.
Why not scripted: `www.nlb.gov.sg` is blocked by egress policy.

Lowest priority on this page. No coefficient depends on it. A-03 is already settled from
Parliamentary and White Paper sources.

---

## Reachable, so please do not do these by hand

Checked during stage 2, listed because section 8 reads as though they need a person.

**LTA quarterly quota press releases and Annex A.** `www.lta.gov.sg` is reachable and the
newsroom index lists the releases at a stable URL pattern,
`/content/ltagov/en/newsroom/{year}/{month}/news-releases/certificate-of-entitlement-quota-for-...`.
The Annex A PDFs sit under `/content/dam/ltagov/news/press/` and download without
authentication. One was fetched end to end as a check. These are scriptable at stage 4.

**MOT newsroom and Parliamentary replies.** Reachable at
`https://www.mot.gov.sg/news-resources/newsroom/`.

**SingStat TableBuilder.** Reachable, and the source of the units and footnotes that
data.gov.sg strips. `python -m src.ingest.pull_singstat` pulls the metadata.

One trap worth knowing. `www.mof.gov.sg` and `www.mot.gov.sg` both return 403 to the default
`python-requests` user agent and 200 to a browser one. A script that reports either as
unreachable is describing its own headers, not the site.

---

## Deregistration counts, which stage 4 no longer has to extract

Section 8 says deregistration counts are not published as a standalone series and that they
have to come out of Annex A PDFs and LTA Annual Vehicle Statistics. Stage 4 budgets that as the
week-one bottleneck.

SingStat table M650291, "Motor Vehicles De-Registered Under Vehicle Quota System, Monthly",
is that series. LTA-sourced, 1990 May to 2026 Jul, split by the same VQS categories as the
population and registration series already in section 8.

This is not yet adopted. Only the metadata is committed and nothing reads the values, because
putting a new source into section 8 is a call for the gate rather than one to make mid-pull.
Two questions decide whether it replaces the Annex A extraction or only cross-checks it: whether
it is the same quantity the quota formula's rolling four-quarter average is built from, and
whether it separates out guaranteed deregistrations, which the formula nets off. If it does not
separate them, some Annex A work remains and this becomes the check on it. See A-16.

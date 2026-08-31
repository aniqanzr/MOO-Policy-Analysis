# Manual downloads

What still needs a person, and what turned out not to. Written 2026-08-31 at the stage 2 gate,
revised the same day after both discovered sources were adopted.

Reachability is from this build environment, which sits behind an egress proxy with an
allowlist. A host marked blocked is blocked by that policy, not necessarily down.

---

## Nothing needs downloading by hand

The list is empty. One environment fix is outstanding and one source is deferred by decision.

---

## One allowlist entry to fix

`singaporebudget.gov.sg` was added, but the fetch still fails. The apex host is on the list and
answers, then redirects every request to `www.singaporebudget.gov.sg`, which is not on the list,
and the redirect is denied at CONNECT.

Adding the `www` host is the whole fix. Nothing else about the source is a problem.

What it is wanted for: the A-17 spot check. The MOF Analysis of Revenue and Expenditure is no
longer the source for the revenue reconciliation, since SingStat M130571 carries the same line
in machine-readable form and is adopted as primary. What remains is verification, one financial
year checked against the SingStat figure, because AGD and MOF publishing identical numbers is
currently an assumption rather than something checked. A-10 should not be treated as passed
until it is done.

Not urgent. Stage 3 can run against M130571 now, with the spot check landing before A-10 is
called.

---

## Deferred by decision, not blocked

**LTA DataMall, MVP01 and MVP02.** Deferred entirely. The claim that these tables carry COE
revalidation counts came from the day one scan and has never been checked against the tables
themselves. The credential path is unresolved: DataMall requires an account key. Nothing in
week one depends on it. Revisit at stage 4 only if renewals turn out to need it.

Recorded here so it is not mistaken for something still being chased.

---

## Reachable and scripted, so do not do these by hand

**LTA quarterly quota press releases and Annex A.** Scripted at
`python -m src.ingest.pull_annexa`. Four quarters straddling February 2023 are committed under
`data/raw/annex-a`. The release URLs follow no stable naming convention, so the fetcher checks
each release page still links the PDF path it expects rather than trusting a hardcoded path.

**SingStat TableBuilder.** Scripted at `python -m src.ingest.pull_singstat`. Source of the two
adopted tables and of the units and footnotes data.gov.sg strips.

**data.gov.sg.** Scripted at `python -m src.ingest.pull_datagov`.

**MOT newsroom and Parliamentary replies.** Reachable at
`https://www.mot.gov.sg/news-resources/newsroom/`. Not yet scripted, nothing needs it yet.

**NLB Infopedia.** Still blocked by egress policy. Context for the case study only, no
coefficient depends on it, and A-03 is already settled from Parliamentary and White Paper
sources. Not worth an allowlist change unless the case study wants it.

One trap worth keeping. `www.mof.gov.sg` and `www.mot.gov.sg` both return 403 to the default
`python-requests` user agent and 200 to a browser one. A script reporting either as unreachable
is describing its own headers, not the site.

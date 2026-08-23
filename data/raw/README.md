# data/raw

Raw downloads, committed so the pipeline reproduces from a clean clone. Nothing here is
edited by hand. Cleaning happens downstream and lands in `data/processed`.

## What the script pulls

    python -m src.ingest.pull --verify     check every dataset ID in section 8 still resolves
    python -m src.ingest.pull              verify, download, write manifest.json

Eight data.gov.sg datasets, listed in `src/ingest/sources.py`. Each arrives as
`<slug>.csv` alongside `<slug>.metadata.json`, and `manifest.json` records a SHA-256 per file
so an upstream revision is visible in a diff rather than silently changing a fitted
coefficient.

The script exits non-zero if any dataset ID fails to resolve. A 404 means the ID has moved:
find the current one, update section 8 of the brief, and note it in the decision log.

## Status

**Nothing has been downloaded yet.** The session where stage 2 ran had no route to any
Singapore government host, so no dataset ID has been checked against the live API and no file
has been fetched. The eight datasets remain unverified. See the decision log entry for
2026-08-23 on the blocked stage 2 gate.

## What has to be downloaded by hand

These six are not on the data.gov.sg API. Save them here with the filenames given, then the
downstream stages can find them.

### 1. LTA quarterly quota press releases, with Annex A

- Where: https://www.lta.gov.sg/content/ltagov/en/newsroom.html, filter to press releases about
  the COE quota.
- Save as: `annex-a/<yyyy>-q<n>.pdf`
- Needed: eight to twelve quarters straddling the regime changes, plus the most recent few.
  At minimum one before and one after February 2023, when quota computation moved to the
  rolling four-quarter deregistration average, and one after February 2025, when discretionary
  injection began.
- Why: the authoritative source for the quota formula in section 3.1, and the only place the
  deregistration arithmetic is shown worked through. Stage 4 depends on these.

### 2. LTA Annual Vehicle Statistics

- Where: https://www.lta.gov.sg/content/ltagov/en/who_we_are/statistics_and_publications/statistics.html
- Save as: `annual-vehicle-statistics/<yyyy>.pdf`
- Why: deregistration counts are not published as a standalone series. This and Annex A are
  where they exist at all.

### 3. LTA DataMall static data, MVP01 and MVP02

- Where: https://datamall.lta.gov.sg/content/datamall/en/static-data.html
- Requires a free DataMall account key. Put it in `.env` as `LTA_DATAMALL_ACCOUNT_KEY`.
  `.env` is gitignored and the key must not be committed.
- Save as: `datamall/mvp01.csv`, `datamall/mvp02.csv`
- Why: COE revalidation counts. Section 4.2 needs them because renewals break the clean ten
  year window the accumulator would otherwise assume.

### 4. MOF Analysis of Revenue and Expenditure

- Where: https://www.mof.gov.sg/singaporebudget/revenue-and-expenditure
- Save as: `mof-revenue/fy<yyyy>.pdf`
- Needed: several fiscal years, enough for stage 3 to reconcile more than one.
- Why: the Vehicle Quota Premiums line under Operating Revenue is the ground truth for gate
  A-10. Published as annual Budget PDFs with no API.
- Note: the line covers all five categories including D and E, and the figures are fiscal
  years. Both have to be handled before comparing.

### 5. MOT Parliamentary replies and ministerial statements

- Where: https://www.mot.gov.sg/news
- Save as: `policy/<yyyy-mm-dd>-<slug>.pdf` or `.html`
- Why: sourcing for the assumptions register. Cited, not parsed.

### 6. NLB Infopedia, 1990 Select Committee on Land Transport

- Where: https://www.nlb.gov.sg
- Save as: `policy/1990-select-committee.html`
- Why: history of the scheme's stated purpose. Cited, not parsed.

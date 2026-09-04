# Raw data

Downloaded source files, committed on purpose so the pipeline reproduces from a clean clone.
Nothing under `data/` is gitignored. Do not clean this directory.

Section 8 of `docs/PROJECT_BRIEF.md` names every source. `src/ingest/sources.py` restates that
list in machine-readable form and is the file to change when a source moves. This README
explains how each kind of file gets here.

## How files arrive

**Scripted.** The open data.gov.sg datasets are pulled by `python -m src.ingest.fetch` from the
repo root. It resolves each dataset id, pages the datastore API until the record count is
exhausted, writes `data/raw/<key>.csv`, and records row counts, column names and a sha256 per
file in `data/raw/manifest.json`. Run `--check-only` to confirm the ids still resolve without
downloading. Every endpoint it touches is open and needs no account.

**By hand.** The Annex A quota press releases, LTA Annual Vehicle Statistics, the MOF Analysis
of Revenue and Expenditure, MOT Parliamentary replies and the NLB Infopedia history are PDFs
and tables with no open API. Download them, put them here, and add a line to the table below
saying what the file is and the URL it came from. The URL matters more than the file name: a
committed PDF with no recorded provenance cannot be re-verified.

## Credentials

**No credential is stored anywhere in this repo, and none should be added.**

Not in a `.env` file, not in an example env file, not in a config module, not in a cloud
environment variable. Three reasons, and they compound:

- This repo will be made public. A committed key is a published key.
- The build runs in Claude Code on the web. There is no durable local filesystem, so an
  uncommitted local `.env` does not survive between sessions and the only way to make one
  persist is to commit it.
- Environment variables set on the cloud environment are visible to anyone using that
  environment, so they are not a private store either.

`.env` stays in `.gitignore` as a safety net against an accidental commit. That is not
permission to create one.

A source that requires an account key is deferred rather than authenticated. If it later turns
out to be needed, the files are downloaded by hand outside this repo, through a browser, and
the resulting data files are committed here like any other manual download. The key never
touches the repo or the environment.

### LTA DataMall

Deferred. Section 8 lists DataMall static data, tables MVP01 and MVP02, including COE
revalidation counts. DataMall requires a registered account key, so under the rule above it is
not fetched.

Nothing currently depends on it. Every other section 8 source is open, and the vehicle
population, VQS population and VQS new registration series cover the accumulator's inputs.
Revalidation counts would only become load-bearing if stage 7 shows the accumulator cannot
reproduce the published population series without them, which is A-04's falsification test.

If that happens: download the MVP01 and MVP02 files by hand from
<https://datamall.lta.gov.sg/> and commit them here with a row in the table below. No key gets
stored, no `.env` gets created, and `src/ingest/fetch.py` stays credential-free. The same
applies if COE revalidation counts turn out to be needed for the revalidation adjustment in the
quota formula.

## What is here

The eight data.gov.sg CSVs are recorded in `manifest.json`, one entry each, with the resource
id, row count, column names, coverage and a sha256. That file is the record for them and this
table does not repeat it.

Everything else here came from somewhere the pull script does not go.

| File | Source | Method | Retrieved | URL |
| ---- | ------ | ------ | --------- | --- |
| `singstat-metadata.json` | SingStat TableBuilder metadata for six tables. Units and footnotes, which data.gov.sg strips. | `python -m src.ingest.pull_singstat` | 2026-08-31 | <https://tablebuilder.singstat.gov.sg/api/table/metadata/{table_id}> |
| `vehicle-quota-premiums-annual.csv` | SingStat table M130571 series 1.2.1, Vehicle Quota Premiums, annual, millions of dollars. The stage 3 reconciliation target. | `python -m src.ingest.pull_revenue` | 2026-09-04 | <https://tablebuilder.singstat.gov.sg/api/table/tabledata/M130571> |
| `vehicle-quota-premiums-annual.meta.json` | Provenance for the file above, including the footnote that says which financial years are actual figures. | `python -m src.ingest.pull_revenue` | 2026-09-04 | same |
| `mof-review-of-fy2025.pdf` | MOF, Review of Financial Year 2025, from the Revenue and Expenditure Estimates for FY2026. Table 2.1 carries Vehicle Quota Premiums actual FY2024. The A-17 spot check. | one-off download, no pull script | 2026-09-04 | <https://www.singaporebudget.gov.sg/revenue-and-expenditure/revenue-expenditure-estimates>, document at <https://cms.singaporebudget.gov.sg/assets/567a92bc-910e-4e19-a67e-a0016a2adbe1> |

## What could not be reached automatically

**Egress changes between sessions and the state below is what the last run found.** On
2026-08-31 every section 8 host was refused at the proxy with a 403 on CONNECT. The pull ran
later that day. On 2026-09-04 `tablebuilder.singstat.gov.sg`, `www.mof.gov.sg` and
`www.singaporebudget.gov.sg` were all reachable, which is how the stage 3 target and the MOF
spot check got here without a human. Do not treat a host recorded as blocked here as blocked
now. Try it. `python -m src.ingest.fetch --check-only` names each failure without downloading
anything.

**Requires manual download regardless of network policy**, because there is no open API:

- `lta_annex_a_quota_releases`, quarterly quota press releases with Annex A. Stage 4 needs
  eight to twelve straddling the regime changes plus recent quarters.
- `lta_annual_vehicle_statistics`, the other published home of deregistration counts.
- `mof_revenue_and_expenditure`, the Vehicle Quota Premiums line, fiscal years. One document
  is here now, for the A-17 spot check. The reconciliation itself runs against the SingStat
  series, so no more of these are needed unless A-20 gets chased.
- `mot_parliamentary_replies`, policy mechanics and framing.
- `nlb_infopedia_select_committee`, 1990 history, secondary source, framing only.

**Deferred**, needs an account key that this project does not store:

- `lta_datamall_mvp01_mvp02`. See above.

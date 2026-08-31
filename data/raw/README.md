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

Nothing yet. The scripted pull has not run successfully.

| File | Source | Method | Retrieved | URL |
| ---- | ------ | ------ | --------- | --- |
|      |        |        |           |     |

## What could not be reached automatically

Stage 2 status as of 2026-08-31. The stage 2 gate, knowing exactly what you have and exactly
what you must download by hand, is **not passed**.

**Blocked by the network egress policy, not by the sources.** Every host in section 8 is
refused at the proxy with a 403 on CONNECT, so no dataset id has been verified to resolve and
no file has been downloaded. The affected hosts:

```
data.gov.sg                   api-production.data.gov.sg
www.data.gov.sg               api-open.data.gov.sg
tablebuilder.singstat.gov.sg  www.lta.gov.sg
www.mof.gov.sg                datamall2.mytransport.sg
```

`python -m src.ingest.fetch --check-only` reproduces this and names each failure. Re-run it
once the egress policy allows those hosts. Until then the eight scriptable sources are
unverified, and section 8's warning that ids and coverage change has not been acted on.

**Requires manual download regardless of network policy**, because there is no open API:

- `lta_annex_a_quota_releases`, quarterly quota press releases with Annex A. Stage 4 needs
  eight to twelve straddling the regime changes plus recent quarters.
- `lta_annual_vehicle_statistics`, the other published home of deregistration counts.
- `mof_revenue_and_expenditure`, the Vehicle Quota Premiums line, fiscal years.
- `mot_parliamentary_replies`, policy mechanics and framing.
- `nlb_infopedia_select_committee`, 1990 history, secondary source, framing only.

**Deferred**, needs an account key that this project does not store:

- `lta_datamall_mvp01_mvp02`. See above.

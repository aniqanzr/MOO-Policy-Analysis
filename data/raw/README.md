# Raw data

Published files as served, committed on purpose so the pipeline reproduces from a clean clone.
Nothing under `data/` is gitignored. Nothing here is cleaned, reshaped or corrected. Do not
clean this directory.

Section 8 of `docs/PROJECT_BRIEF.md` names every source. `src/ingest/sources.py` restates that
list in machine-readable form and is the file to change when a source moves. Filenames here are
the registry keys, so a file and its entry cannot drift apart.

## How files arrive

Everything section 8 needs is now scripted. Nothing is waiting on a manual download.

| what | command | writes |
| --- | --- | --- |
| data.gov.sg datasets | `python -m src.ingest.pull_datagov` | eight CSVs, `manifest.json` |
| SingStat tables | `python -m src.ingest.pull_singstat` | two JSON series, `singstat-metadata.json` |
| LTA Annex A quarters | `python -m src.ingest.pull_annexa` | four PDFs under `annex-a/` |

`pull_datagov` saves the CSV the portal itself serves rather than a table rebuilt from the
datastore API, so the bytes match what a person clicking Download would get. It falls back to
the datastore and records which path it used. `manifest.json` carries a sha256, row count and
period range per file. Two independent pulls on 2026-08-31 gave identical checksums, so the
hashes are worth comparing against on a re-pull.

The SingStat responses are saved as JSON rather than flattened to CSV, because the per-series
footnotes carry conditions the model has to respect and no reshaping would keep them.

Two checks reproduce the findings below rather than asking you to trust them:
`python -m src.ingest.crosscheck_coe` and
`python -m src.ingest.crosscheck_deregistrations`.

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

A source that requires an account key is deferred rather than authenticated. Every endpoint the
pull scripts touch is open. `tests/test_ingest_sources.py` walks the syntax tree of every module
under `src/ingest` and fails on a `getenv`, an `environ` or a dotenv import, so the rule is
enforced by something other than this paragraph.

**LTA DataMall is the live case and it is deferred**, by decision rather than by blockage. It
needs an account key, and separately the claim that MVP01 and MVP02 carry COE revalidation
counts has never been checked against the tables. Nothing in week one depends on it. It becomes
load-bearing only if stage 7 shows the accumulator cannot reproduce the published population
series without renewal counts, which is A-04's falsification test. If that happens, download the
files by hand through a browser and commit them here with their URLs recorded. The key never
touches the repo or the environment.

## What each file is

| file | source | coverage |
| --- | --- | --- |
| `coe_bidding_results.csv` | `d_69b3380ad7e51aff3a7dcc84eba52b8a` | 2010-01 to 2026-08 |
| `quota_and_premium_monthly.csv` | `d_22094bf608253d36c0c63b52d852dd6e` | 2002Feb to 2026Jul |
| `vehicle_population_annual.csv` | `d_2873f3b1b2a836103f51f696350b98fa` | 2005 to 2024 |
| `vehicle_population_monthly.csv` | `d_2ecb009f1e1ec5a816a454944dec4022` | 2012-01 to 2018-02 |
| `vqs_population_monthly.csv` | `d_ede1a559013d10f234d209ac5e9fd9b4` | 1990May to 2026Jun |
| `vqs_new_registrations_monthly.csv` | `d_529752a3d78beb78bd4f38e3be37f1b6` | 1990May to 2026Jan |
| `peak_hour_speeds_annual.csv` | `d_26f6afadf2f86b2004f9a1e28f5564cc` | 2004 to 2025 |
| `public_roads_annual.csv` | `d_f73d13943f7a3cc1aca76b18fea75013` | 1990 to 2025 |
| `vqs_deregistrations_monthly.json` | SingStat M650291 | 1990 May to 2026 Jul |
| `government_operating_revenue_annual.json` | SingStat M130571 | FY1997 to FY2026 |
| `annex-a/*.pdf` | LTA quarterly quota releases | four quarters straddling Feb 2023 |

## Read this before parsing any of it

Findings from the stage 2 pull. Registered as A-12 through A-19 in `docs/ASSUMPTIONS.md`.

**The two COE sources conflict on two values.** `coe_bidding_results.csv` carries a wrong
premium at 2010-01 bidding 2 Category D and a wrong quota at 2010-02 bidding 1 Category B. Both
repeat the value from the row above. `quota_and_premium_monthly.csv` has the correct figures and
its per-category quotas sum to its own published total where the long table's do not. Do not
correct the files here. Handle it downstream where the correction is visible.

**`coe_bidding_results.csv` writes thousands separators** in `bids_success` and `bids_received`
from 2023-05 onward, and only in those two columns. `quota` and `premium` are clean throughout.
A naive numeric read silently turns those two columns into strings.

**The 2002 to 2009 span is only in `quota_and_premium_monthly.csv`.** The long table starts at
2010-01. Section 8 said April 2002, which is when open bidding replaced closed bidding, not when
this file starts.

**April, May and June 2020 are suspended exercises,** written `-` in the wide table and simply
absent from the long table. They are not zero-quota months. Prevailing quota premium is still
published for them, because it is a trailing average.

**`vehicle_population_monthly.csv` stops at 2018-02** and changes its own category labels
partway through, using `Cars` and `Rental Cars` to 2017-07 and `Car` and `Rental cars` from
2017-08. Use `vqs_population_monthly.csv` for the accumulator backtest instead.

**`public_roads_annual.csv` is in lane-kilometres**, confirmed from `singstat-metadata.json` for
the upstream table M650321, covering LTA-maintained roads only. The CSV itself states no unit.
Read it from the metadata rather than inferring it from magnitudes.

**`vqs_deregistrations_monthly.json` is gross, and its total row is not Annex A's total.**
Sum the four VQS category lines. The file's own total row also counts taxis and VQS-exempt
vehicles and runs over 5 percent higher. The four category lines are Annex A row B1 exactly,
verified across four quarters. The guaranteed deregistration subset the formula nets off from
August 2023 is not in this file and is currently negligible for a reason that expires. See A-16.

**`government_operating_revenue_annual.json` is actual only to FY2024.** FY2025 are revised
estimates and FY2026 budgeted, per the table footnote. Financial years begin 1 April. See A-17.

**The Annex A PDFs restate each other.** The May 2023 annex gives that quarter a total quota of
9,575; the August 2023 annex, printing the same quarter, gives 10,431. Mid-quarter injection,
not a misprint. Prefer the later annex's comparison row. See A-19.

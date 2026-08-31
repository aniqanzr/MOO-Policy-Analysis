# Raw downloads

Published files as served, unchanged. Nothing here is cleaned, reshaped or corrected. They are
committed so the pipeline reproduces from a clean clone without hitting the network.

The eight CSVs are the data.gov.sg sources from section 8 of `docs/PROJECT_BRIEF.md`, pulled by
`python -m src.ingest.pull_datagov`. `manifest.json` records, per file, the resource id, a
sha256, the row count, the period range and whether the pull came from the portal's own CSV or
was rebuilt from datastore records. Two independent pulls on 2026-08-31 produced identical
checksums, so the hashes are worth comparing against on a later re-pull.

Three further sets came in when two SingStat tables were adopted into section 8 at the stage 2
gate. `python -m src.ingest.pull_singstat` writes `singstat-metadata.json`, which carries the
units and footnotes data.gov.sg strips, plus `vqs-deregistrations-monthly.json` (M650291) and
`government-operating-revenue-annual.json` (M130571). Both are saved as the API serves them,
because reshaping to CSV would drop per-series footnotes that carry real conditions.
`python -m src.ingest.pull_annexa` writes the four PDFs under `annex-a/`.

## What each file is

| file | resource id | coverage |
| --- | --- | --- |
| `coe-bidding-results.csv` | `d_69b3380ad7e51aff3a7dcc84eba52b8a` | 2010-01 to 2026-08 |
| `quota-premium-monthly.csv` | `d_22094bf608253d36c0c63b52d852dd6e` | 2002Feb to 2026Jul |
| `vehicle-population-annual.csv` | `d_2873f3b1b2a836103f51f696350b98fa` | 2005 to 2024 |
| `vehicle-population-monthly.csv` | `d_2ecb009f1e1ec5a816a454944dec4022` | 2012-01 to 2018-02 |
| `vqs-population-monthly.csv` | `d_ede1a559013d10f234d209ac5e9fd9b4` | 1990May to 2026Jun |
| `vqs-new-registrations-monthly.csv` | `d_529752a3d78beb78bd4f38e3be37f1b6` | 1990May to 2026Jan |
| `peak-hour-speed-annual.csv` | `d_26f6afadf2f86b2004f9a1e28f5564cc` | 2004 to 2025 |
| `public-roads-annual.csv` | `d_f73d13943f7a3cc1aca76b18fea75013` | 1990 to 2025 |

## Read this before parsing any of it

Findings from the stage 2 pull. Registered as A-12 through A-15 in `docs/ASSUMPTIONS.md`.

**The two COE sources conflict on two values.** `coe-bidding-results.csv` carries a wrong
premium at 2010-01 bidding 2 Category D and a wrong quota at 2010-02 bidding 1 Category B. Both
repeat the value from the row above. `quota-premium-monthly.csv` has the correct figures and its
per-category quotas sum to its own published total where the long table's do not. Run
`python -m src.ingest.crosscheck_coe` to reproduce. Do not correct the files here. Handle it
downstream where the correction is visible.

**`coe-bidding-results.csv` writes thousands separators** in `bids_success` and `bids_received`
from 2023-05 onward, and only in those two columns. `quota` and `premium` are clean throughout.
A naive numeric read silently turns those two columns into strings.

**The 2010 to 2002 span is only in `quota-premium-monthly.csv`.** The long table starts at
2010-01. Anything needing the full post-2002 record, the revenue reconciliation included, reads
the wide table for the earlier years.

**April, May and June 2020 are suspended exercises,** written `-` in the wide table and simply
absent from the long table. They are not zero-quota months. Prevailing quota premium is still
published for them, because it is a trailing average.

**`vehicle-population-monthly.csv` stops at 2018-02** and changes its own category labels
partway through, using `Cars` and `Rental Cars` to 2017-07 and `Car` and `Rental cars` from
2017-08. Use `vqs-population-monthly.csv` for the accumulator backtest instead. It runs from
1990May and is on the VQS categories the model uses.

**The unit in `public-roads-annual.csv` is not stated in the file.** It is lane-kilometres,
confirmed from `singstat-metadata.json` for the upstream table M650321, and covers
LTA-maintained roads only. Read it from there rather than inferring it. See A-15.

**`vqs-deregistrations-monthly.json` is gross, and its total row is not Annex A's total.**
Sum the four VQS category lines. The file's own total row also counts taxis and VQS-exempt
vehicles and runs over 5 percent higher. The four category lines are Annex A row B1 exactly,
verified across four quarters by `python -m src.ingest.crosscheck_deregistrations`. The
guaranteed deregistration subset the formula nets off from August 2023 is not in this file.
See A-16.

**`government-operating-revenue-annual.json` is actual only to FY2024.** FY2025 are revised
estimates and FY2026 budgeted, per the table footnote. Financial years begin 1 April. See A-17.

**The Annex A PDFs under `annex-a/` restate each other.** The May 2023 annex gives that
quarter a total quota of 9,575; the August 2023 annex, printing the same quarter, gives 10,431.
Mid-quarter injection, not a misprint. Prefer the later annex's comparison row. See A-19.

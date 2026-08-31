"""Pull the SingStat sources: metadata for the republished tables, data for the adopted two.

Run it:

    python -m src.ingest.pull_singstat

Two jobs, and they are different.

Four of the eight data.gov.sg sources in section 8 are republished SingStat tables. Only their
metadata is pulled. data.gov.sg serves the numbers without units or footnotes and neither is
recoverable from the CSV: the public roads file gives 10,265 for 2025 with nothing saying what
is being counted. That gap is what opened A-15, and the `uoM` field pulled here is what closed
it. The values are not pulled, because they are already committed from data.gov.sg and two
copies of one series invites reading the wrong one.

Two further tables were adopted into section 8 at the stage 2 gate, and for those SingStat is
the source rather than the upstream, so metadata and values are both pulled.

M650291, monthly deregistrations under the VQS. Adopted as primary for deregistrations,
conditional on the A-16 reconciliation against Annex A quarters straddling February 2023.

M130571, government operating revenue, for the Vehicle Quota Premiums line. Adopted as primary
for the A-10 reconciliation target, with a spot check against the MOF document as verification.

Responses are saved as served, as JSON. Reshaping to CSV would drop the per-series footnotes,
and on both these tables the footnotes carry conditions the model has to respect: which years
are actual rather than estimated, and which series stops early.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.ingest.singstat import SingStatError, metadata, series_span, tabledata

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
METADATA_FILE = "singstat-metadata.json"

# SingStat table behind each section 8 source that data.gov.sg republishes. Metadata only.
UPSTREAM_OF_DATAGOV = {
    "M651121": "d_22094bf608253d36c0c63b52d852dd6e",
    "M650341": "d_ede1a559013d10f234d209ac5e9fd9b4",
    "M650281": "d_529752a3d78beb78bd4f38e3be37f1b6",
    "M650321": "d_f73d13943f7a3cc1aca76b18fea75013",
}

# Adopted into section 8 at the stage 2 gate. Metadata and values.
ADOPTED = {
    "M650291": {
        "slug": "vqs-deregistrations-monthly",
        "role": "primary for deregistrations, conditional on A-16",
        "condition": (
            "Reconcile against three or four Annex A quarters straddling February 2023 before "
            "stage 4 drops the PDF extraction. The open question is whether this published "
            "count is the same quantity as the effective deregistrations net of guaranteed "
            "deregistrations that the quota formula uses."
        ),
    },
    "M130571": {
        "slug": "government-operating-revenue-annual",
        "role": "primary for the A-10 reconciliation target",
        "condition": (
            "Spot check one financial year against the MOF Analysis of Revenue and Expenditure "
            "before A-10 is run against it. Actual figures run to FY2024 only."
        ),
    },
}

KEEP = ("id", "title", "frequency", "dataSource", "footnote",
        "dataLastUpdated", "startPeriod", "endPeriod")


def summarise(records):
    """Metadata flattened to the fields worth committing."""
    entry = {key: records.get(key) for key in KEEP}
    entry["series"] = [
        {
            "seriesNo": row.get("seriesNo"),
            "rowText": row.get("rowText"),
            "uoM": row.get("uoM"),
            "footnote": row.get("footnote") or None,
        }
        for row in records.get("row", [])
    ]
    return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    tables, failures, pulled = {}, [], []

    with requests.Session() as session:
        for table_id, resource_id in UPSTREAM_OF_DATAGOV.items():
            try:
                entry = summarise(metadata(session, table_id))
            except (requests.RequestException, SingStatError) as exc:
                failures.append((table_id, str(exc)))
                continue
            entry["role"] = "upstream of a section 8 data.gov.sg source, metadata only"
            entry["republished_on_datagov_as"] = resource_id
            tables[table_id] = entry

        for table_id, spec in ADOPTED.items():
            try:
                entry = summarise(metadata(session, table_id))
                data = tabledata(session, table_id)
            except (requests.RequestException, SingStatError) as exc:
                failures.append((table_id, str(exc)))
                continue

            filename = f"{spec['slug']}.json"
            payload = json.dumps(data, indent=2) + "\n"
            (args.out / filename).write_text(payload)

            first, last, longest = series_span(data)
            entry["role"] = spec["role"]
            entry["condition"] = spec["condition"]
            entry["file"] = filename
            entry["series_count"] = len(data["row"])
            entry["widest_span"] = f"{first} to {last}"
            entry["longest_series_periods"] = longest
            tables[table_id] = entry
            pulled.append((table_id, filename, len(payload), first, last))

    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/ingest/pull_singstat.py",
        "note": (
            "Metadata for every table listed. Values are pulled only for the tables adopted "
            "into section 8, and are saved as served in their own files."
        ),
        "tables": tables,
    }
    (args.out / METADATA_FILE).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nwrote {args.out / METADATA_FILE}\n")
    print(f"{'table':<10}{'coverage':<26}{'units seen'}")
    print("-" * 72)
    for table_id, entry in tables.items():
        units = sorted({s["uoM"] for s in entry["series"] if s["uoM"]})
        coverage = f"{entry['startPeriod']} to {entry['endPeriod']}"
        print(f"{table_id:<10}{coverage:<26}{', '.join(units)}")

    if pulled:
        print("\nvalues pulled:")
        for table_id, filename, size, first, last in pulled:
            print(f"  {table_id}  {filename}  {size} bytes  {first} to {last}")

    for table_id, error in failures:
        print(f"  {table_id} failed: {error}")

    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

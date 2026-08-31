"""Pull SingStat TableBuilder metadata for the tables behind the section 8 wide sources.

Run it:

    python -m src.ingest.pull_singstat

Four of the eight data.gov.sg sources are republished SingStat tables. data.gov.sg serves the
numbers without the units or the footnotes, and neither is recoverable from the CSV: the
public roads file gives 10,265 for 2025 with nothing saying what is being counted. SingStat
publishes both, so this pulls the metadata and commits it beside the data.

That is not a nicety. It is what the working rules mean by not inventing a number. A-15 was
opened because the lane-km unit was assumed rather than read, and it was closed by the
`uoM` field this script saves.

Two further tables are listed here as candidates. They are not section 8 sources and nothing
downstream reads them. They are pulled because section 8 makes a claim about one of them that
is wrong, and because the other is the ground truth for a validation the project has to run.
Whether either enters the brief is a decision for the stage 2 gate, not for this script.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

METADATA_URL = "https://tablebuilder.singstat.gov.sg/api/table/metadata/{table_id}"
TIMEOUT = 60

# TableBuilder rejects the default python-requests agent on some paths.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MOO-Policy-Analysis/0.1)"}

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_FILE = "singstat-metadata.json"

# SingStat table behind each section 8 wide source.
BEHIND_SECTION_8 = {
    "M651121": "d_22094bf608253d36c0c63b52d852dd6e",
    "M650341": "d_ede1a559013d10f234d209ac5e9fd9b4",
    "M650281": "d_529752a3d78beb78bd4f38e3be37f1b6",
    "M650321": "d_f73d13943f7a3cc1aca76b18fea75013",
}

# Not in section 8. Pulled as evidence for the stage 2 gate, not adopted.
CANDIDATES = {
    "M650291": (
        "Monthly deregistrations under the VQS, by category. Section 8 states deregistration "
        "counts are not published as a standalone series and stage 4 budgets a week to "
        "extract them from Annex A PDFs. This table is that series."
    ),
    "M130571": (
        "Government operating revenue, annual, including a Vehicle Quota Premiums line. "
        "Candidate ground truth for the A-10 reconciliation, which section 8 currently "
        "sources from the MOF Analysis of Revenue and Expenditure."
    ),
}

KEEP = ("id", "title", "frequency", "dataSource", "footnote",
        "dataLastUpdated", "startPeriod", "endPeriod")


def fetch(session, table_id):
    """Metadata for one table, flattened to the fields worth committing."""
    response = session.get(
        METADATA_URL.format(table_id=table_id), headers=HEADERS, timeout=TIMEOUT
    )
    response.raise_for_status()

    # The payload nests the record under Data.records. Reading Data directly yields a dict of
    # Nones rather than an error, which is a quiet way to record nothing at all.
    records = response.json().get("Data", {}).get("records")
    if not records:
        raise RuntimeError(f"{table_id} returned no records")

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

    tables, failures = {}, []
    with requests.Session() as session:
        for table_id, resource_id in BEHIND_SECTION_8.items():
            try:
                entry = fetch(session, table_id)
            except (requests.RequestException, RuntimeError) as exc:
                failures.append((table_id, str(exc)))
                continue
            entry["republished_on_datagov_as"] = resource_id
            entry["role"] = "source of a section 8 dataset"
            tables[table_id] = entry

        for table_id, why in CANDIDATES.items():
            try:
                entry = fetch(session, table_id)
            except (requests.RequestException, RuntimeError) as exc:
                failures.append((table_id, str(exc)))
                continue
            entry["role"] = "candidate, not in section 8"
            entry["why_pulled"] = why
            tables[table_id] = entry

    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/ingest/pull_singstat.py",
        "note": "Metadata only. No series values are pulled here.",
        "tables": tables,
    }
    (args.out / OUT_FILE).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nwrote {args.out / OUT_FILE}\n")
    print(f"{'table':<10}{'coverage':<26}{'units seen'}")
    print("-" * 72)
    for table_id, entry in tables.items():
        units = sorted({s["uoM"] for s in entry["series"] if s["uoM"]})
        coverage = f"{entry['startPeriod']} to {entry['endPeriod']}"
        print(f"{table_id:<10}{coverage:<26}{', '.join(units)}")

    for table_id, error in failures:
        print(f"  {table_id} failed: {error}")

    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

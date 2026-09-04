"""Pull the Vehicle Quota Premiums revenue line, the stage 3 reconciliation target.

Run it:

    python -m src.ingest.pull_revenue

Section 8 sources the reconciliation target from the MOF Analysis of Revenue and Expenditure,
which is a PDF. A-17 records that the same line is published as a machine-readable annual
series: SingStat TableBuilder table M130571, "Government Operating Revenue, Annual", series
1.2.1 "Vehicle Quota Premiums", in millions of dollars, sourced to the Accountant-General's
Department. This script pulls that one series and commits it.

Two things travel with the numbers and both matter downstream, so the metadata is written
beside the CSV rather than left on the table page:

The table footnote says which financial years are actual figures and which are revised or
budgeted estimates. `src/model/revenue.py` reads that sentence and refuses to reconcile
against a year that is not an actual, so the constraint is enforced by the data rather than by
a constant somebody has to remember to update.

The figures are financial years beginning 1 April, not calendar years. The column labels say
1997 and 2026 with no marking, so a reader who has not seen the footnote will align them
wrong. A-10 turns on getting that alignment right.

No credential is used. The TableBuilder endpoint is open.
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

TABLE_ID = "M130571"
SERIES_NO = "1.2.1"
TABLEDATA_URL = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/{table_id}"
TIMEOUT = 60

# TableBuilder rejects the default python-requests agent on some paths.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MOO-Policy-Analysis/0.1)"}

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CSV_FILE = "vehicle-quota-premiums-annual.csv"
META_FILE = "vehicle-quota-premiums-annual.meta.json"

# The sentence src/model/revenue.py parses out of the table footnote. Checked here so a
# footnote rewrite surfaces at the pull rather than at the reconciliation.
ACTUALS_SENTENCE = re.compile(r"Data up to FY(\d{4}) are actual figures")


def fetch(session, table_id=TABLE_ID, series_no=SERIES_NO):
    """The one series, with the table-level footnote it has to be read against."""
    response = session.get(
        TABLEDATA_URL.format(table_id=table_id),
        headers=HEADERS,
        params={"seriesNoORrowNo": series_no},
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    data = response.json().get("Data")
    if not data:
        raise RuntimeError(f"{table_id} returned no Data block")

    rows = [row for row in data.get("row", []) if row.get("seriesNo") == series_no]
    if len(rows) != 1:
        raise RuntimeError(
            f"{table_id} series {series_no}: expected one row, got {len(rows)}"
        )
    return data, rows[0]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path, row):
    """Values as published, in file order, no rounding and no type coercion."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["financial_year", "vehicle_quota_premiums_million"])
        for column in row.get("columns", []):
            writer.writerow([column["key"], column["value"]])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        try:
            data, row = fetch(session)
        except (requests.RequestException, RuntimeError) as exc:
            print(f"failed: {exc}", file=sys.stderr)
            return 1

    footnote = data.get("footnote") or ""
    match = ACTUALS_SENTENCE.search(footnote)
    if not match:
        print(
            "failed: the table footnote no longer says which years are actual figures.\n"
            "src/model/revenue.py reads that sentence to enforce the A-10 constraint, so it "
            "has to be read again by hand before this file is used.\n"
            f"footnote: {footnote}",
            file=sys.stderr,
        )
        return 1

    csv_path = args.out / CSV_FILE
    write_csv(csv_path, row)

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/ingest/pull_revenue.py",
        "endpoint": TABLEDATA_URL.format(table_id=TABLE_ID),
        "params": {"seriesNoORrowNo": SERIES_NO},
        "table": {
            "id": data.get("id"),
            "title": data.get("title"),
            "frequency": data.get("frequency"),
            "dataSource": data.get("datasource"),
            "dataLastUpdated": data.get("dataLastUpdated"),
            "footnote": footnote,
        },
        "series": {
            "seriesNo": row.get("seriesNo"),
            "rowText": row.get("rowText"),
            "uoM": row.get("uoM"),
            "footnote": row.get("footnote") or None,
        },
        "latest_actual_financial_year": int(match.group(1)),
        "file": CSV_FILE,
        "rows": len(row.get("columns", [])),
        "sha256": sha256(csv_path),
        "note": (
            "Financial years beginning 1 April, not calendar years. Figures after the latest "
            "actual year are revised or budgeted estimates and are not reconciliation "
            "targets. See A-10 and A-17."
        ),
    }
    (args.out / META_FILE).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {csv_path}")
    print(f"wrote {args.out / META_FILE}\n")
    print(f"{data.get('id')} series {row.get('seriesNo')}: {row.get('rowText')} "
          f"({row.get('uoM')})")
    # The tabledata payload carries no start and end period, unlike the metadata payload, so
    # coverage is read off the columns actually returned.
    periods = [column["key"] for column in row.get("columns", [])]
    print(f"coverage FY{min(periods)} to FY{max(periods)}, "
          f"actual figures up to FY{match.group(1)}")
    print(f"table last updated {data.get('dataLastUpdated')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

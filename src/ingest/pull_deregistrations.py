"""Pull the monthly deregistration series under the VQS, the stage 4 candidate.

Run it:

    python -m src.ingest.pull_deregistrations

Section 8 said deregistration counts are not published as a standalone series, and stage 4
budgeted a week to extract them from Annex A PDFs. A-16 found that SingStat table M650291,
"Motor Vehicles De-Registered Under Vehicle Quota System, Monthly", is that series: LTA-sourced,
1990 May onward, on the same VQS categories as the population and registration series. Stage 2
committed its metadata and no values. This pulls the values.

Whether it replaces the Annex A extraction or only checks it depends on two questions A-16
asks, and nothing here answers them. This script only puts the numbers where the comparison can
read them.

Written in the published shape, one row per series and one column per month, as the other
SingStat-derived files in `data/raw` are, with the table and series footnotes in a sidecar.
The footnotes matter here: the Category C series includes vehicles later placed under the
Early Turnover Scheme, and the total includes weekend cars and VQS-exempt vehicles.

No credential is used. The TableBuilder endpoint is open.
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

TABLE_ID = "M650291"
TABLEDATA_URL = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/{table_id}"
TIMEOUT = 60
PAGE_LIMIT = 5000

# TableBuilder rejects the default python-requests agent on some paths.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MOO-Policy-Analysis/0.1)"}

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CSV_FILE = "vqs-deregistrations-monthly.csv"
META_FILE = "vqs-deregistrations-monthly.meta.json"

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def fetch(session, table_id=TABLE_ID):
    response = session.get(
        TABLEDATA_URL.format(table_id=table_id),
        headers=HEADERS,
        params={"limit": PAGE_LIMIT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json().get("Data")
    if not data or not data.get("row"):
        raise RuntimeError(f"{table_id} returned no rows")
    return data


def period_key(label):
    """`2026 Jul` to (2026, 7). TableBuilder writes monthly keys with a space."""
    year, month = label.split()
    return int(year), MONTHS.index(month[:3]) + 1


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path, rows):
    """Published values as strings, newest month first, matching the data.gov.sg wide files."""
    periods = sorted(
        {column["key"] for row in rows for column in row["columns"]},
        key=period_key,
        reverse=True,
    )
    labels = [f"{period_key(p)[0]}{MONTHS[period_key(p)[1] - 1]}" for p in periods]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["DataSeries", *labels])
        for row in rows:
            values = {column["key"]: column["value"] for column in row["columns"]}
            writer.writerow([row["rowText"], *(values.get(p, "") for p in periods)])
    return periods


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        try:
            data = fetch(session)
        except (requests.RequestException, RuntimeError) as exc:
            print(f"failed: {exc}", file=sys.stderr)
            return 1

    rows = data["row"]
    csv_path = args.out / CSV_FILE
    periods = write_csv(csv_path, rows)

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/ingest/pull_deregistrations.py",
        "endpoint": TABLEDATA_URL.format(table_id=TABLE_ID),
        "table": {
            "id": data.get("id"),
            "title": data.get("title"),
            "frequency": data.get("frequency"),
            "dataSource": data.get("datasource"),
            "dataLastUpdated": data.get("dataLastUpdated"),
            "footnote": data.get("footnote"),
        },
        "series": [
            {
                "seriesNo": row.get("seriesNo"),
                "rowText": row.get("rowText"),
                "uoM": row.get("uoM"),
                "footnote": row.get("footnote") or None,
            }
            for row in rows
        ],
        "file": CSV_FILE,
        "rows": len(rows),
        "periods": len(periods),
        "period_first": min(periods, key=period_key),
        "period_last": max(periods, key=period_key),
        "sha256": sha256(csv_path),
        "note": (
            "Candidate stage 4 source, not yet adopted into section 8. Whether it is the "
            "quantity the quota formula's rolling average is built from, and whether it "
            "separates guaranteed deregistrations, is A-16's question and is answered against "
            "Annex A, not here."
        ),
    }
    (args.out / META_FILE).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {csv_path}")
    print(f"wrote {args.out / META_FILE}\n")
    print(f"{data.get('id')}: {data.get('title')}")
    print(f"{len(rows)} series, {len(periods)} months, "
          f"{meta['period_first']} to {meta['period_last']}")
    print(f"table last updated {data.get('dataLastUpdated')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

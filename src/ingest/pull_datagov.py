"""Stage 2 of docs/BUILD_SEQUENCE.md. Pull the data.gov.sg sources from section 8.

Run it:

    python -m src.ingest.pull_datagov              verify, download, write the manifest
    python -m src.ingest.pull_datagov --verify     verify only, touch nothing on disk

Each source is checked to still resolve, then downloaded to /data/raw as the CSV the portal
serves, then measured: row count, period range, and whether that range matches what section 8
claims. Results go to data/raw/manifest.json alongside the files, with a sha256 per file so a
later re-pull can be compared against what the fits were run on.

The stage 2 gate is knowing exactly what you have. A source that fails here is not worked
around and no substitute is invented for it. It is reported at the end under sources that
could not be reached, and the gate covers it.
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.ingest.datagov import (
    SourceError,
    ThrottledError,
    describe,
    download_published_csv,
    download_via_datastore,
)
from src.ingest.periods import covers, span
from src.ingest.sources import DATASTORE

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
MANIFEST = "manifest.json"
FIELD_LIST_LIMIT = 20


def read_periods(source, text):
    """Period labels in a raw CSV, taken from the column or the header as the shape requires."""
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    if source.shape == "wide":
        return [column for column in header if column != "DataSeries"]

    if source.period_field not in header:
        return []
    index = header.index(source.period_field)
    return sorted({row[index] for row in reader if len(row) > index})


def measure(source, payload):
    """What a downloaded file contains, and whether it matches section 8."""
    text = payload.decode("utf-8-sig")
    rows = max(text.count("\n") - 1, 0)
    if text and not text.endswith("\n"):
        rows += 1

    periods = read_periods(source, text)
    first, last, ordering = span(periods)

    record = {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": rows,
        "periods": len(periods),
        "period_first": first,
        "period_last": last,
        "period_ordering": ordering,
    }

    if source.claimed_start:
        record["claimed_start"] = source.claimed_start
        record["matches_claim"] = covers(first, source.claimed_start)
    return record


def pull_one(session, source, out_dir, verify_only):
    """Verify one source and, unless verifying only, download and measure it."""
    entry = {
        "key": source.key,
        "dataset_id": source.dataset_id,
        "title": source.title,
        "needed_for": list(source.needed_for),
    }

    try:
        described = describe(session, source.dataset_id)
    except ThrottledError as exc:
        entry["status"] = "throttled"
        entry["error"] = str(exc)
        return entry
    except (SourceError, requests.RequestException) as exc:
        entry["status"] = "unreachable"
        entry["error"] = str(exc)
        return entry

    entry["status"] = "resolves"
    entry["datastore_total"] = described["total"]
    entry["field_count"] = len(described["fields"])
    # On a wide table the fields are the period columns, so listing all several hundred of
    # them would restate the period range and bury every real change in the manifest diff.
    # The manifest is committed and meant to be read, so only a short field list is kept.
    if len(described["fields"]) <= FIELD_LIST_LIMIT:
        entry["fields"] = described["fields"]

    if verify_only:
        return entry

    try:
        payload = download_published_csv(session, source.dataset_id)
        entry["retrieved_via"] = "published-csv"
    except (SourceError, requests.RequestException) as exc:
        entry["published_csv_error"] = str(exc)
        try:
            payload = download_via_datastore(session, source.dataset_id)
            entry["retrieved_via"] = "datastore-rebuild"
        except ThrottledError as fallback_exc:
            entry["status"] = "throttled"
            entry["error"] = str(fallback_exc)
            return entry
        except (SourceError, requests.RequestException) as fallback_exc:
            entry["status"] = "unreachable"
            entry["error"] = str(fallback_exc)
            return entry

    filename = source.raw_filename
    (out_dir / filename).write_bytes(payload)
    entry["file"] = filename
    entry["status"] = "downloaded"
    entry.update(measure(source, payload))
    return entry


def report(entries, stream=sys.stdout):
    """The stage 2 gate, printed. What was pulled, and what section 8 gets wrong."""
    write = lambda line="": print(line, file=stream)

    write("")
    write(f"{'source':<36}{'status':<13}{'rows':>7}  coverage")
    write("-" * 92)
    for entry in entries:
        coverage = ""
        if entry.get("period_first"):
            coverage = f"{entry['period_first']} to {entry['period_last']}"
            if entry.get("period_ordering") == "file":
                coverage += " (file order)"
        write(
            f"{entry['key']:<36}{entry['status']:<13}"
            f"{entry.get('rows', ''):>7}  {coverage}"
        )

    mismatches = [e for e in entries if e.get("matches_claim") is False]
    unreachable = [e for e in entries if e["status"] == "unreachable"]
    throttled = [e for e in entries if e["status"] == "throttled"]
    rebuilt = [e for e in entries if e.get("retrieved_via") == "datastore-rebuild"]

    if mismatches:
        write("")
        write("Coverage narrower than section 8 claims:")
        for entry in mismatches:
            write(
                f"  {entry['key']}: section 8 says from {entry['claimed_start']}, "
                f"the file starts at {entry['period_first']}"
            )

    if rebuilt:
        write("")
        write("Rebuilt from datastore records rather than the published CSV:")
        for entry in rebuilt:
            write(f"  {entry['key']}: {entry.get('published_csv_error', '')}")

    if throttled:
        write("")
        write("Rate limited, not resolved either way. Re-run before concluding anything:")
        for entry in throttled:
            write(f"  {entry['key']} ({entry['dataset_id']}): {entry['error']}")

    if unreachable:
        write("")
        write("Could not be reached:")
        for entry in unreachable:
            write(f"  {entry['key']} ({entry['dataset_id']}): {entry['error']}")

    write("")
    return not unreachable and not throttled


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verify", action="store_true", help="check the ids resolve, download nothing"
    )
    parser.add_argument("--out", type=Path, default=RAW_DIR, help="output directory")
    args = parser.parse_args(argv)

    if not args.verify:
        args.out.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        entries = [pull_one(session, s, args.out, args.verify) for s in DATASTORE]

    if not args.verify:
        manifest = {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generated_by": "src/ingest/pull_datagov.py",
            "brief_section": "8",
            "sources": entries,
        }
        (args.out / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")

    return 0 if report(entries) else 1


if __name__ == "__main__":
    sys.exit(main())

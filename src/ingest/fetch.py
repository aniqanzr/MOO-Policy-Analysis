"""Stage 2 pull script for the open data.gov.sg sources.

Run from the repo root:

    python -m src.ingest.fetch              # resolve ids and download
    python -m src.ingest.fetch --check-only # resolve ids, download nothing
    python -m src.ingest.fetch --key coe_bidding_results

For each scriptable source it resolves the dataset id against the metadata endpoint, then
pages the datastore search endpoint until the record count is exhausted, writes the rows to
data/raw/<key>.csv and records what it got in data/raw/manifest.json. Sources listed as
manual or deferred in sources.py are never fetched; they are reported so the run ends with
an explicit list of what still has to be downloaded by hand.

No credential is read or required. Every endpoint here is open. See data/raw/README.md.

Nothing is invented. If a source cannot be reached, the manifest records the failure and the
file is left absent rather than partially written.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .sources import DATASTORE_SEARCH_URL, SCRIPTABLE, SOURCES, Source

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"

PAGE_SIZE = 5000
TIMEOUT_SECONDS = 60
RETRIES = 3
BACKOFF_SECONDS = 2.0


class FetchError(RuntimeError):
    """A source could not be retrieved. The caller records it and carries on."""


def _get(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET returning parsed JSON, retrying transport errors and 5xx only.

    A 4xx is not retried. On these endpoints it means the id is wrong or has moved, which
    is a stage 2 finding rather than a flake.
    """
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
            if 400 <= response.status_code < 500:
                raise FetchError(f"HTTP {response.status_code} from {response.url}")
            response.raise_for_status()
            return response.json()
        except FetchError:
            raise
        except Exception as exc:  # transport error or 5xx
            last = exc
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF_SECONDS * (2**attempt))
    raise FetchError(f"{url} failed after {RETRIES} attempts: {last}")


def resolve(source: Source) -> dict[str, Any]:
    """Confirm the dataset id resolves and return what the metadata endpoint says about it.

    This is the stage 2 gate for the scriptable half of section 8: every id must resolve.
    """
    payload = _get(source.metadata_url)
    data = payload.get("data", payload)
    return {
        "name": data.get("name"),
        "last_updated": data.get("lastUpdatedAt") or data.get("last_updated"),
        "status": data.get("status"),
        "columns": [c.get("name") for c in data.get("columnMetadata", {}).get("order", [])]
        if isinstance(data.get("columnMetadata"), dict)
        else None,
    }


def download(source: Source) -> tuple[list[dict[str, Any]], list[str]]:
    """Page the datastore endpoint until every record is retrieved.

    Returns the records and the field order the API reports, so the CSV keeps the published
    column order rather than whatever order a dict happens to have.
    """
    records: list[dict[str, Any]] = []
    fields: list[str] = []
    offset = 0
    total: int | None = None

    while True:
        payload = _get(
            DATASTORE_SEARCH_URL,
            params={"resource_id": source.dataset_id, "limit": PAGE_SIZE, "offset": offset},
        )
        if not payload.get("success", False):
            raise FetchError(f"{source.key}: datastore_search reported failure")
        result = payload["result"]
        if not fields:
            fields = [f["id"] for f in result.get("fields", []) if f["id"] != "_id"]
        if total is None:
            total = result.get("total")
        page = result.get("records", [])
        records.extend(page)
        offset += len(page)
        if not page or (total is not None and offset >= total):
            break

    if total is not None and len(records) != total:
        raise FetchError(
            f"{source.key}: API reported {total} records, retrieved {len(records)}"
        )
    return records, fields


def write_csv(source: Source, records: list[dict[str, Any]], fields: list[str]) -> Path:
    path = RAW_DIR / source.raw_filename
    if not fields:
        fields = sorted({k for r in records for k in r} - {"_id"})
    tmp = path.with_suffix(".csv.partial")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    tmp.replace(path)
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(keys: list[str] | None = None, check_only: bool = False) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    selected = [s for s in SCRIPTABLE if keys is None or s.key in keys]

    entries: list[dict[str, Any]] = []
    for source in selected:
        entry: dict[str, Any] = {
            "key": source.key,
            "title": source.title,
            "dataset_id": source.dataset_id,
            "method": source.method,
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        try:
            entry["metadata"] = resolve(source)
            entry["id_resolves"] = True
        except FetchError as exc:
            entry["id_resolves"] = False
            entry["error"] = str(exc)
            entries.append(entry)
            print(f"FAIL   {source.key}: {exc}", file=sys.stderr)
            continue

        if check_only:
            entry["downloaded"] = False
            entries.append(entry)
            print(f"OK     {source.key}: id resolves")
            continue

        try:
            records, fields = download(source)
            path = write_csv(source, records, fields)
            entry.update(
                downloaded=True,
                file=str(path.relative_to(RAW_DIR.parents[1])),
                rows=len(records),
                columns=fields,
                sha256=sha256(path),
                bytes=path.stat().st_size,
            )
            print(f"OK     {source.key}: {len(records)} rows -> {path.name}")
        except FetchError as exc:
            entry["downloaded"] = False
            entry["error"] = str(exc)
            print(f"FAIL   {source.key}: {exc}", file=sys.stderr)
        entries.append(entry)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "Written by src/ingest/fetch.py. Open endpoints only, no credential. Sources "
            "listed as manual or deferred are not fetched by this script."
        ),
        "datastore": entries,
        "manual": [
            {"key": s.key, "title": s.title, "url": s.url, "needed_for": list(s.needed_for)}
            for s in SOURCES
            if s.method == "manual"
        ],
        "singstat": [
            {"key": s.key, "title": s.title, "url": s.url, "needed_for": list(s.needed_for)}
            for s in SOURCES
            if s.method == "singstat"
        ],
        "deferred": [
            {"key": s.key, "title": s.title, "url": s.url, "reason": s.notes}
            for s in SOURCES
            if s.method == "deferred"
        ],
    }
    if keys is None:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", action="append", dest="keys", help="fetch one source only")
    parser.add_argument("--check-only", action="store_true", help="resolve ids, download nothing")
    args = parser.parse_args(argv)

    manifest = run(keys=args.keys, check_only=args.check_only)
    failed = [e for e in manifest["datastore"] if e.get("error")]

    print()
    print("Not fetched by this script:")
    for item in manifest["singstat"]:
        print(f"  singstat  {item['key']}  {item['url']}")
    for item in manifest["manual"]:
        print(f"  manual    {item['key']}  {item['url']}")
    for item in manifest["deferred"]:
        print(f"  deferred  {item['key']}  {item['url']}")
    if failed:
        print()
        print(f"{len(failed)} scriptable source(s) failed. Stage 2 gate is not passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

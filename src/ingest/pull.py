"""Pull the data.gov.sg sources in section 8 of the brief into data/raw.

Two things it does, and they are separable because stage 2 asks for both:

    python -m src.ingest.pull --verify     check every dataset ID still resolves
    python -m src.ingest.pull              verify, then download and write the manifest

Raw files are committed, so the pipeline reproduces from a clean clone and a later run can be
diffed against what was committed. The manifest records a SHA-256 for every file, which is how
a silent upstream revision gets noticed rather than quietly changing a fitted coefficient.

Sources that need a human are not downloaded and not guessed at. They are printed as a list.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.ingest.sources import API_SOURCES, MANUAL_SOURCES

BASE_URL = "https://api-open.data.gov.sg"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

TIMEOUT = 60
RETRIES = 4
BACKOFF = 2.0
POLL_ATTEMPTS = 10
POLL_WAIT = 3.0


class PullError(Exception):
    """A source could not be fetched. Carries the reason for the report."""


def _get(session, url, **kwargs):
    """GET with retries on transport errors and 5xx. Does not retry a 4xx."""
    last = None
    for attempt in range(RETRIES):
        try:
            response = session.get(url, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            last = f"{type(exc).__name__}: {exc}"
        else:
            if response.status_code < 500:
                return response
            last = f"HTTP {response.status_code}"
        if attempt < RETRIES - 1:
            time.sleep(BACKOFF * (2 ** attempt))
    raise PullError(f"{url} failed after {RETRIES} attempts, last error {last}")


def fetch_metadata(session, source, base_url=BASE_URL):
    """Confirm the dataset ID resolves and return what the API says about it."""
    url = f"{base_url}/v1/public/api/datasets/{source.dataset_id}/metadata"
    response = _get(session, url)
    if response.status_code == 404:
        raise PullError(
            f"dataset ID {source.dataset_id} does not resolve (HTTP 404). It has moved or been "
            f"withdrawn. Find the current ID, update section 8, note it in the decision log."
        )
    if response.status_code != 200:
        raise PullError(f"metadata returned HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError:
        raise PullError("metadata response was not JSON")
    if payload.get("code") != 0:
        raise PullError(f"API reported code {payload.get('code')}: {payload.get('errorMsg')}")
    return payload.get("data", {})


def fetch_download_url(session, source, base_url=BASE_URL):
    """Ask for a download link. The endpoint may need a few polls before the file is ready."""
    url = f"{base_url}/v1/public/api/datasets/{source.dataset_id}/poll-download"
    for attempt in range(POLL_ATTEMPTS):
        response = _get(session, url)
        if response.status_code != 200:
            raise PullError(f"poll-download returned HTTP {response.status_code}")
        payload = response.json()
        if payload.get("code") != 0:
            raise PullError(
                f"poll-download reported code {payload.get('code')}: {payload.get('errorMsg')}"
            )
        link = (payload.get("data") or {}).get("url")
        if link:
            return link
        if attempt < POLL_ATTEMPTS - 1:
            time.sleep(POLL_WAIT)
    raise PullError(f"poll-download gave no URL after {POLL_ATTEMPTS} attempts")


def download(session, source, out_dir, base_url=BASE_URL):
    """Fetch one source and write the file and its metadata. Returns a manifest row."""
    metadata = fetch_metadata(session, source, base_url)
    link = fetch_download_url(session, source, base_url)

    response = _get(session, link)
    if response.status_code != 200:
        raise PullError(f"file download returned HTTP {response.status_code} from {link}")
    body = response.content
    if not body:
        raise PullError("file download returned an empty body")

    csv_path = out_dir / f"{source.slug}.csv"
    csv_path.write_bytes(body)
    (out_dir / f"{source.slug}.metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )

    text = body.decode("utf-8", errors="replace")
    return {
        "slug": source.slug,
        "title": source.title,
        "dataset_id": source.dataset_id,
        "file": csv_path.name,
        "bytes": len(body),
        "lines": text.count("\n"),
        "sha256": hashlib.sha256(body).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def run(verify_only=False, out_dir=RAW_DIR, base_url=BASE_URL, sources=None):
    """Verify, optionally download, and return (manifest_rows, failures)."""
    sources = API_SOURCES if sources is None else sources
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, failures = [], []

    with requests.Session() as session:
        session.headers["User-Agent"] = "MOO-Policy-Analysis stage 2 ingestion"
        for source in sources:
            try:
                if verify_only:
                    fetch_metadata(session, source, base_url)
                    rows.append({
                        "slug": source.slug,
                        "title": source.title,
                        "dataset_id": source.dataset_id,
                        "resolved": True,
                    })
                else:
                    rows.append(download(session, source, out_dir, base_url))
            except PullError as exc:
                failures.append({
                    "slug": source.slug,
                    "title": source.title,
                    "dataset_id": source.dataset_id,
                    "error": str(exc),
                })

    if not verify_only:
        (out_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "base_url": base_url,
                    "sources": rows,
                    "failures": failures,
                },
                indent=2,
            )
            + "\n"
        )
    return rows, failures


def _report(rows, failures, verify_only):
    verb = "resolved" if verify_only else "downloaded"
    print(f"\n{len(rows)} of {len(rows) + len(failures)} data.gov.sg sources {verb}.")
    for row in rows:
        detail = "" if verify_only else f"  {row['bytes']:>9,} bytes  {row['lines']:>7,} lines"
        print(f"  ok    {row['slug']:<42}{detail}")
    for failure in failures:
        print(f"  FAIL  {failure['slug']:<42}  {failure['error']}")

    print(f"\n{len(MANUAL_SOURCES)} sources cannot be pulled by this script:")
    for source in MANUAL_SOURCES:
        key = f"  needs {source.needs_credential}" if source.needs_credential else ""
        print(f"  manual  {source.slug:<40}{key}")
        print(f"          {source.url}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="check every dataset ID resolves, download nothing")
    parser.add_argument("--out", type=Path, default=RAW_DIR, help="output directory")
    parser.add_argument("--base-url", default=BASE_URL, help="API base, for testing")
    args = parser.parse_args(argv)

    rows, failures = run(args.verify, args.out, args.base_url)
    _report(rows, failures, args.verify)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

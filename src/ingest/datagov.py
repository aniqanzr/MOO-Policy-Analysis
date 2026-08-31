"""Client for the two data.gov.sg endpoints this project pulls from.

Two endpoints are used, for different jobs.

`datastore_search` on data.gov.sg answers whether a resource id still resolves and what
fields it carries, without downloading anything. That is the stage 2 verification step.

`initiate-download` and `poll-download` on api-open.data.gov.sg return a signed link to the
CSV the portal itself serves. Pulling that file means /data/raw holds the same bytes a person
clicking Download on the portal would get, which is the provenance the reconciliation in
stage 3 needs.

The paginated datastore fallback exists because the download endpoints sit on a different
host and hand out short-lived S3 links, either of which can be blocked by a network policy
that still allows the datastore API. The fallback reconstructs the same table from the
datastore records. It is a reconstruction, not the published file, so which path produced a
file is recorded in the manifest rather than left implicit.

Both endpoints rate limit. Pulling all eight sources back to back returns 429 partway through,
so requests are spaced and 429 is retried with backoff. A 429 is a throttle, not a missing
resource, and the two are kept separate: reporting a throttled request as an id that no longer
resolves would send stage 2 looking for a replacement id that does not need replacing.
"""

import csv
import io
import time

import requests

DATASTORE_URL = "https://data.gov.sg/api/action/datastore_search"
INITIATE_URL = "https://api-open.data.gov.sg/v1/public/api/datasets/{rid}/initiate-download"
POLL_URL = "https://api-open.data.gov.sg/v1/public/api/datasets/{rid}/poll-download"

TIMEOUT = 60
# The portal builds the CSV on request. Observed turnaround is under a second, so this is
# headroom rather than a measured requirement.
POLL_ATTEMPTS = 10
POLL_INTERVAL = 2.0
# datastore_search caps a single response. 10000 is the documented ceiling.
PAGE_SIZE = 10000

# Spacing between requests, and the retry ladder for a throttled one. Both were set by
# watching where the unthrottled run started returning 429, not by picking round numbers.
REQUEST_SPACING = 1.5
RETRY_WAITS = (5.0, 15.0, 30.0, 60.0)
RETRY_CODES = frozenset({429, 500, 502, 503, 504})

_last_request = 0.0


class SourceError(RuntimeError):
    """A source did not return what was asked of it."""


class ThrottledError(SourceError):
    """The host kept rate limiting the request. Says nothing about whether the id is valid."""


def _space_requests():
    global _last_request
    gap = time.monotonic() - _last_request
    if gap < REQUEST_SPACING:
        time.sleep(REQUEST_SPACING - gap)
    _last_request = time.monotonic()


def _get(session, url, **kwargs):
    """GET with pacing, retrying the codes that mean try again rather than not here."""
    for attempt in range(len(RETRY_WAITS) + 1):
        _space_requests()
        response = session.get(url, timeout=TIMEOUT, **kwargs)
        if response.status_code not in RETRY_CODES:
            response.raise_for_status()
            return response
        if attempt < len(RETRY_WAITS):
            time.sleep(RETRY_WAITS[attempt])

    raise ThrottledError(
        f"{url.split('?')[0]} returned {response.status_code} on every attempt"
    )


def describe(session, resource_id):
    """Confirm a resource id resolves and report what is behind it.

    Returns the total row count and the field list. Raises SourceError if the id no longer
    resolves, which is the stage 2 failure the build sequence asks to be told about.
    """
    try:
        response = _get(
            session, DATASTORE_URL, params={"resource_id": resource_id, "limit": 1}
        )
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            raise SourceError(f"{resource_id} no longer resolves: 404 from the datastore") from exc
        raise SourceError(f"{resource_id} datastore request failed: {exc}") from exc

    payload = response.json()
    if not payload.get("success"):
        raise SourceError(f"{resource_id} returned success=false: {payload}")

    result = payload["result"]
    return {
        "total": result.get("total"),
        "fields": [f["id"] for f in result["fields"] if f["id"] != "_id"],
    }


def download_published_csv(session, resource_id):
    """Fetch the CSV the portal serves, as bytes.

    Two steps. The initiate call builds the file and returns a link, the poll call reports
    when that link is ready. Both return a link, and in practice the first one already works,
    but the documented sequence is followed rather than relying on that.
    """
    initiate = _get(session, INITIATE_URL.format(rid=resource_id)).json()
    if "data" not in initiate:
        raise SourceError(f"{resource_id} initiate-download returned {initiate}")

    url = None
    for attempt in range(POLL_ATTEMPTS):
        poll = _get(session, POLL_URL.format(rid=resource_id)).json()
        data = poll.get("data", {})
        if data.get("status") == "DOWNLOAD_SUCCESS" and data.get("url"):
            url = data["url"]
            break
        if attempt < POLL_ATTEMPTS - 1:
            time.sleep(POLL_INTERVAL)

    if url is None:
        url = initiate["data"].get("url")
    if url is None:
        raise SourceError(f"{resource_id} download never became ready")

    return _get(session, url).content


def download_via_datastore(session, resource_id):
    """Rebuild the table from paginated datastore records, as CSV bytes.

    Column order follows the field order the API reports, so it matches the published CSV.
    The internal `_id` column is dropped because it is a datastore row key, not data.
    """
    offset = 0
    fields = None
    rows = []

    while True:
        payload = _get(
            session,
            DATASTORE_URL,
            params={"resource_id": resource_id, "limit": PAGE_SIZE, "offset": offset},
        ).json()
        if not payload.get("success"):
            raise SourceError(f"{resource_id} returned success=false: {payload}")

        result = payload["result"]
        if fields is None:
            fields = [f["id"] for f in result["fields"] if f["id"] != "_id"]

        records = result.get("records", [])
        rows.extend(records)
        offset += len(records)
        if not records or offset >= result.get("total", 0):
            break

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")

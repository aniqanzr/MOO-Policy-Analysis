"""Client for the SingStat TableBuilder API.

Two endpoints. `metadata` gives units, footnotes, coverage and the series list without any
values. `tabledata` gives the same header plus every observation, in one response per table
with no pagination at the sizes this project pulls.

SingStat matters here for two separate reasons and they are worth keeping straight.

For the four section 8 sources that are republished SingStat tables, it is the upstream. It
carries the units and footnotes data.gov.sg strips, and it runs ahead of the republication by
up to six months. Only metadata is pulled for those, because the values are already committed
from data.gov.sg and having two copies of the same series invites reading the wrong one.

For the two tables adopted at the stage 2 gate, M650291 and M130571, it is the source itself,
and both metadata and values are pulled.

Responses are saved as served. The JSON carries per-series footnotes that no CSV reshaping of
it would keep, and those footnotes are what closed A-15 and bounded A-10.
"""

import time

import requests

from src.ingest.periods import period_key

METADATA_URL = "https://tablebuilder.singstat.gov.sg/api/table/metadata/{table_id}"
TABLEDATA_URL = "https://tablebuilder.singstat.gov.sg/api/table/tabledata/{table_id}"

TIMEOUT = 90

# TableBuilder answers 403 to the default python-requests agent on some paths. So do
# mof.gov.sg and mot.gov.sg. A script that reports those as unreachable is describing its own
# headers rather than the site.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MOO-Policy-Analysis/0.1)"}

REQUEST_SPACING = 1.0
RETRY_WAITS = (5.0, 15.0, 30.0)
RETRY_CODES = frozenset({429, 500, 502, 503, 504})

_last_request = 0.0


class SingStatError(RuntimeError):
    """TableBuilder did not return what was asked of it."""


def _get(session, url):
    global _last_request
    for attempt in range(len(RETRY_WAITS) + 1):
        gap = time.monotonic() - _last_request
        if gap < REQUEST_SPACING:
            time.sleep(REQUEST_SPACING - gap)
        _last_request = time.monotonic()

        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code not in RETRY_CODES:
            response.raise_for_status()
            return response
        if attempt < len(RETRY_WAITS):
            time.sleep(RETRY_WAITS[attempt])

    raise SingStatError(f"{url} returned {response.status_code} on every attempt")


def metadata(session, table_id):
    """Table metadata. Units, footnotes, coverage and the series list, no values."""
    payload = _get(session, METADATA_URL.format(table_id=table_id)).json()

    # The metadata payload nests the record one level deeper than tabledata does. Reading
    # Data directly yields a dict of Nones rather than raising, which is a quiet way to
    # record nothing at all, so the shape is checked rather than assumed.
    records = payload.get("Data", {}).get("records")
    if not records:
        raise SingStatError(f"{table_id} metadata returned no records")
    return records


def tabledata(session, table_id):
    """The full table, header and every observation, as served."""
    payload = _get(session, TABLEDATA_URL.format(table_id=table_id)).json()
    data = payload.get("Data")
    if not data or not data.get("row"):
        raise SingStatError(f"{table_id} tabledata returned no rows")
    return data


def series_span(data):
    """Widest period range across the series in a tabledata payload.

    Series inside one table do not always share a range. In M650291 the weekend and off-peak
    car line stops in 1998 while the rest run to 2026, so a single first and last taken from
    the first series would misstate the table.
    """
    firsts, lasts, lengths = [], [], []
    for row in data["row"]:
        columns = row.get("columns") or []
        if not columns:
            continue
        firsts.append(columns[0]["key"])
        lasts.append(columns[-1]["key"])
        lengths.append(len(columns))

    if not firsts:
        return None, None, 0

    # Sorted on the parsed date, not the label. SingStat writes "1990 May", and comparing
    # those as strings puts June before May.
    return (min(firsts, key=period_key), max(lasts, key=period_key), max(lengths))

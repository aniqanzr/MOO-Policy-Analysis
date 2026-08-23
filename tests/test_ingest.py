"""Stage 2. Checks the pull script's behaviour against a local stub of the data.gov.sg API.

The real API is not reachable from this environment, so these tests stand a stub in its place
and exercise the paths that matter: a dataset that resolves, one that does not, an endpoint
that makes you poll, and one that fails before recovering. They check the script, not the data.
A green run here says nothing about whether the dataset IDs in section 8 are still live. Only
`python -m src.ingest.pull --verify` against the real API answers that.
"""

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src.ingest import pull
from src.ingest.sources import Source

GOOD_ID = "d_" + "a" * 32
MISSING_ID = "d_" + "b" * 32
POLLING_ID = "d_" + "c" * 32
FLAKY_ID = "d_" + "d" * 32

PAYLOAD = b"year,category,quota,premium\n2025,A,1000,100000\n"


class _Stub(BaseHTTPRequestHandler):
    poll_counts = {}
    flaky_counts = {}

    def log_message(self, *args):
        pass

    def _json(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = self.path
        if path == "/file.csv":
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD)
            return

        dataset_id = path.split("/datasets/")[1].split("/")[0] if "/datasets/" in path else ""

        if dataset_id == MISSING_ID:
            self._json(404, {"code": 4, "errorMsg": "not found"})
            return

        if dataset_id == FLAKY_ID and path.endswith("/metadata"):
            n = self.flaky_counts.get(FLAKY_ID, 0)
            self.flaky_counts[FLAKY_ID] = n + 1
            if n == 0:
                self._json(503, {"code": 5, "errorMsg": "unavailable"})
                return

        if path.endswith("/metadata"):
            self._json(200, {"code": 0, "data": {"datasetMetadata": {"name": dataset_id}}})
            return

        if path.endswith("/poll-download"):
            if dataset_id == POLLING_ID:
                n = self.poll_counts.get(POLLING_ID, 0)
                self.poll_counts[POLLING_ID] = n + 1
                if n < 2:
                    self._json(200, {"code": 0, "data": {}})
                    return
            base = f"http://127.0.0.1:{self.server.server_address[1]}"
            self._json(200, {"code": 0, "data": {"url": f"{base}/file.csv"}})
            return

        self._json(404, {"code": 4, "errorMsg": "unknown path"})


@pytest.fixture
def stub_api(monkeypatch):
    monkeypatch.setattr(pull, "BACKOFF", 0.0)
    monkeypatch.setattr(pull, "POLL_WAIT", 0.0)
    _Stub.poll_counts.clear()
    _Stub.flaky_counts.clear()
    server = HTTPServer(("127.0.0.1", 0), _Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _source(slug, dataset_id):
    return Source(slug=slug, title=slug, group="test", dataset_id=dataset_id)


def test_downloads_and_records_a_checksum(stub_api, tmp_path):
    rows, failures = pull.run(
        out_dir=tmp_path, base_url=stub_api, sources=[_source("good", GOOD_ID)]
    )

    assert failures == []
    assert (tmp_path / "good.csv").read_bytes() == PAYLOAD
    assert json.loads((tmp_path / "good.metadata.json").read_text())["datasetMetadata"]

    row = rows[0]
    assert row["sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
    assert row["bytes"] == len(PAYLOAD)
    assert row["lines"] == 2


def test_manifest_lists_every_source_and_failure(stub_api, tmp_path):
    pull.run(
        out_dir=tmp_path,
        base_url=stub_api,
        sources=[_source("good", GOOD_ID), _source("gone", MISSING_ID)],
    )

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert [s["slug"] for s in manifest["sources"]] == ["good"]
    assert [f["slug"] for f in manifest["failures"]] == ["gone"]
    assert manifest["base_url"] == stub_api
    assert manifest["generated_at"].endswith("+00:00")


def test_a_moved_dataset_id_is_reported_not_raised(stub_api, tmp_path):
    """A 404 is the case the brief warns about, so it has to survive into the report."""
    rows, failures = pull.run(
        out_dir=tmp_path, base_url=stub_api, sources=[_source("gone", MISSING_ID)]
    )

    assert rows == []
    assert len(failures) == 1
    assert MISSING_ID in failures[0]["error"]
    assert "does not resolve" in failures[0]["error"]
    assert not (tmp_path / "gone.csv").exists(), "nothing should be written for a failed pull"


def test_verify_only_touches_no_files(stub_api, tmp_path):
    rows, failures = pull.run(
        verify_only=True, out_dir=tmp_path, base_url=stub_api,
        sources=[_source("good", GOOD_ID)],
    )

    assert failures == []
    assert rows[0]["resolved"] is True
    assert list(tmp_path.iterdir()) == []


def test_polls_until_the_download_url_appears(stub_api, tmp_path):
    rows, failures = pull.run(
        out_dir=tmp_path, base_url=stub_api, sources=[_source("slow", POLLING_ID)]
    )

    assert failures == []
    assert rows[0]["bytes"] == len(PAYLOAD)
    assert _Stub.poll_counts[POLLING_ID] == 3, "should have polled through the empty responses"


def test_retries_a_server_error(stub_api, tmp_path):
    rows, failures = pull.run(
        out_dir=tmp_path, base_url=stub_api, sources=[_source("flaky", FLAKY_ID)]
    )

    assert failures == []
    assert _Stub.flaky_counts[FLAKY_ID] == 2, "should have retried past the 503"

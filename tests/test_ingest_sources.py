"""Checks on the stage 2 source registry.

Two things are worth a test rather than a reading. The registry has to stay consistent with
what `fetch.py` assumes about it, and the no-credential rule has to be enforced by something
other than a paragraph in a README, because the failure mode is a future session helpfully
adding a key read.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ingest import sources as S

INGEST_DIR = Path(S.__file__).parent
CREDENTIAL_READS = {"getenv", "environ", "load_dotenv", "dotenv_values"}


def test_keys_are_unique():
    keys = [s.key for s in S.SOURCES]
    assert len(keys) == len(set(keys))


KNOWN_METHODS = {"datastore", "singstat", "annexa", "manual", "deferred"}


def test_methods_are_known():
    assert {s.method for s in S.SOURCES} <= KNOWN_METHODS


def test_dataset_ids_belong_to_datastore_sources_only():
    for source in S.SOURCES:
        if source.method == "datastore":
            assert source.dataset_id, f"{source.key} is scriptable but has no dataset id"
            assert source.dataset_id.startswith("d_")
        else:
            assert source.dataset_id is None, f"{source.key} is not scriptable but has an id"


def test_dataset_ids_are_unique():
    ids = [s.dataset_id for s in S.SOURCES if s.dataset_id]
    assert len(ids) == len(set(ids))


def test_table_ids_belong_to_singstat_sources_only():
    for source in S.SOURCES:
        if source.method == "singstat":
            assert source.table_id, f"{source.key} is a SingStat source with no table id"
            assert source.table_id.startswith("M")
        else:
            assert source.table_id is None, f"{source.key} is not SingStat but has a table id"


def test_table_ids_are_unique():
    ids = [s.table_id for s in S.SOURCES if s.table_id]
    assert len(ids) == len(set(ids))


def test_scriptable_sources_record_what_was_actually_pulled():
    """Stage 2 pulled every scriptable source, so each one knows its own coverage.

    The point is not the string. It is that a source cannot be marked scriptable on the
    strength of an id resolving, without anyone having looked at what came back.
    """
    for source in S.SCRIPTABLE:
        assert source.coverage.strip(), f"{source.key} is scriptable but records no coverage"


def test_claimed_coverage_is_only_recorded_where_section_8_claimed_something():
    """`claimed_start` exists to flag drift, so it belongs only on sources with a claim."""
    for source in S.SOURCES:
        if source.claimed_start:
            assert source.method == "datastore", (
                f"{source.key} records a section 8 coverage claim but is not pulled from "
                "data.gov.sg, so nothing checks it"
            )


def test_every_source_says_what_needs_it_and_carries_a_note():
    for source in S.SOURCES:
        assert source.needed_for, f"{source.key} names no consumer"
        assert source.notes.strip(), f"{source.key} has no note"


def test_datamall_is_deferred_not_authenticated():
    """The one source that needs an account key stays deferred. See CLAUDE.md."""
    assert S.by_key("lta_datamall_mvp01_mvp02").method == "deferred"


@pytest.mark.parametrize("path", sorted(INGEST_DIR.glob("*.py")), ids=lambda p: p.name)
def test_ingest_reads_no_credential(path: Path):
    """No module under src/ingest reads an environment variable or a dotenv file.

    Docstrings and comments are free to mention them, and they do, to say not to. This walks
    the syntax tree so only real name references count.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in CREDENTIAL_READS:
            pytest.fail(f"{path.name} reads {node.attr}")
        if isinstance(node, ast.Name) and node.id in CREDENTIAL_READS:
            pytest.fail(f"{path.name} reads {node.id}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names]
            module = getattr(node, "module", None) or ""
            assert "dotenv" not in module and not any("dotenv" in n for n in names), (
                f"{path.name} imports dotenv"
            )

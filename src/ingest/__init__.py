"""Stage 2 ingestion: the source registry and the data.gov.sg pull script.

Section 8 of docs/PROJECT_BRIEF.md names every dataset. `sources.py` restates that list in
one machine-readable place so the pull script and `data/raw/README.md` cannot drift apart
from it. `fetch.py` pulls the scriptable ones and records what it got.

No credential is read, stored or required anywhere in this package. Sources that need one
are deferred, not authenticated. See `data/raw/README.md`.
"""

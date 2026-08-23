"""Data ingestion. Stage 2 of docs/BUILD_SEQUENCE.md.

Pulls the data.gov.sg sources named in section 8 of the brief into data/raw and records what
was fetched. Sources that cannot be pulled over an API, the Annex A press releases, the MOF
revenue tables and the LTA Annual Vehicle Statistics, are listed in the same registry and
marked as manual so the list of what must be downloaded by hand is generated rather than
remembered.

Section 7 of the brief does not name this directory. Added as the stage before src/fit, with
the reason in docs/decision-log.md.
"""

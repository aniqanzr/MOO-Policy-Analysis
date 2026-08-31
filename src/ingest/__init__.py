"""Scripted pulls of the raw sources listed in section 8 of docs/PROJECT_BRIEF.md.

Nothing in this package cleans, reshapes or interprets anything. It fetches published files
as they are served, writes them to /data/raw unchanged, and records what was fetched. Cleaning
happens downstream against the committed bytes, so a clean clone reproduces the pipeline
without hitting the network again.
"""

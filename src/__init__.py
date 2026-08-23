"""Build pipeline for the COE multi-objective model.

Section 7 of docs/PROJECT_BRIEF.md sets the layout. Python computes the frontier, the
feasible cloud, the weight simplex map and the sensitivity bands offline and writes JSON.
The frontend in /web loads that JSON. There is no server.
"""

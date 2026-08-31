"""The data.gov.sg sources named in section 8 of docs/PROJECT_BRIEF.md.

One entry per resource id in section 8. `claimed_start` is what section 8 says about coverage,
written down here so the pull script can check it rather than leaving it to be noticed by eye.
Where section 8 makes no coverage claim the field is None and nothing is checked.

Tables on data.gov.sg come in two shapes and the difference matters for reading coverage off a
file. Long tables carry the period in a column. Wide tables, which are the SingStat extracts,
carry one column per period and the series names down the first column.
"""

from dataclasses import dataclass

LONG = "long"
WIDE = "wide"


@dataclass(frozen=True)
class Source:
    slug: str
    resource_id: str
    title: str
    shape: str
    period_field: str = ""
    claimed_start: str = ""
    note: str = ""


SOURCES = (
    Source(
        slug="coe-bidding-results",
        resource_id="d_69b3380ad7e51aff3a7dcc84eba52b8a",
        title="COE bidding results and prices",
        shape=LONG,
        period_field="month",
        claimed_start="2002-04",
        note="Section 8 COE and quota. One row per category per exercise.",
    ),
    Source(
        slug="quota-premium-monthly",
        resource_id="d_22094bf608253d36c0c63b52d852dd6e",
        title="Motor vehicle quota, quota premium and prevailing quota premium, monthly",
        shape=WIDE,
        claimed_start="",
        note=(
            "Section 8 COE and quota. SingStat and LTA. Section 8 says this carries the 2002 "
            "and 2020 footnotes."
        ),
    ),
    Source(
        slug="vehicle-population-annual",
        resource_id="d_2873f3b1b2a836103f51f696350b98fa",
        title="Annual motor vehicle population by type",
        shape=LONG,
        period_field="year",
        note="Section 8 vehicle population and registrations.",
    ),
    Source(
        slug="vehicle-population-monthly",
        resource_id="d_2ecb009f1e1ec5a816a454944dec4022",
        title="Monthly motor vehicle population by type",
        shape=LONG,
        period_field="month",
        note="Section 8 vehicle population and registrations.",
    ),
    Source(
        slug="vqs-population-monthly",
        resource_id="d_ede1a559013d10f234d209ac5e9fd9b4",
        title="Motor vehicle population under the Vehicle Quota System, monthly",
        shape=WIDE,
        note="Section 8 vehicle population and registrations.",
    ),
    Source(
        slug="vqs-new-registrations-monthly",
        resource_id="d_529752a3d78beb78bd4f38e3be37f1b6",
        title="New registration of motor vehicles under the VQS, monthly",
        shape=WIDE,
        note="Section 8 vehicle population and registrations.",
    ),
    Source(
        slug="peak-hour-speed-annual",
        resource_id="d_26f6afadf2f86b2004f9a1e28f5564cc",
        title="Average speed during peak hours",
        shape=LONG,
        period_field="year",
        claimed_start="2004",
        note="Section 8 congestion. Expressway and arterial split.",
    ),
    Source(
        slug="public-roads-annual",
        resource_id="d_f73d13943f7a3cc1aca76b18fea75013",
        title="Public roads, annual",
        shape=WIDE,
        claimed_start="1990",
        note="Section 8 congestion. Section 8 describes this as lane-km by road category.",
    ),
)

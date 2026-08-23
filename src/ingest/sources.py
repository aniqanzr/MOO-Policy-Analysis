"""Every source in section 8 of docs/PROJECT_BRIEF.md, as a registry.

One place that says what the project needs, where it comes from, and whether a script can get
it. The pull script reads this, and so does the list of manual downloads. Keeping both off one
registry means the two cannot drift apart.

Dataset IDs are transcribed from section 8. The brief says to re-check them before relying on
them, since IDs and coverage change. `pull.py --verify` is what does that.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    slug: str                 # file name stem under data/raw
    title: str                # as named in section 8
    group: str                # section 8 heading
    dataset_id: str = ""      # data.gov.sg dataset ID, empty when not applicable
    manual: bool = False      # cannot be pulled by this script
    url: str = ""             # where a human goes to get it, or the API landing page
    needs_credential: str = "" # env var holding the key, when one is required
    note: str = ""
    used_for: str = ""        # which part of the model consumes it


# Pulled by the script over the data.gov.sg public API.
API_SOURCES = [
    Source(
        slug="coe-bidding-results",
        title="COE bidding results and prices",
        group="COE and quota",
        dataset_id="d_69b3380ad7e51aff3a7dcc84eba52b8a",
        note="One row per category per exercise from April 2002. Fields include bidding "
             "period, exercise number, category, quota, bids received, quota premium.",
        used_for="4.1 premium fits, 4.4 revenue reconciliation",
    ),
    Source(
        slug="motor-vehicle-quota-and-premium-monthly",
        title="Motor vehicle quota, quota premium and prevailing quota premium, monthly",
        group="COE and quota",
        dataset_id="d_22094bf608253d36c0c63b52d852dd6e",
        note="Carries the 2002 and 2020 footnotes. Cross-check against the bidding results.",
        used_for="4.1, break table",
    ),
    Source(
        slug="motor-vehicle-population-annual",
        title="Annual motor vehicle population by type",
        group="Vehicle population and registrations",
        dataset_id="d_2873f3b1b2a836103f51f696350b98fa",
        used_for="4.2 accumulator backtest",
    ),
    Source(
        slug="motor-vehicle-population-monthly",
        title="Monthly motor vehicle population by type",
        group="Vehicle population and registrations",
        dataset_id="d_2ecb009f1e1ec5a816a454944dec4022",
        used_for="4.2 accumulator backtest",
    ),
    Source(
        slug="vqs-population-monthly",
        title="Motor vehicle population under the Vehicle Quota System, monthly",
        group="Vehicle population and registrations",
        dataset_id="d_ede1a559013d10f234d209ac5e9fd9b4",
        used_for="4.2, category-level population",
    ),
    Source(
        slug="vqs-new-registrations-monthly",
        title="New registration of motor vehicles under the VQS, monthly",
        group="Vehicle population and registrations",
        dataset_id="d_529752a3d78beb78bd4f38e3be37f1b6",
        used_for="4.2 accumulator inflow",
    ),
    Source(
        slug="peak-hour-average-speed",
        title="Average speed during peak hours",
        group="Congestion",
        dataset_id="d_26f6afadf2f86b2004f9a1e28f5564cc",
        note="Annual from 2004, expressway and arterial split. Peak hour is 8 to 9am and "
             "6 to 7pm on weekdays. Roughly twenty observations, which is why A-09 exists.",
        used_for="4.3 BPR calibration",
    ),
    Source(
        slug="public-roads-annual",
        title="Public roads, annual",
        group="Congestion",
        dataset_id="d_f73d13943f7a3cc1aca76b18fea75013",
        note="Lane-km by road category from 1990. Covers only LTA-maintained roads. Watch the "
             "2023 to 2024 jump, which looks like reclassification rather than construction.",
        used_for="4.3 capacity anchor",
    ),
]

# Everything the script cannot get. These are the hand-download list.
MANUAL_SOURCES = [
    Source(
        slug="lta-quota-press-releases-annex-a",
        title="LTA quarterly quota press releases, with Annex A",
        group="COE and quota",
        manual=True,
        url="https://www.lta.gov.sg/content/ltagov/en/newsroom.html",
        note="Authoritative source for the quota formula in 3.1 and for deregistration counts. "
             "Stage 4 needs eight to twelve of these straddling the regime changes plus recent "
             "quarters, not one.",
        used_for="3.1 quota formula, stage 4 deregistration extraction",
    ),
    Source(
        slug="lta-annual-vehicle-statistics",
        title="LTA Annual Vehicle Statistics",
        group="Vehicle population and registrations",
        manual=True,
        url="https://www.lta.gov.sg/content/ltagov/en/who_we_are/statistics_and_publications/"
            "statistics.html",
        note="Deregistration counts are not published as a standalone series. They appear here "
             "and inside the Annex A arithmetic.",
        used_for="stage 4 deregistration extraction",
    ),
    Source(
        slug="lta-datamall-mvp01-mvp02",
        title="LTA DataMall static data, MVP01 and MVP02",
        group="Vehicle population and registrations",
        manual=True,
        url="https://datamall.lta.gov.sg/content/datamall/en/static-data.html",
        needs_credential="LTA_DATAMALL_ACCOUNT_KEY",
        note="Requires a DataMall account key. Includes COE revalidation counts, which 4.2 "
             "needs because renewals break the clean ten year window. Registration is free but "
             "cannot be scripted from a clean clone.",
        used_for="4.2 renewals and revalidation",
    ),
    Source(
        slug="mof-analysis-of-revenue-and-expenditure",
        title="MOF Analysis of Revenue and Expenditure",
        group="Revenue",
        manual=True,
        url="https://www.mof.gov.sg/singaporebudget/revenue-and-expenditure",
        note="The Vehicle Quota Premiums line under Operating Revenue. Published as annual "
             "Budget PDFs, one per fiscal year, no API. Stage 3 needs several years.",
        used_for="4.4 revenue reconciliation, gate A-10",
    ),
    Source(
        slug="mot-parliamentary-replies",
        title="MOT newsroom Parliamentary replies and ministerial statements",
        group="Policy context",
        manual=True,
        url="https://www.mot.gov.sg/news",
        note="Policy mechanics and the stated purpose of the scheme. Cited in the assumptions "
             "register rather than parsed. Not a data pull.",
        used_for="assumptions register sourcing",
    ),
    Source(
        slug="nlb-infopedia-select-committee",
        title="NLB Infopedia, 1990 Select Committee on Land Transport",
        group="Policy context",
        manual=True,
        url="https://www.nlb.gov.sg/main/article-detail?cmsuuid=",
        note="History of the scheme's stated purpose. Cited, not parsed.",
        used_for="assumptions register sourcing",
    ),
]

ALL_SOURCES = API_SOURCES + MANUAL_SOURCES

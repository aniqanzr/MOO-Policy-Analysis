"""The section 8 source list, in one place.

Every dataset the build needs, with how it is obtained. Four methods:

`datastore`  pulled by `fetch.py` from the data.gov.sg datastore API, no credential.
`singstat`   pulled from the SingStat TableBuilder API by its own script, no credential.
`manual`     a PDF or a table with no open API. Downloaded by hand and committed.
`deferred`   not obtained, and not needed unless a later stage proves otherwise.

Credentials
-----------
Nothing here reads an environment variable, a `.env` file or a key file, and nothing should
be added that does. This repo is public and the build runs in Claude Code on the web, where
there is no durable local filesystem to keep a key out of git and where environment
variables are visible to anyone using the environment. A source that requires an account key
is `deferred`. If it later turns out to be needed, the files are downloaded by hand outside
this repo and the resulting data files are committed. See `data/raw/README.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

# Landing pages for the manual and deferred sources are site roots rather than deep links.
# Egress to every one of these hosts was blocked when this file was written, so a deep link
# could not be checked and an unchecked one is worse than none. Navigate from the root and
# record the document URL in data/raw/README.md when a file is downloaded by hand.

DATASTORE_SEARCH_URL = "https://data.gov.sg/api/action/datastore_search"
DATASET_METADATA_URL = "https://api-production.data.gov.sg/v2/public/api/datasets/{dataset_id}/metadata"


@dataclass(frozen=True)
class Source:
    """One dataset from section 8 of the brief.

    key         short name, also the stem of the file written under data/raw
    title       the dataset as section 8 names it
    method      datastore | singstat | manual | deferred
    dataset_id  data.gov.sg dataset id, for datastore sources only
    url         where a human goes to get it, or the API endpoint
    needed_for  the build stages that consume it
    notes       anything a future session would otherwise have to rediscover
    """

    key: str
    title: str
    method: str
    url: str
    needed_for: tuple[str, ...]
    notes: str
    dataset_id: str | None = None

    @property
    def raw_filename(self) -> str:
        return f"{self.key}.csv"

    @property
    def metadata_url(self) -> str:
        if self.dataset_id is None:
            raise ValueError(f"{self.key} has no dataset id, so it has no metadata endpoint")
        return DATASET_METADATA_URL.format(dataset_id=self.dataset_id)


SOURCES: tuple[Source, ...] = (
    # COE and quota
    Source(
        key="coe_bidding_results",
        title="COE bidding results and prices, LTA",
        method="datastore",
        dataset_id="d_69b3380ad7e51aff3a7dcc84eba52b8a",
        url="https://data.gov.sg/datasets/d_69b3380ad7e51aff3a7dcc84eba52b8a/view",
        needed_for=("3 revenue reconciliation", "6 premium fits"),
        notes=(
            "One row per category per exercise from April 2002. Carries bidding period, "
            "exercise number, category, quota, bids received and quota premium. This is the "
            "spine of the premium fit and of the revenue reconciliation."
        ),
    ),
    Source(
        key="quota_and_premium_monthly",
        title="Motor vehicle quota, quota premium and prevailing quota premium, monthly",
        method="datastore",
        dataset_id="d_22094bf608253d36c0c63b52d852dd6e",
        url="https://data.gov.sg/datasets/d_22094bf608253d36c0c63b52d852dd6e/view",
        needed_for=("6 premium fits", "7 accumulator"),
        notes=(
            "SingStat and LTA. Carries the 2002 and 2020 footnotes, so read the footnotes "
            "before treating a gap as missing data. Prevailing quota premium is the renewal "
            "price, which A-04 needs."
        ),
    ),
    Source(
        key="lta_annex_a_quota_releases",
        title="LTA quarterly quota press releases, Annex A",
        method="manual",
        url="https://www.lta.gov.sg/",
        needed_for=("4 deregistrations and break table", "10 quota formula"),
        notes=(
            "PDF press releases, no API. Authoritative source for the formula in section 3.1 "
            "and the only published place the deregistration inputs appear as arithmetic. "
            "Stage 4 needs eight to twelve of them straddling the regime changes plus recent "
            "quarters, not one."
        ),
    ),
    # Vehicle population and registrations
    Source(
        key="vehicle_population_annual",
        title="Annual motor vehicle population by type",
        method="datastore",
        dataset_id="d_2873f3b1b2a836103f51f696350b98fa",
        url="https://data.gov.sg/datasets/d_2873f3b1b2a836103f51f696350b98fa/view",
        needed_for=("7 accumulator backtest", "9 congestion calibration"),
        notes="The series the accumulator backtest is scored against under A-04.",
    ),
    Source(
        key="vehicle_population_monthly",
        title="Monthly motor vehicle population by type",
        method="datastore",
        dataset_id="d_2ecb009f1e1ec5a816a454944dec4022",
        url="https://data.gov.sg/datasets/d_2ecb009f1e1ec5a816a454944dec4022/view",
        needed_for=("7 accumulator backtest",),
        notes="Monthly counterpart to the annual series. Finer grain for the same quantity.",
    ),
    Source(
        key="vqs_population_monthly",
        title="Motor vehicle population under the Vehicle Quota System, monthly",
        method="datastore",
        dataset_id="d_ede1a559013d10f234d209ac5e9fd9b4",
        url="https://data.gov.sg/datasets/d_ede1a559013d10f234d209ac5e9fd9b4/view",
        needed_for=("7 accumulator backtest",),
        notes=(
            "Restricted to vehicles under the quota system, so this is the population the "
            "growth allowance actually applies to, not the all-vehicle count."
        ),
    ),
    Source(
        key="vqs_new_registrations_monthly",
        title="New registration of motor vehicles under the VQS, monthly",
        method="datastore",
        dataset_id="d_529752a3d78beb78bd4f38e3be37f1b6",
        url="https://data.gov.sg/datasets/d_529752a3d78beb78bd4f38e3be37f1b6/view",
        needed_for=("7 accumulator backtest",),
        notes=(
            "Registrations are the accumulator's inflow. Pairs with the population series to "
            "let deregistrations be backed out as a residual if stage 4 extraction fails."
        ),
    ),
    Source(
        key="lta_annual_vehicle_statistics",
        title="LTA Annual Vehicle Statistics",
        method="manual",
        url="https://www.lta.gov.sg/",
        needed_for=("4 deregistrations and break table",),
        notes=(
            "Deregistration counts are not published as a standalone series. They appear here "
            "and inside the Annex A arithmetic. PDF and spreadsheet, downloaded by hand."
        ),
    ),
    Source(
        key="lta_datamall_mvp01_mvp02",
        title="LTA DataMall static data, MVP01 and MVP02, including COE revalidation counts",
        method="deferred",
        url="https://datamall.lta.gov.sg/",
        needed_for=("7 accumulator backtest, only if renewals cannot be handled without it",),
        notes=(
            "Deferred. DataMall requires a registered account key and this repo is public and "
            "runs in Claude Code on the web, so there is nowhere to put a key that is both "
            "reachable by the pipeline and not exposed. No key is stored in this repo, in a "
            "`.env` file or in an environment variable, and none should be added. "
            "Every other section 8 source is open. If stage 7 shows the accumulator cannot "
            "reproduce the population series without explicit revalidation counts, the MVP01 "
            "and MVP02 files get downloaded by hand from the link above and committed under "
            "data/raw as data files, with no credential involved."
        ),
    ),
    # Congestion
    Source(
        key="peak_hour_speeds_annual",
        title="Average speed during peak hours, LTA",
        method="datastore",
        dataset_id="d_26f6afadf2f86b2004f9a1e28f5564cc",
        url="https://data.gov.sg/datasets/d_26f6afadf2f86b2004f9a1e28f5564cc/view",
        needed_for=("9 congestion calibration",),
        notes=(
            "Annual from 2004, expressway and arterial split, peak hour 8 to 9am and 6 to 7pm "
            "weekdays. Roughly twenty annual observations. This is the whole evidence base "
            "for O2 and the reason A-09 is expected to end as accepted-as-limitation."
        ),
    ),
    Source(
        key="public_roads_annual",
        title="Public roads, annual, lane-km by road category",
        method="datastore",
        dataset_id="d_f73d13943f7a3cc1aca76b18fea75013",
        url="https://data.gov.sg/datasets/d_f73d13943f7a3cc1aca76b18fea75013/view",
        needed_for=("9 congestion calibration",),
        notes="From 1990. The capacity term in the BPR calibration.",
    ),
    # Revenue
    Source(
        key="singstat_vehicle_quota_premiums",
        title=(
            "Government Operating Revenue, Annual, SingStat table M130571, series 1.2.1 "
            "Vehicle Quota Premiums"
        ),
        method="singstat",
        url="https://tablebuilder.singstat.gov.sg/api/table/tabledata/M130571",
        needed_for=("3 revenue reconciliation",),
        notes=(
            "The stage 3 reconciliation target, pulled by `python -m src.ingest.pull_revenue`. "
            "Sourced to the Accountant-General's Department, annual in millions of dollars "
            "from FY1997. Financial years beginning 1 April, so align periods before "
            "comparing, and the line covers all five categories. The table footnote says "
            "which years are actual figures and which are revised or budgeted estimates; "
            "`src/model/revenue.py` reads it and refuses the estimates. See A-10 and A-17."
        ),
    ),
    Source(
        key="mof_revenue_and_expenditure",
        title="MOF Analysis of Revenue and Expenditure, Vehicle Quota Premiums line",
        method="manual",
        url="https://www.singaporebudget.gov.sg/revenue-and-expenditure/revenue-expenditure-estimates",
        needed_for=("3 revenue reconciliation, as the check on the SingStat target",),
        notes=(
            "Annual budget PDFs, no API. No longer the reconciliation target itself: the same "
            "line is machine-readable from SingStat, above. What this is for is the spot check "
            "A-17 asks for, that the two publications carry the same number. "
            "`data/raw/mof-review-of-fy2025.pdf` is the FY2026 estimates volume's Review of "
            "FY2025, whose Table 2.1 gives Vehicle Quota Premiums actual FY2024 as 6.38 "
            "billion against SingStat's 6379.2 million. Done, for one year."
        ),
    ),
    # Policy context
    Source(
        key="mot_parliamentary_replies",
        title="MOT newsroom Parliamentary replies and ministerial statements",
        method="manual",
        url="https://www.mot.gov.sg/",
        needed_for=("4 break table verification", "17 case study"),
        notes=(
            "Primary source for policy mechanics and for the framing in section 11. Read "
            "before asserting anything about what COE is for."
        ),
    ),
    Source(
        key="nlb_infopedia_select_committee",
        title="NLB Infopedia, 1990 Select Committee history",
        method="manual",
        url="https://www.nlb.gov.sg/",
        needed_for=("17 case study",),
        notes=(
            "Secondary source, used for history and framing only. Nothing from here enters a "
            "regression as a dummy without a primary document behind it, per A-11."
        ),
    ),
)


def by_method(method: str) -> tuple[Source, ...]:
    """Every source obtained the given way."""
    return tuple(s for s in SOURCES if s.method == method)


def by_key(key: str) -> Source:
    for source in SOURCES:
        if source.key == key:
            return source
    raise KeyError(f"no source named {key!r}")


SCRIPTABLE = by_method("datastore")
SINGSTAT = by_method("singstat")
MANUAL = by_method("manual")
DEFERRED = by_method("deferred")

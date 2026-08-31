"""The section 8 source list, in one place.

Every dataset the build needs, with how it is obtained. Three methods:

`datastore`  pulled by `pull_datagov.py` from data.gov.sg, no credential.
`singstat`   pulled by `pull_singstat.py` from SingStat TableBuilder, no credential.
`annexa`     LTA quarterly quota PDFs, pulled by `pull_annexa.py`, no credential.
`manual`     a PDF or a table with no open API. Downloaded by hand and committed.
`deferred`   not obtained, and not needed unless a later stage proves otherwise.

Stage 2 verified every `datastore` id and pulled every scriptable source. The `coverage` field
records what each file turned out to contain, which is not always what section 8 claimed. Rows
A-12 to A-19 of the assumptions register carry the detail.

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

# The portal's own CSV, which is what the pull actually saves. See the decision log entry on
# provenance: bytes matching the published file make ingestion faithfulness answerable.
INITIATE_DOWNLOAD_URL = (
    "https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/initiate-download"
)

# Left pointing at the datastore rather than at api-production.data.gov.sg/v2. That host is
# refused by the egress policy here and was never reached by the session that first wrote this
# constant, so it was never a checked endpoint. datastore_search answers the same question.
DATASET_METADATA_URL = DATASTORE_SEARCH_URL + "?resource_id={dataset_id}&limit=1"


@dataclass(frozen=True)
class Source:
    """One dataset from section 8 of the brief.

    key         short name, also the stem of the file written under data/raw
    title       the dataset as section 8 names it
    method      datastore | singstat | annexa | manual | deferred
    dataset_id  data.gov.sg dataset id, for datastore sources only
    table_id    SingStat TableBuilder id, for singstat sources only
    url         where a human goes to get it, or the API endpoint
    needed_for  the build stages that consume it
    notes       anything a future session would otherwise have to rediscover
    shape       long | wide, for the tabular sources. Wide is the SingStat layout, one
                column per period, and it changes how coverage is read off a file.
    period_field  column holding the period, for long sources only
    claimed_start what section 8 said about coverage before stage 2 checked it. Kept so the
                pull can flag drift rather than leaving it to be noticed by eye.
    coverage    what the pulled file actually contains, filled in from the stage 2 pull
    extension   file extension written under data/raw
    """

    key: str
    title: str
    method: str
    url: str
    needed_for: tuple[str, ...]
    notes: str
    dataset_id: str | None = None
    table_id: str | None = None
    shape: str = ""
    period_field: str = ""
    claimed_start: str = ""
    coverage: str = ""
    extension: str = "csv"

    @property
    def raw_filename(self) -> str:
        return f"{self.key}.{self.extension}"

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
            "One row per category per exercise. Carries bidding period, exercise number, "
            "category, quota, bids received and quota premium. The spine of the premium fit "
            "and of the revenue reconciliation.\n\n"
            "Section 8 recorded this as running from April 2002. It starts at 2010-01. April "
            "2002 is when open bidding fully replaced closed bidding, a regime date rather "
            "than this file's start. For 2002 to 2009 read `quota_and_premium_monthly`.\n\n"
            "Two values are wrong: the 2010-01 bidding 2 Cat D premium and the 2010-02 "
            "bidding 1 Cat B quota, both repeating the row above. Thousands separators appear "
            "in `bids_success` and `bids_received` from 2023-05, and only there. See A-12 and "
            "A-13, and `python -m src.ingest.crosscheck_coe`."
        ),
        shape="long",
        period_field="month",
        claimed_start="2002-04",
        coverage="2010-01 to 2026-08",
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
        shape="wide",
        coverage="2002Feb to 2026Jul",
    ),
    Source(
        key="lta_annex_a_quota_releases",
        title="LTA quarterly quota press releases with Annex A",
        method="annexa",
        url="https://www.lta.gov.sg/content/ltagov/en/newsroom.html",
        needed_for=("4 deregistrations and break table", "10 quota formula"),
        extension="pdf",
        coverage="four quarters straddling Feb 2023, committed under data/raw/annex-a",
        notes=(
            "Scripted at `python -m src.ingest.pull_annexa`. The quarters and the figures read "
            "off them live in `annexa.py`. Release URLs follow no stable naming convention, "
            "running from `certificate-of-entitlement-quota-for-february-2023-to-april-2023` to "
            "`COEs_quota_for_Aug23_to_Oct23`, so the fetcher checks each release page still "
            "links the PDF it expects. Still the only source for the growth allowance, the "
            "named adjustments, and rows B2 and C4 of the cut-and-fill era. A quarter's quota "
            "can be restated by a later annex, so prefer the later comparison row. See A-19."
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
        shape="long",
        period_field="year",
        coverage="2005 to 2024",
    ),
    Source(
        key="vehicle_population_monthly",
        title="Monthly motor vehicle population by type",
        method="datastore",
        dataset_id="d_2ecb009f1e1ec5a816a454944dec4022",
        url="https://data.gov.sg/datasets/d_2ecb009f1e1ec5a816a454944dec4022/view",
        needed_for=("7 accumulator backtest",),
        notes="Monthly counterpart to the annual series. Finer grain for the same quantity.",
        shape="long",
        period_field="month",
        coverage="2012-01 to 2018-02",
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
        shape="wide",
        coverage="1990May to 2026Jun",
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
        shape="wide",
        coverage="1990May to 2026Jan",
    ),
    Source(
        key="lta_annual_vehicle_statistics",
        title="LTA Annual Vehicle Statistics",
        method="deferred",
        url="https://www.lta.gov.sg/content/ltagov/en/who_we_are/statistics_and_publications/statistics.html",
        needed_for=("4 break table, only if a date cannot be sourced elsewhere",),
        notes=(
            "Listed by section 8 as a place deregistration counts could be extracted from. "
            "Superseded: SingStat M650291 publishes the monthly series and it reconciles "
            "exactly against Annex A. Deferred rather than dropped, since it may still settle "
            "a break-table date. See A-16."
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
        key="vqs_deregistrations_monthly",
        title="Motor vehicles de-registered under the Vehicle Quota System, monthly",
        method="singstat",
        table_id="M650291",
        url="https://tablebuilder.singstat.gov.sg/table/TS/M650291",
        needed_for=("4 deregistrations", "10 quota formula", "7 accumulator backtest"),
        extension="json",
        shape="wide",
        coverage="1990 May to 2026 Jul",
        notes=(
            "Primary source for deregistrations, adopted at the stage 2 gate. Section 8 "
            "previously held that no standalone series existed. Twenty comparisons across four "
            "Annex A quarters straddling Feb 2023 reconcile exactly, reproduced by "
            "`python -m src.ingest.crosscheck_deregistrations`.\n\n"
            "Sum the four VQS category lines. The table's own total row also counts taxis and "
            "VQS-exempt vehicles, which Annex A's total excludes, and runs over 5 percent "
            "higher. What this carries is Annex A row B1, gross. It does not carry row B2, the "
            "guaranteed deregistration subset the formula has netted off since Aug 2023, which "
            "is currently negligible and will not stay so. See A-16."
        ),
    ),
    Source(
        key="government_operating_revenue_annual",
        title="Government operating revenue, annual, Vehicle Quota Premiums line",
        method="singstat",
        table_id="M130571",
        url="https://tablebuilder.singstat.gov.sg/table/TS/M130571",
        needed_for=("3 revenue reconciliation",),
        extension="json",
        shape="wide",
        coverage="FY1997 to FY2026, actual only to FY2024",
        notes=(
            "Primary target for the A-10 reconciliation, adopted at the stage 2 gate. Series "
            "1.2.1, millions of dollars, from the Accountant-General's Department.\n\n"
            "Bound the window before running A-10. The table footnote states FY2026 are "
            "budgeted estimates and FY2025 revised, with actuals only to FY2024. Financial "
            "years begin 1 April. The MOF spot check under `mof_revenue_and_expenditure` is "
            "still outstanding. See A-17."
        ),
    ),
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
        shape="long",
        period_field="year",
        claimed_start="2004",
        coverage="2004 to 2025",
    ),
    Source(
        key="public_roads_annual",
        title="Public roads, annual, lane-km by road category",
        method="datastore",
        dataset_id="d_f73d13943f7a3cc1aca76b18fea75013",
        url="https://data.gov.sg/datasets/d_f73d13943f7a3cc1aca76b18fea75013/view",
        needed_for=("9 congestion calibration",),
        notes="From 1990. The capacity term in the BPR calibration.",
        shape="wide",
        claimed_start="1990",
        coverage="1990 to 2025",
    ),
    # Revenue
    Source(
        key="mof_revenue_and_expenditure",
        title="MOF Analysis of Revenue and Expenditure, Vehicle Quota Premiums line",
        method="manual",
        url="https://www.mof.gov.sg/",
        needed_for=("3 revenue reconciliation, as verification not as the target",),
        notes=(
            "No longer the source. SingStat M130571 carries the same line machine-readable "
            "and is adopted as primary, so what remains here is a spot check of one financial "
            "year, because AGD and MOF publishing identical figures is an assumption rather "
            "than something checked. A-10 is not passed until it is done. Blocked for now: "
            "`singaporebudget.gov.sg` is allowlisted but redirects to "
            "`www.singaporebudget.gov.sg`, which is not, so the redirect is refused at "
            "CONNECT. Adding the www host is the whole fix. See A-17."
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


DATASTORE = by_method("datastore")
SINGSTAT = by_method("singstat")
ANNEXA = by_method("annexa")
MANUAL = by_method("manual")
DEFERRED = by_method("deferred")

# Everything a script can fetch without a credential.
SCRIPTABLE = DATASTORE + SINGSTAT + ANNEXA

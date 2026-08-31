"""The Annex A quarters pulled for the A-16 reconciliation, and what was read off them.

Four consecutive quarters straddling February 2023, which is when quota computation moved to
a rolling four-quarter deregistration average. Two quarters under each regime, so the check
covers both.

The `b1` figures below are transcribed by hand from the committed PDFs, which are the primary
source. Every number carries the row label it came from and the window that row states, so any
one of them can be checked against the file in `data/raw/annex-a` without re-deriving anything.
They are reference values for a test, never model inputs.

Two things the four quarters establish about the formula, both of which the brief describes
loosely and the annexes state exactly.

The window and the slice changed together at February 2023. Before, row B1 covered six months
and B2 took 50 percent of it. After, B1 covers twelve months and B2 or B3 takes 25 percent.
Both produce one quarter of the trailing average, which is the arithmetic the working rules say
must not be modelled as a policy rate.

Guaranteed deregistrations became a separate row only from the August 2023 annex, as B2, with
the replacement term then computed on B1 minus B2. Before that there is no netting row at all.
So "deregistrations net of guaranteed deregistrations" is a quantity Annex A constructs, not one
that is published anywhere, and it is not what the monthly series carries. See A-16.
"""

from dataclasses import dataclass, field

PRESS_BASE = "https://www.lta.gov.sg/content/ltagov/en/newsroom"
PDF_BASE = "https://www.lta.gov.sg/content/dam/ltagov/news/press"

CAT_A = "Category A: Cars"
CAT_B = "Category B: Cars"
CAT_C = "Category C: Goods Vehicles & Buses"
CAT_D = "Category D: Motorcycles & Scooters"


@dataclass(frozen=True)
class Quarter:
    slug: str
    quota_period: str
    press_path: str
    pdf_path: str
    filename: str
    # Window that the B1 row itself states, as (year, month, months).
    b1_window: tuple
    b1_window_label: str
    b1_row_label: str
    # B1 by category, transcribed from the PDF.
    b1: dict
    b1_total: int
    regime: str
    # Guaranteed deregistrations row, where the annex has one.
    guaranteed: dict = field(default_factory=dict)
    note: str = ""


QUARTERS = (
    Quarter(
        slug="nov22-jan23",
        quota_period="Nov 2022 to Jan 2023",
        press_path="2022/10/news-releases/COE_quota_for_Nov22_to_Jan23",
        pdf_path="2022/221014_COE_quota_Nov22-Jan23_Annex.pdf",
        filename="2022-10_annex-a_nov22-jan23.pdf",
        b1_window=(2022, 4, 6),
        b1_window_label="Apr 2022 to Sep 2022",
        b1_row_label="B1) Total vehicle de-registrations from Apr 2022 to Sep 2022",
        b1={CAT_A: 6096, CAT_B: 5447, CAT_C: 4441, CAT_D: 5161},
        b1_total=21145,
        regime="pre-Feb-2023: six-month window, B2 takes 50 percent",
        note="No guaranteed deregistration row exists in this annex.",
    ),
    Quarter(
        slug="feb23-apr23",
        quota_period="Feb 2023 to Apr 2023",
        press_path=(
            "2023/1/news-releases/"
            "certificate-of-entitlement-quota-for-february-2023-to-april-2023"
        ),
        pdf_path="2023/230120-1q2023-coe-quota.pdf",
        filename="2023-01_annex-a_feb23-apr23.pdf",
        b1_window=(2022, 1, 12),
        b1_window_label="Jan 2022 to Dec 2022",
        b1_row_label="B1) Total vehicle deregistrations from Jan 2022 to Dec 2022",
        b1={CAT_A: 13471, CAT_B: 11467, CAT_C: 9043, CAT_D: 11145},
        b1_total=45126,
        regime="first quarter on the twelve-month window, B2 takes 25 percent",
        note="Still no guaranteed deregistration row.",
    ),
    Quarter(
        slug="may23-jul23",
        quota_period="May 2023 to Jul 2023",
        press_path="2023/4/news-releases/coe_quota_for_May23-Jul23",
        pdf_path="2023/230421_Monthly_COEquota_May23-Jul23_AnnexA.pdf",
        filename="2023-04_annex-a_may23-jul23.pdf",
        b1_window=(2022, 4, 12),
        b1_window_label="Apr 2022 to Mar 2023",
        b1_row_label="B1) Total vehicle deregistrations from Apr 2022 to Mar 2023",
        b1={CAT_A: 12430, CAT_B: 10488, CAT_C: 9674, CAT_D: 11190},
        b1_total=43782,
        regime="twelve-month window, B2 takes 25 percent",
        note=(
            "Cut-and-fill began during this quarter. The quota this annex publishes was "
            "later restated: see the comparison row in the August 2023 annex."
        ),
    ),
    Quarter(
        slug="aug23-oct23",
        quota_period="Aug 2023 to Oct 2023",
        press_path="2023/7/news-releases/COEs_quota_for_Aug23_to_Oct23",
        pdf_path="2023/230714_COE_quota_Aug_to_Oct23_AnnexA.pdf",
        filename="2023-07_annex-a_aug23-oct23.pdf",
        b1_window=(2022, 7, 12),
        b1_window_label="Jul 2022 to Jun 2023",
        b1_row_label="B1) Total vehicle deregistrations from Jul 2022 to Jun 2023",
        b1={CAT_A: 13707, CAT_B: 11046, CAT_C: 8686, CAT_D: 11173},
        b1_total=44612,
        regime="twelve-month window, B3 takes 25 percent of B1 minus B2",
        guaranteed={CAT_A: 1, CAT_B: 0, CAT_C: 0, CAT_D: 0},
        note=(
            "First annex with a guaranteed deregistration row, B2, and the first with a "
            "C4 redistribution line, at 700 for Cat A and 325 for Cat B."
        ),
    ),
)

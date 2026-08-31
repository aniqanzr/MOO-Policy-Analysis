"""Download the Annex A PDFs for the quarters in src/ingest/annexa.py.

Run it:

    python -m src.ingest.pull_annexa

The PDFs are committed, so this does not need running to reproduce the pipeline. It exists so
the set can be re-fetched and extended, and so the URLs are recorded as code rather than as a
line in a commit message.

The press release page is fetched alongside the PDF and its link is checked against the path
recorded in the registry. LTA does not use a stable naming convention for these releases, the
titles run from `certificate-of-entitlement-quota-for-february-2023-to-april-2023` to
`COEs_quota_for_Aug23_to_Oct23`, so a hardcoded PDF path that silently starts 404ing is a
real possibility. Better to be told the link moved than to skip the quarter.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

import requests

from src.ingest.annexa import PDF_BASE, PRESS_BASE, QUARTERS

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "annex-a"
TIMEOUT = 90

# lta.gov.sg serves the newsroom to a browser agent. So do mof.gov.sg and mot.gov.sg, both of
# which answer 403 to the default python-requests agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    )
}

PDF_LINK = re.compile(r'href="([^"]*\.pdf)"', re.IGNORECASE)


def check_press_page(session, quarter):
    """Confirm the release page still links the PDF path the registry records."""
    url = f"{PRESS_BASE}/{quarter.press_path}.html"
    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"press page unreachable: {exc}"

    links = {match.lower() for match in PDF_LINK.findall(response.text)}
    expected = f"/content/dam/ltagov/news/press/{quarter.pdf_path}".lower()
    if expected not in links:
        return f"press page no longer links {quarter.pdf_path}"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--skip-press-check", action="store_true",
        help="download the PDFs without re-fetching the release pages",
    )
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    failures = []
    with requests.Session() as session:
        for quarter in QUARTERS:
            warning = None
            if not args.skip_press_check:
                warning = check_press_page(session, quarter)

            url = f"{PDF_BASE}/{quarter.pdf_path}"
            try:
                response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
                response.raise_for_status()
            except requests.RequestException as exc:
                failures.append((quarter.slug, str(exc)))
                print(f"  {quarter.slug:<14} FAILED  {exc}")
                continue

            if not response.content.startswith(b"%PDF"):
                failures.append((quarter.slug, "response was not a PDF"))
                print(f"  {quarter.slug:<14} FAILED  not a PDF")
                continue

            (args.out / quarter.filename).write_bytes(response.content)
            digest = hashlib.sha256(response.content).hexdigest()[:16]
            flag = f"  warning: {warning}" if warning else ""
            print(
                f"  {quarter.slug:<14} {len(response.content):>7} bytes  "
                f"{digest}  {quarter.filename}{flag}"
            )

    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

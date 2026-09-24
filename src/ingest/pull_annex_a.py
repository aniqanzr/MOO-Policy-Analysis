"""Pull LTA's quarterly COE quota releases and their Annex A PDFs.

Run it:

    python -m src.ingest.pull_annex_a

Annex A is the only place LTA publishes the quota formula as worked arithmetic: the
deregistrations it counts, the guaranteed deregistrations it nets off, and every named
adjustment. Stage 4 needs it for two things. The deregistration series in M650291 does not
separate guaranteed deregistrations, which the formula removes, so that line has to come from
here. And the release text and Annex A footnotes are primary LTA statements of when each regime
started, which is what the break table is verified against.

The LTA newsroom index lists every quota release from February 2020 onward. This script reads
that index, fetches each release page, saves its text, follows the Annex A link, and saves the
PDF. It writes a manifest with the URL, retrieval time and sha256 of every file, because a
committed PDF with no recorded provenance cannot be re-verified.

Releases before 2020 are not in the index. The regime change that falls before then, May 2017,
is stated in the footnotes of every later Annex A, and that is the primary source used for it.

No credential is used. Every URL here is open.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://www.lta.gov.sg"
INDEX_URL = f"{BASE}/content/ltagov/en/newsroom.html"
TIMEOUT = 60

# www.lta.gov.sg returns 403 to the default python-requests agent. See manual-downloads.md.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MOO-Policy-Analysis/0.1)"}

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "lta-annex-a"
MANIFEST = "manifest.json"

# A quarterly quota release, as opposed to a release that merely mentions COEs. The slugs are
# not consistent across years, so the test is on what the slug names, and the page itself is
# checked for an Annex A link afterwards.
RELEASE = re.compile(
    r"/content/ltagov/en/newsroom/(\d{4})/(\d{1,2})/news-releases/"
    r"[^\"]*(?:quota[-_]for|quota[-_](?:may|aug|nov|feb)|coe[-_]quota|coes[-_]quota|"
    r"certificate[-_]of[-_]entitlement[^\"]*quota)[^\"]*\.html",
    re.IGNORECASE,
)
# A PDF link and its anchor text. Release pages link Annex A twice, once inline and once in the
# attachment list, and some add an Annex B worked example, so links are deduplicated and the
# anchor text is kept to say which is which.
# Releases that are not quarterly quota releases but are the primary source for a break date,
# so they are pulled with the rest. Each carries the reason it is here.
SUPPLEMENTARY = {
    "/content/ltagov/en/newsroom/2020/4/news-releases/"
    "suspension-of-coe-bidding-exercises-in-april-during-elevated-saf.html":
        "start of the April to June 2020 bidding suspension",
    "/content/ltagov/en/newsroom/2020/6/news-releases/"
    "resumption-of-coe-bidding-exercises-from-6-july.html":
        "size and schedule of the quota returned after the 2020 suspension",
    "/content/ltagov/en/newsroom/2023/9/news-releases/"
    "additional-adjustments-to-coe-category-a.html":
        "reallocation adjustments during the 2023 cut-and-fill period",
}

PDF_LINK = re.compile(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', re.IGNORECASE | re.S)


def text_of(html):
    """Page body as plain text. Scripts and styles out, tags out, whitespace collapsed."""
    html = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_paths(session):
    response = session.get(INDEX_URL, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    found = {match.group(0) for match in RELEASE.finditer(response.text)}
    return sorted(found | set(SUPPLEMENTARY))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    entries, failures = [], []
    with requests.Session() as session:
        paths = release_paths(session)
        for path in paths:
            year, month = re.search(r"/newsroom/(\d{4})/(\d{1,2})/", path).groups()
            stem = f"{year}-{int(month):02d}-{path.rsplit('/', 1)[-1][:-5]}"
            url = BASE + path
            try:
                page = session.get(url, headers=HEADERS, timeout=TIMEOUT)
                page.raise_for_status()
            except requests.RequestException as exc:
                failures.append((url, str(exc)))
                continue

            text_path = args.out / f"{stem}.txt"
            text_path.write_text(text_of(page.text) + "\n", encoding="utf-8")
            entry = {
                "release_url": url,
                "why": SUPPLEMENTARY.get(path, "quarterly COE quota release"),
                "release_text": text_path.name,
                "release_sha256": sha256(text_path),
                "retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            # Distinct press PDFs, each with the longest anchor text seen for it.
            links = {}
            for href, anchor in PDF_LINK.findall(page.text):
                if "/news/press/" not in href:
                    continue
                label = re.sub(r"<[^>]+>|&nbsp;|\s+", " ", anchor).strip()
                if len(label) > len(links.get(href, "")):
                    links[href] = label

            entry["attachments"] = []
            for index, (href, label) in enumerate(sorted(links.items())):
                pdf_url = href if href.startswith("http") else BASE + href
                try:
                    pdf = session.get(pdf_url, headers=HEADERS, timeout=TIMEOUT)
                    pdf.raise_for_status()
                except requests.RequestException as exc:
                    failures.append((pdf_url, str(exc)))
                    continue
                if not pdf.content.startswith(b"%PDF"):
                    failures.append((pdf_url, "response is not a PDF"))
                    continue

                is_annex_a = label.lower().startswith("annex a") or re.search(
                    r"annex[-_ ]?a", href, re.IGNORECASE
                ) is not None
                suffix = "annex-a" if is_annex_a else f"attachment-{index + 1}"
                pdf_path = args.out / f"{stem}.{suffix}.pdf"
                pdf_path.write_bytes(pdf.content)
                entry["attachments"].append(
                    {
                        "file": pdf_path.name,
                        "url": pdf_url,
                        "anchor_text": label,
                        "is_annex_a": is_annex_a,
                        "sha256": sha256(pdf_path),
                        "bytes": len(pdf.content),
                    }
                )

            annex = [a for a in entry["attachments"] if a["is_annex_a"]]
            # A supplementary release's Annex A is kept too when it has one. The June 2020
            # release carries the full quota table for July 2020, and the September 2023 one a
            # revised quota. Whether a table has formula lines is the extractor's call.
            entry["annex_a"] = annex[0]["file"] if len(annex) == 1 else None
            if len(annex) != 1:
                entry["note"] = f"{len(annex)} attachments identified as Annex A"
            entries.append(entry)

    manifest = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/ingest/pull_annex_a.py",
        "index": INDEX_URL,
        "note": (
            "LTA quarterly COE quota releases listed in the newsroom index, with the page "
            "text and the Annex A PDF each links to. The index reaches back to February 2020."
        ),
        "releases": entries,
    }
    (args.out / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with_pdf = sum(1 for e in entries if e.get("annex_a"))
    print(f"\n{len(paths)} releases pulled, {len(SUPPLEMENTARY)} of them supplementary, "
          f"{with_pdf} quarterly Annex A tables saved")
    for entry in entries:
        if not entry.get("annex_a"):
            print(f"  no Annex A: {entry['release_url']}  ({entry.get('note')})")
    for url, error in failures:
        print(f"  failed: {url}: {error}", file=sys.stderr)
    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

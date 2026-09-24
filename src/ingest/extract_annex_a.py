"""Extract the quota arithmetic from LTA's Annex A PDFs, and check it.

Run it:

    python -m src.ingest.extract_annex_a

Reads every Annex A under `data/raw/lta-annex-a`, pulls each labelled line of the quota table
into long form, and writes `data/processed/annex-a-quota-arithmetic.csv`. Nothing is typed in by
hand and nothing is guessed. A line whose five category values do not sum to its own published
total is dropped and reported, not repaired by eye.

The PDFs extract to text cleanly but not perfectly. Values arrive with footnote markers between
them, `-` for nothing, and the odd line break inside a number (`1 2,022` for 12,022). Each line
is tokenised a few ways and the reading kept is the one whose category values sum to the
published total. That identity is the check. It is printed, so a line that needed a repair is
visible.

Then three checks against other published data, all printed.

1. The deregistration line, B1, against M650291 over the window B1's own label names. This is
   A-16's first question: is the standalone series the quantity the formula uses.
2. Whether a guaranteed-deregistration line exists, and from when. A-16's second question:
   M650291 has no such split, so if the formula nets one off, it has to come from here.
3. The replacement share the formula applies, 100, 50 or 25 percent, read off the window length.
   This dates the regime changes from the arithmetic itself rather than from the prose.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
ANNEX_DIR = ROOT / "data" / "raw" / "lta-annex-a"
DEREG_FILE = ROOT / "data" / "raw" / "vqs-deregistrations-monthly.csv"
OUT_FILE = ROOT / "data" / "processed" / "annex-a-quota-arithmetic.csv"

CATEGORIES = ("A", "B", "C", "D", "E")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# M650291 rows for the four categories whose deregistrations enter the formula. Category E has
# no vehicles of its own, so it has no deregistrations.
DEREG_ROWS = {
    "A": "Category A: Cars",
    "B": "Category B: Cars",
    "C": "Category C: Goods Vehicles & Buses",
    "D": "Category D: Motorcycles & Scooters",
}

# Where a line of the quota table starts: a code such as `B1)` or `(B)`, or a summary line, at
# the start of a text line. Anchoring to the line start matters, because labels refer to other
# lines by code, as in "(10% of B2)", and splitting there tears a label in half.
LINE_START = re.compile(
    r"(?m)^(?=\s*(?:[ABCD]\d\)|\([ABCD]\)|Total Quota for|Average Monthly Quota for|"
    r"Monthly Quota for|Average\s*$))"
)
# A text line that is only a page number or a "Page 1 of 2" footer.
PAGE_NUMBER = re.compile(r"(?im)^\s*(?:Page\s+)?\d{1,2}(?:\s+of\s+\d{1,2})?\s*$")
NUMBER = re.compile(r"^-?\d{1,3}(?:,\d{3})*$|^-?\d+$")


def pdf_text(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def table_text(text):
    """The quota table only, from the first line code to the footnotes, page numbers removed."""
    # A regular Annex opens with A1). A mid-quarter revision has no formula lines and opens with
    # (A), the quota as first announced.
    starts = [i for i in (text.find("A1)"), text.find("(A)")) if i >= 0]
    start = min(starts) if starts else -1
    end = text.find("Note", start)
    if end < start:
        end = len(text)
    return PAGE_NUMBER.sub("", text[start:end]) if start >= 0 else ""


def split_records(table):
    """Table text split into one record per line of the quota table.

    A split point is a line code at the start of a text line. The exception is a label that
    wraps just after it names another line, "(10% of" then "B1) ...", where the wrapped text
    starts with a code and is not a new line. A record ending in "of" or an open bracket is
    therefore joined to the one after it.
    """
    records = []
    for piece in LINE_START.split(table):
        if not piece.strip():
            continue
        if records and re.search(r"(?:\bof|\()\s*$", records[-1]):
            records[-1] = records[-1].rstrip() + " " + piece.lstrip()
        else:
            records.append(piece)
    return records


def clean(record):
    """Strip footnote markers and superscripts, normalise dashes and spacing."""
    record = re.sub(r"\([a-z]\)|[⁽⁾ᵃ-ᶻ]", " ", record)
    record = record.replace("–", "-").replace("\n", " ")
    return re.sub(r"\s+", " ", record).strip()


def to_int(token):
    return 0 if token == "-" else int(token.replace(",", ""))


def value_tokens(record):
    """Trailing tokens that are numbers or dashes, in order."""
    tokens = record.split(" ")
    tail = []
    for token in reversed(tokens):
        if token == "-" or NUMBER.match(token):
            tail.append(token)
        else:
            break
    return list(reversed(tail)), " ".join(tokens[: len(tokens) - len(tail)])


def readings(tokens, max_merges=2):
    """Every tokenisation reachable by joining up to `max_merges` adjacent token pairs.

    Joins repair numbers the PDF text split across a space, `1 2,022` for 12,022 or `7 1` for
    71. A join is only kept if the result is itself a well-formed number.
    """
    yield tokens
    positions = range(len(tokens) - 1)
    for count in range(1, max_merges + 1):
        for chosen in combinations(positions, count):
            if any(b - a < 2 for a, b in zip(chosen, chosen[1:])):
                continue
            merged, skip, ok = [], set(), True
            for i, token in enumerate(tokens):
                if i in skip:
                    continue
                if i in chosen:
                    joined = token + tokens[i + 1]
                    if token == "-" or not NUMBER.match(joined):
                        ok = False
                        break
                    merged.append(joined)
                    skip.add(i + 1)
                else:
                    merged.append(token)
            if ok:
                yield merged


def satisfying(candidate, width):
    """The candidate read as `width` trailing values, as a dict, if it satisfies the identity.

    Six values are A to E and the total. Five are A to D and the total with the Category E cell
    left blank, which Annex A does on lines where Category E has no vehicles of its own.
    """
    if len(candidate) < width:
        return None
    values = [to_int(t) for t in candidate[-width:]]
    if sum(values[:-1]) != values[-1]:
        return None
    if width == 5:
        values = [*values[:4], 0, values[4]]
    return dict(zip((*CATEGORIES, "Total"), values))


def parse_record(record):
    """Label and values, or the tokens and a reason it could not be read.

    Readings are tried in order of how much repair they need, and the first tier that yields a
    reading wins:

        1. the tokens as extracted, six values
        2. the tokens as extracted, five values with Category E blank
        3. up to two adjacent tokens joined, six values
        4. up to two adjacent tokens joined, five values

    Within a tier, exactly one distinct set of values must satisfy the identity that the
    categories sum to the published total. Two that both satisfy it make the line ambiguous,
    and an ambiguous line is left unread rather than resolved by choosing.
    """
    text = clean(record)
    text = re.sub(r"(\d),\s+(\d{3})\b", r"\1,\2", text)             # `3, 544`
    text = re.sub(r"(\d,\d{1,2})\s+(\d{1,2})\b",
                  lambda m: m.group(1) + m.group(2)
                  if len(m.group(1).split(",")[1] + m.group(2)) == 3 else m.group(0),
                  text)                                                  # `1,4 69`
    tokens, label = value_tokens(text)

    joined = [c for c in readings(tokens) if c is not tokens]
    tiers = (
        ([tokens], 6, False),
        ([tokens], 5, False),
        (joined, 6, True),
        (joined, 5, True),
    )
    for candidates, width, repaired in tiers:
        distinct = {}
        for candidate in candidates:
            values = satisfying(candidate, width)
            if values is not None:
                distinct.setdefault(tuple(values.values()), (values, candidate))
        if len(distinct) == 1:
            values, candidate = next(iter(distinct.values()))
            extra = candidate[: len(candidate) - width]
            return {
                "label": f"{label} {' '.join(extra)}".strip(),
                "values": values,
                "repaired": repaired,
                "e_blank": width == 5,
            }
        if len(distinct) > 1:
            return {"label": label, "values": None, "tokens": tokens,
                    "reason": f"{len(distinct)} readings satisfy the row total"}
    return {"label": label, "values": None, "tokens": tokens,
            "reason": "no reading satisfies the row total"}


def line_code(label):
    match = re.match(r"([ABCD]\d\)|\([ABCD]\))", label)
    if match:
        return match.group(1)
    # Summary lines repeat their prefix for the current and the previous quarter, so the
    # quarter they name is part of the key.
    for prefix in ("Total Quota for", "Average Monthly Quota for", "Monthly Quota for"):
        if label.startswith(prefix):
            named = re.match(
                rf"{prefix}\s+(.+?)\s+Bidding", label
            )
            return f"{prefix} {named.group(1)}" if named else prefix
    return label[:20]


def quota_period(text):
    """The bidding quarter the Annex is for, e.g. `Feb 2023 to Apr 2023`."""
    match = re.search(
        r"COE QUOTA (?:FOR|FROM)\s+([A-Z]+)\s*(\d{4})?\s*TO\s+([A-Z]+)\s*(\d{4})", text.upper()
    )
    if not match:
        # A single-month table, as in July 2020 after the suspension.
        single = re.search(r"COE QUOTA FOR\s+([A-Z]+)\s*(\d{4})", text.upper())
        if single:
            month, year = single.groups()
            return f"{month[:3].title()} {year} to {month[:3].title()} {year}"
        return None
    m0, y0, m1, y1 = match.groups()
    y0 = y0 or y1
    return f"{m0[:3].title()} {y0} to {m1[:3].title()} {y1}"


def window_of(label):
    """The deregistration window a B1 label names, as ((year, month), (year, month))."""
    match = re.search(
        r"(?:from\s+)?([A-Z][a-z]{2})[a-z]*\s*(\d{4})?\s+to\s+([A-Z][a-z]{2})[a-z]*\s*(\d{4})",
        label,
    )
    if not match:
        return None
    m0, y0, m1, y1 = match.groups()
    y0 = int(y0 or y1)
    y1 = int(y1)
    return (y0, MONTHS.index(m0) + 1), (y1, MONTHS.index(m1) + 1)


def months_between(window):
    (y0, m0), (y1, m1) = window
    return (y1 - y0) * 12 + (m1 - m0) + 1


def load_deregistrations():
    rows = list(csv.reader(DEREG_FILE.open(newline="", encoding="utf-8")))
    header, series = rows[0], {row[0]: row for row in rows[1:]}
    values = defaultdict(dict)
    for index, column in enumerate(header[1:], start=1):
        key = (int(column[:4]), MONTHS.index(column[4:]) + 1)
        for category, name in DEREG_ROWS.items():
            raw = series[name][index].strip().replace(",", "")
            if raw and raw.lower() not in {"-", "na"}:
                values[category][key] = int(float(raw))
    return values


def extract(annex_dir=ANNEX_DIR):
    manifest = json.loads((annex_dir / "manifest.json").read_text(encoding="utf-8"))
    releases, rows, unread = [], [], []

    for entry in manifest["releases"]:
        if not entry.get("annex_a"):
            continue
        text = pdf_text(annex_dir / entry["annex_a"])
        period = quota_period(text)
        records = split_records(table_text(text))

        release = {
            "file": entry["annex_a"],
            "period": period,
            "revision": "REVISED MONTHLY COE QUOTA" in text.upper(),
            "lines": {},
        }
        for record in records:
            parsed = parse_record(record)
            code = line_code(parsed["label"])
            if parsed["values"] is None:
                if parsed.get("tokens"):
                    unread.append((entry["annex_a"], code, " ".join(parsed["tokens"]),
                                   parsed["reason"]))
                continue
            if code in release["lines"]:
                raise RuntimeError(
                    f"{entry['annex_a']}: line {code} appears twice. A record was split or "
                    "joined wrongly, and keeping either copy would be a guess."
                )
            release["lines"][code] = parsed
            for category, value in parsed["values"].items():
                rows.append(
                    {
                        "annex_a": entry["annex_a"],
                        "quota_period": period,
                        "line": code,
                        "label": parsed["label"],
                        "category": category,
                        "value": value,
                        "repaired": parsed["repaired"],
                    }
                )
        releases.append(release)

    def start_of(release):
        if not release["period"]:
            return (9999, 99, release["file"])
        month, year = release["period"].split(" to ")[0].split()
        return (int(year), MONTHS.index(month) + 1, release["revision"])

    releases.sort(key=start_of)
    return releases, rows, unread


def deregistration_line(release):
    """The line carrying total deregistrations over the window, and the window it names."""
    for code, parsed in release["lines"].items():
        label = parsed["label"].lower()
        if code == "B1)" and "deregistration" in label.replace("-", ""):
            window = window_of(parsed["label"])
            if window:
                return parsed, window
    return None, None


def guaranteed_line(release):
    for code, parsed in release["lines"].items():
        if "guaranteed" in parsed["label"].lower() and code.startswith("B"):
            return code, parsed
    return None, None


def write(rows, path=OUT_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["annex_a", "quota_period", "line", "label", "category", "value", "repaired"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)

    releases, rows, unread = extract()
    write(rows)
    deregs = load_deregistrations()

    repaired = sum(1 for r in rows if r["repaired"] and r["category"] == "Total")
    print(f"\n{len(releases)} Annex A tables read, {len(rows) // 6} lines kept, "
          f"{repaired} needing a tokenisation repair, {len(unread)} unread")
    for file, code, tokens, reason in unread:
        print(f"   unread: {file[:40]} {code}: {tokens}  ({reason})")

    print("\n1. B1 deregistrations against M650291 over the window B1 names")
    print(f"   {'quota period':<24}{'window':<22}{'months':>7}{'share':>7}"
          f"{'A':>8}{'B':>8}{'C':>8}{'D':>8}   match")
    matched = total = 0
    for release in releases:
        parsed, window = deregistration_line(release)
        if parsed is None:
            note = ("revision of an announced quota, no formula lines"
                    if release["revision"] else "NO B1 LINE READ")
            print(f"   {release['period'] or release['file'][:24]:<24}{note}")
            if not release["revision"]:
                total += 1
            continue
        span = months_between(window)
        months = set()
        (y, m), end = window
        while (y, m) <= end:
            months.add((y, m))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

        cells, ok = [], True
        for category in DEREG_ROWS:
            published = sum(deregs[category].get(month, 0) for month in months)
            annex = parsed["values"][category]
            ok &= published == annex
            cells.append(f"{annex - published:>+8,}")
        total += 1
        matched += ok

        # The share of the window's deregistrations that becomes quota: 100, 50 or 25 percent,
        # which is one quarter's worth of a one-, two- or four-quarter window.
        share = f"{round(300 / span)}%"
        label = f"{window[0][0]}-{window[0][1]:02d} to {window[1][0]}-{window[1][1]:02d}"
        print(f"   {release['period']:<24}{label:<22}{span:>7}{share:>7}"
              f"{''.join(cells)}   {'yes' if ok else 'NO'}")
    print(f"   exact match in all four categories: {matched} of {total}")

    print("\n2. Guaranteed deregistrations as a separate line")
    for release in releases:
        code, parsed = guaranteed_line(release)
        if parsed:
            v = parsed["values"]
            print(f"   {release['period']:<24}{code:<5}A {v['A']:>6,}  B {v['B']:>6,}  "
                  f"C {v['C']:>6,}  D {v['D']:>6,}  total {v['Total']:>6,}")
    first = next((r["period"] for r in releases if guaranteed_line(r)[1]), None)
    print(f"   first quarter with the line: {first}")
    print("   Aug and Nov 2023 print it positive with B3 = 25% of (B1 - B2). From Feb 2024 it is")
    print("   printed negative with B3 = 25% of (B1 + B2). Same quantity, presentation changed.")

    replacement_n, deviations = check_replacement_share(releases)
    print("\n3. The replacement line against share x (B1 net of guaranteed deregistrations)")
    print(f"   {replacement_n} quarters checked, {len(deviations)} published values that no "
          "rounding of the product gives")
    for period, category, expected, got in deviations:
        name = "row total " if category == "Total" else f"Category {category}"
        print(f"   {period:<24}{name:<12} published {got:>7,}  arithmetic {expected:>10,.2f}"
              f"  off by {got - expected:+.2f}")
    if deviations:
        worst = max(abs(got - expected) for _, _, expected, got in deviations)
        print(f"   largest gap: {worst:.2f} COEs. Each category is otherwise a rounding of its own")
        print("   product, in no fixed direction. These cells are not, and the table does not say")
        print("   why. Rounding the row total and apportioning it was tested and does not fit.")

    totals_ok, totals_n = check_table_totals(releases)
    print(f"\n4. Each table's total quota against the sum of its own (A), (B), (C) and (D) lines")
    print(f"   agrees exactly in {totals_ok} of {totals_n} quarters")

    returned = suspension_returns(releases)
    print("\n5. Quota returned from the suspended April to June 2020 exercises")
    for period, code, value in returned:
        print(f"   {period:<24}{code:<5}{value:>7,}")
    print(f"   total returned across these Annexes: {sum(v for _, _, v in returned):,}")
    print()
    # Exit status reflects extraction, not LTA's arithmetic. A deviation in check 3 is a finding
    # about the published table and is pinned by the tests instead.
    ok = not unread and matched == total and totals_ok == totals_n
    return 0 if ok else 1


def check_replacement_share(releases):
    """Replacement quota against share times effective deregistrations, per category.

    Share is one quarter of the window: 100 percent of a three-month window, 50 percent of six,
    25 percent of twelve. Effective deregistrations are B1 less guaranteed deregistrations,
    whichever sign the Annex prints them with. A published value agrees if it is the floor or
    the ceiling of the product, which covers any rounding rule. Anything else is returned as a
    deviation with its numbers, because it is a fact about the published arithmetic and not
    something to absorb into a tolerance.

    Before August 2022 the share is 100 percent and there is no separate replacement line, so
    the (B) subtotal's total is compared with B1's total instead.
    """
    checked, deviations = 0, []
    for release in releases:
        parsed, window = deregistration_line(release)
        if parsed is None:
            continue
        share = 3 / months_between(window)
        code, guaranteed = guaranteed_line(release)

        replacement = None
        for key, line in release["lines"].items():
            label = line["label"].lower()
            if key.startswith("B") and key not in ("B1)", code) and "% of" in label \
                    and "deregistration" in label.replace("-", "") and "contribution" not in label:
                replacement = line
        checked += 1

        if replacement is None:
            subtotal = release["lines"]["(B)"]["values"]["Total"]
            if subtotal != parsed["values"]["Total"]:
                deviations.append((release["period"], "Total", parsed["values"]["Total"],
                                   subtotal))
            continue

        nets = {}
        for category in DEREG_ROWS:
            nets[category] = parsed["values"][category] - abs(
                guaranteed["values"][category] if guaranteed else 0
            )
            expected = share * nets[category]
            got = replacement["values"][category]
            if got not in (int(expected // 1), int(-(-expected // 1))):
                deviations.append((release["period"], category, expected, got))
        # The row total is not checked against share x total. LTA rounds each category on its
        # own, in no fixed direction, and the total is the sum of the rounded categories, which
        # the row identity already enforces. A total can therefore sit up to two COEs from the
        # rounded product without anything being wrong.
    return checked, deviations


def check_table_totals(releases):
    """The published total quota against the sum of the table's own subtotal lines."""
    ok = n = 0
    for release in releases:
        if release["revision"] or not release["period"]:
            continue
        lines = release["lines"]
        parts = [lines[c] for c in ("(A)", "(B)", "(C)") if c in lines]
        if len(parts) != 3:
            continue
        final_code = "(D)" if "(D)" in lines else next(
            (c for c in lines if c.startswith("Total Quota for " + release["period"].split(" to ")[0])
             or c == f"Total Quota for {release['period']}"),
            None,
        )
        if final_code is None:
            continue
        final = lines[final_code]["values"]
        extra = [lines[c] for c in lines if c.startswith("D") and c != "D1)"] if "(D)" in lines else []
        n += 1
        good = True
        for category in (*CATEGORIES, "Total"):
            summed = sum(p["values"][category] for p in parts)
            summed += sum(p["values"][category] for p in extra if p["values"])
            if "(D)" in lines:
                # (D) = D1 + returned quota, and D1 = (A) + (B) + (C).
                summed = lines["D1)"]["values"][category] + sum(
                    p["values"][category] for p in extra
                )
            good &= summed == final[category]
        ok += good
    return ok, n


def suspension_returns(releases):
    """Lines returning quota from the April to June 2020 suspension, with their totals."""
    found = []
    for release in releases:
        for code, line in release["lines"].items():
            label = line["label"].lower()
            if "suspended" in label and ("return" in label or "redistribution" in label):
                found.append((release["period"], code, line["values"]["Total"]))
    return found


if __name__ == "__main__":
    sys.exit(main())

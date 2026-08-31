"""Reading the period range off a raw file.

Coverage is checked against what section 8 claims, so the period labels have to be ordered
rather than taken in file order. Source ordering happens to be chronological in every file
pulled so far, but that is not something the API promises and it is cheap not to rely on.

Four label shapes appear across the section 8 sources: `2010-01`, `2026Jul`, `2005` and
`2024-Q3`. Anything else returns None, and the caller falls back to file order and says so.
"""

import re

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_ISO_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_NAMED_MONTH = re.compile(r"^(\d{4})[- ]?([A-Za-z]{3})[a-z]*$")
_QUARTER = re.compile(r"^(\d{4})[- ]?Q([1-4])$", re.IGNORECASE)
_YEAR = re.compile(r"^(\d{4})$")


def period_key(label):
    """Sort key for a period label, or None if the shape is not recognised.

    The key is (year, month) with month 0 for a bare year, so a year sorts before any month
    inside it. Quarters map to their first month.
    """
    label = str(label).strip()

    match = _ISO_MONTH.match(label)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        return (year, month) if 1 <= month <= 12 else None

    match = _NAMED_MONTH.match(label)
    if match:
        month = _MONTHS.get(match.group(2).lower())
        return (int(match.group(1)), month) if month else None

    match = _QUARTER.match(label)
    if match:
        return (int(match.group(1)), (int(match.group(2)) - 1) * 3 + 1)

    match = _YEAR.match(label)
    if match:
        return (int(match.group(1)), 0)

    return None


def span(labels):
    """First and last period across `labels`, plus how the ordering was arrived at.

    Returns (first, last, ordering). `ordering` is "parsed" when every label was understood
    and "file" when at least one was not, in which case the bounds are simply the first and
    last label as they appear. The distinction is recorded in the manifest so a coverage
    figure that rests on file order is not mistaken for one that rests on parsed dates.
    """
    labels = [str(label) for label in labels]
    if not labels:
        return None, None, "empty"

    keys = [period_key(label) for label in labels]
    if any(key is None for key in keys):
        return labels[0], labels[-1], "file"

    ordered = [label for _, label in sorted(zip(keys, labels))]
    return ordered[0], ordered[-1], "parsed"


def covers(first, claimed_start):
    """Whether coverage starting at `first` satisfies a section 8 claim of `claimed_start`.

    True when the file starts at or before the claimed start. False when it starts later,
    which means section 8 overstates the coverage. None when either label is unrecognised,
    because that is not the same as a mismatch and should not be reported as one.
    """
    a, b = period_key(first), period_key(claimed_start)
    if a is None or b is None:
        return None
    return a <= b

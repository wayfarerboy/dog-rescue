"""Shared filters for dog results — age, gender, breed, distance.

Usage:
    from filters import filter_dogs_by_age, filter_dogs_by_gender

    dogs = filter_dogs_by_age(dogs, max_months=12)
    dogs = filter_dogs_by_gender(dogs, keep="Female")
"""

from __future__ import annotations

import re

from sites.base import Dog

# ---------------------------------------------------------------------------
# age parsing
# ---------------------------------------------------------------------------

# Mapping of Unicode bold/mathematical characters to plain ASCII
_UNICODE_BOLD_MAP: dict[int, str] = {}
for _i in range(26):
    _UNICODE_BOLD_MAP[0x1D5D4 + _i] = chr(ord("A") + _i)  # bold caps
    _UNICODE_BOLD_MAP[0x1D5EE + _i] = chr(ord("a") + _i)  # bold small

# Weeks in an average month (365.25 / 12 / 7)
_WEEKS_PER_MONTH = 4.345


def _unbold(text: str) -> str:
    """Normalize Unicode bold characters to plain ASCII."""
    return "".join(_UNICODE_BOLD_MAP.get(ord(ch), ch) for ch in text)


def parse_age_months(age_str: str) -> int | None:
    """Parse an age string into total months.

    Returns None if unparseable (so callers can decide: keep or skip).

    Handles:
      "6 months", "6 Months", "11 Months Old", "18 Month Old"
      "1 year", "1 Year old", "2.5 Year Old", "0 years 9 months"
      "11 weeks", "12 Week Old"
      "1-2 years"          → lower bound
      "6 & 10 Year Old"    → lower bound
      "approx. 7 Months old", Unicode bold prefixes
      "1 year approx.", "1 year old approx"
    """
    if not age_str:
        return None

    text = _unbold(age_str).lower().strip()
    # Collapse whitespace and non-breaking spaces
    text = re.sub(r"\s+", " ", text)

    # Strip leading "approx." / "approx" noise
    text = re.sub(r"^approx\.?\s*", "", text)

    months = 0
    matched = False

    # Pattern for range/pair: take lower bound.
    # "6 & 10 Year Old" → first number, unit from full text
    # "1-2 years" → first number, unit from full text
    parts = re.split(r"\s*(?:&|–|—|-|to)\s*", text)
    lower_text = parts[0].strip()

    # Try to find number in lower part
    num_match = re.search(r"(\d+(?:\.\d+)?)", lower_text)
    if not num_match:
        return None
    count = float(num_match.group(1))

    # Unit: check lower part first, then full text (for ranges like
    # "6 & 10 Year Old" where unit only appears after the separator)
    if re.search(r"years?\b", lower_text):
        months = int(count * 12)
        matched = True
    elif re.search(r"months?\b", lower_text):
        months = int(count)
        matched = True
    elif re.search(r"weeks?\b", lower_text):
        months = round(count / _WEEKS_PER_MONTH)
        matched = True
    elif re.search(r"years?\b", text):
        months = int(count * 12)
        matched = True
    elif re.search(r"months?\b", text):
        months = int(count)
        matched = True
    elif re.search(r"weeks?\b", text):
        months = round(count / _WEEKS_PER_MONTH)
        matched = True

    return months if matched else None


# ---------------------------------------------------------------------------
# filters
# ---------------------------------------------------------------------------

def filter_dogs_by_age(
    dogs: list[Dog],
    max_months: int,
) -> list[Dog]:
    """Keep only dogs whose age parses to ≤ max_months.

    Dogs with unparseable ages are kept (conservative — don't hide a dog
    just because we can't parse its age).
    """
    result: list[Dog] = []
    for dog in dogs:
        age_months = parse_age_months(dog.age)
        if age_months is None or age_months <= max_months:
            result.append(dog)
    return result


def filter_dogs_by_gender(
    dogs: list[Dog],
    keep: str = "Female",
) -> list[Dog]:
    """Keep only dogs whose gender matches (case-insensitive).

    Dogs with empty gender are kept (conservative).
    """
    keep_lower = keep.lower()
    result: list[Dog] = []
    for dog in dogs:
        if not dog.gender or dog.gender.lower() == keep_lower:
            result.append(dog)
    return result

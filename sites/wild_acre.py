"""Wild Acre Rescue site checker.

Single-page Elementor-built WordPress site. Each dog is an
`elementor-widget-image-box` widget. Breed, DOB, and gender are
parsed from the free-text description inside each card.
"""

from __future__ import annotations

import calendar
import datetime
import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LISTING_URL = "https://wildacrerescue.co.uk/dogs-for-adoption/"
LOCATION = "West Midlands"

# Gender patterns (same logic as East Midlands: count gendered words)
_FEMALE_WORDS = re.compile(
    r"\b(girl|she|her|hers|lady|ladies|lass|female)\b", re.IGNORECASE
)
_MALE_WORDS = re.compile(
    r"\b(boy|he|him|his|lad|gent|male)\b", re.IGNORECASE
)

# Breed extraction: "X is a Y", "X we believe is a Y", "probably a Y", etc.
_BREED_RE = re.compile(
    r"(?:is\s+an?\s+|we\s+believe\s+(?:is|may\s+be)\s+an?\s+|"
    r"appears\s+to\s+be\s+an?\s+|probably\s+an?\s+|"
    r"may\s+be\s+an?\s+)"
    r"([\w\s\-/×x]+?)(?:\.|\s*$|\s+(?:and|who|which|with|that|if|but|he|she|it))",
    re.IGNORECASE,
)

# DOB pattern: "DOB July 2022", "DOB Jul 2022", "DOB 15 July 2022"
_DOB_RE = re.compile(
    r"DOB\s+"
    r"(?:approx\.?\s*)?"
    r"(?:(?P<day>\d{1,2})\s+)?"
    r"(?P<month>"
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    r")"
    r"\s+"
    r"(?P<year>(?:20)?\d{2})",
    re.IGNORECASE,
)

_MONTH_ABBREV = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
# For "2022" or "22"
_YEAR_RE = re.compile(r"(\d{2,4})$")


class WildAcreChecker(SiteChecker):
    site_name = "Wild Acre Rescue"
    data_file = "wild-acre.txt"

    def fetch(self) -> str:
        resp = requests.get(LISTING_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse the single listing page into Dog objects."""
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for widget in soup.select(".elementor-widget-image-box"):
            # Name from title
            title_el = widget.select_one(".elementor-image-box-title")
            name = title_el.get_text(strip=True) if title_el else ""
            if not name:
                continue

            # Description
            desc_el = widget.select_one(".elementor-image-box-description")
            desc = desc_el.get_text(" ", strip=True) if desc_el else ""

            # Photo from image
            photo_url = ""
            img_el = widget.select_one(".elementor-image-box-img img")
            if img_el:
                photo_url = img_el.get("src", "") or img_el.get("data-src", "") or ""

            # No separate detail pages; use the listing URL as the profile URL
            # since all info is inline
            dog_url = LISTING_URL

            dogs.append(
                Dog(
                    name=name,
                    age=_parse_age(desc),
                    gender=_infer_gender(desc, name),
                    breed=_parse_breed(desc),
                    url=dog_url,
                    status="Available",
                    location=LOCATION,
                    photo_url=photo_url,
                )
            )

        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, filter, and return new dogs.

        Post-parse filtering: female only, age <= 12 months.
        """
        raw = self.fetch()
        all_dogs = self.parse(raw)

        # Post-parse filtering
        filtered = [
            d for d in all_dogs
            if d.gender == "Female" and _age_months(d.age) <= 12
        ]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new


# ── helpers ──────────────────────────────────────────────────────────


def _parse_breed(desc: str) -> str:
    """Extract breed from description text.

    "Zak we believe is a patterdale x chihuahua x French bulldog."
    → "Patterdale x Chihuahua x French Bulldog"
    """
    m = _BREED_RE.search(desc)
    if not m:
        return ""
    breed = m.group(1).strip()
    # Remove trailing punctuation/sentence fragments
    breed = re.sub(r"[\s,;]+$", "", breed)
    # Title-case for display consistency
    return _titlecase_breed(breed)


def _titlecase_breed(breed: str) -> str:
    """Title-case a breed string, preserving mixed-breed separators."""
    # Split on cross/mix markers but keep them
    parts = re.split(r"(\s*x\s*|\s+/\s+|\s*×\s*)", breed, flags=re.IGNORECASE)
    result: list[str] = []
    for part in parts:
        # If it's a separator (x, /, ×), normalise to " X "
        if re.match(r"^\s*[x/×]\s*$", part, re.IGNORECASE):
            result.append(" X ")
        else:
            # Title-case each word
            words = part.strip().split()
            result.append(" ".join(w.capitalize() for w in words))
    return "".join(result).strip()


def _parse_age(desc: str) -> str:
    """Parse age from description, either from DOB or explicit age mention.

    "DOB July 2022" → calculate months from DOB.
    "1 year old", "6 months", etc. → return as-is.
    """
    # Try DOB first
    m = _DOB_RE.search(desc)
    if m:
        month_name = m.group("month")[:3].lower()
        month = _MONTH_ABBREV.get(month_name, 1)
        day = int(m.group("day")) if m.group("day") else 1
        year_str = m.group("year")
        # "22" → 2022, "2022" → 2022
        year = int(year_str)
        if year < 100:
            year += 2000
        dob = datetime.date(year, month, day)
        age_months = _months_since(dob)
        return _format_age(age_months)

    # Fallback: "6 months old", "2 years old", etc.
    month_match = re.search(
        r"(\d+)\s*(?:month[s]?|mth)[\s-]*(?:old)?", desc, re.IGNORECASE
    )
    if month_match:
        n = int(month_match.group(1))
        return f"{n} {'month' if n == 1 else 'months'}"

    year_match = re.search(
        r"(\d+)\s*(?:year[s]?|yr)[\s-]*(?:old)?", desc, re.IGNORECASE
    )
    if year_match:
        n = int(year_match.group(1))
        return f"{n} {'year' if n == 1 else 'years'}"

    return ""


def _months_since(d: datetime.date) -> int:
    """Calculate months elapsed between date d and today."""
    today = datetime.date.today()
    return (today.year - d.year) * 12 + (today.month - d.month)


def _format_age(months: int) -> str:
    """Format months as a human-readable age string."""
    if months < 1:
        return ""
    if months < 12:
        return f"{months} {'month' if months == 1 else 'months'}"
    years = months // 12
    remaining = months % 12
    if remaining == 0:
        return f"{years} {'year' if years == 1 else 'years'}"
    return (
        f"{years} {'year' if years == 1 else 'years'} "
        f"{remaining} {'month' if remaining == 1 else 'months'}"
    )


def _infer_gender(text: str, name: str) -> str:
    """Infer gender from description text and name.

    Counts weighted female vs male word hits. Ties break female.
    """
    combined = f"{name} {text}"
    female_count = len(_FEMALE_WORDS.findall(combined))
    male_count = len(_MALE_WORDS.findall(combined))

    if female_count == 0 and male_count == 0:
        return ""

    if female_count >= male_count:
        return "Female"
    return "Male"


def _age_months(age_str: str) -> int:
    """Parse an age string into total months. Returns 999 if unparseable."""
    age_str = age_str.lower().strip()
    if not age_str:
        return 999
    # "Less than 1 month" from empty/negative DOB calculation → treat as 0
    if "less than" in age_str:
        return 0
    year_match = re.search(r"(\d+)\s*years?\b", age_str)
    month_match = re.search(r"(\d+)\s*months?\b", age_str)
    if not year_match and not month_match:
        return 999
    years = int(year_match.group(1)) if year_match else 0
    months = int(month_match.group(1)) if month_match else 0
    return years * 12 + months

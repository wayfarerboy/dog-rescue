"""Cheltenham Animal Shelter (GAWA) site checker.

Fetches the filtered dog listing page, visits each dog's detail page
for full data.  Computes approximate age from date-of-birth.
"""

from __future__ import annotations

import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LOCATION = "Gardner's Ln, Cheltenham GL51 9JW"
LISTING_URL = (
    "https://gawa.org.uk/adopt-a-pet/"
    "?filter=true&adopt_tag=available&adopt_category=dogs"
)


class CheltenhamChecker(SiteChecker):
    site_name = "Cheltenham Animal Shelter"
    data_file = "cheltenham.txt"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
    }

    def fetch(self) -> str:
        resp = requests.get(LISTING_URL, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing page, visit detail pages, build Dog objects."""
        soup = BeautifulSoup(raw, "html.parser")
        dog_urls = self._parse_dog_urls(soup)
        if not dog_urls:
            return []

        dogs: list[Dog] = []
        for name, url in dog_urls:
            detail_html = self._fetch_detail(url)
            detail = self._parse_detail(detail_html, name)

            # Skip non-available dogs
            if detail["status"] != "Available":
                continue

            dogs.append(
                Dog(
                    name=detail["name"],
                    age=detail["age"],
                    gender=detail["gender"],
                    breed=detail["breed"],
                    url=url,
                    status=detail["status"],
                    location=LOCATION,
                    photo_url=detail["photo_url"],
                )
            )

        return dogs

    # ── listing page helpers ───────────────────────────────────────

    @staticmethod
    def _parse_dog_urls(soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Extract unique (name, url) pairs from the listing page.

        Name is derived from the URL slug since the listing cards only
        have "FULL DETAILS" as link text.
        """
        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for a in soup.select("a[href]"):
            href = a.get("href", "")
            # Match /adopt/{name}/  — must be a dog detail page (not parent)
            m = re.match(r"https://gawa\.org\.uk/adopt/([^/]+)/?$", href)
            if not m:
                continue
            if href in seen:
                continue
            seen.add(href)

            slug = m.group(1)
            # Derive display name from slug
            name = slug.replace("-", " ").title()
            results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, fallback_name: str) -> dict:
        """Extract all fields from a detail page.

        Returns dict with name, age, gender, breed, status, photo_url.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove noisy elements before text extraction
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe"]):
            tag.decompose()

        body_text = soup.get_text(separator="\n")
        lines = body_text.splitlines()

        result = {
            "name": fallback_name,
            "age": "",
            "gender": "",
            "breed": "",
            "status": "Available",
            "photo_url": "",
        }

        # Try to get a better name from h1 or page title
        title_el = soup.select_one("h1") or soup.select_one("title")
        if title_el:
            title = title_el.get_text(strip=True)
            if "|" in title:
                result["name"] = title.split("|")[0].strip()
            elif "Cheltenham" not in title:
                result["name"] = title.strip()

        # Extract fields from text. Labels and values may be separated
        # by blank lines.  Look ahead past blank lines for the value.
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.lower() in ("breed", "breed:"):
                result["breed"] = _next_nonblank(lines, i + 1)
            elif stripped.lower() in ("gender", "gender:"):
                result["gender"] = _next_nonblank(lines, i + 1)
            elif stripped.lower() == "date of birth":
                # Label stands alone — value is on next non-blank line
                result["age"] = _dob_to_age(_next_nonblank(lines, i + 1))
            elif stripped.lower().startswith("date of birth:"):
                # "Date of Birth: 10/12/2021" — value on same line
                result["age"] = _dob_to_age(stripped[14:].strip())

        # Status: check for non-available markers near top
        first_chunk = "\n".join(lines[:50]).lower()
        if "reserved" in first_chunk and "available" not in first_chunk:
            result["status"] = "Reserved"
        elif "foster" in first_chunk and "available" not in first_chunk:
            result["status"] = "Foster"

        # Photo: first wp-content image that isn't a logo or social icon
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "wp-content/uploads" in src:
                low = src.lower()
                if "logo" not in low and "facebook" not in low and "icon" not in low:
                    result["photo_url"] = src
                    break

        return result


def _next_nonblank(lines: list[str], start: int) -> str:
    """Return the next non-blank line starting at index `start`, or ''."""
    while start < len(lines):
        val = lines[start].strip()
        if val:
            return val
        start += 1
    return ""


def _dob_to_age(dob_str: str) -> str:
    """Convert a DD/MM/YYYY date-of-birth string to an age string like '3 years'."""
    if not dob_str:
        return ""
    try:
        dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
    except ValueError:
        return dob_str  # return as-is if we can't parse

    today = date.today()
    years = today.year - dob.year
    months = today.month - dob.month

    if months < 0:
        years -= 1
        months += 12

    # Adjust for day-of-month
    if today.day < dob.day:
        months -= 1
        if months < 0:
            years -= 1
            months += 12

    if years < 1:
        return f"{months} months"
    if years == 1:
        if months == 0:
            return "1 year"
        return f"1 year {months} months"
    if months == 0:
        return f"{years} years"
    return f"{years} years {months} months"

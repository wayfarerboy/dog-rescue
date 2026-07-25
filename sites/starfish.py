"""Starfish Dog Rescue site checker.

Fetches the /dogs-looking-for-a-home/ listing page, extracts available
dog cards (Container 0 only — reserved / not-ready are separate
containers), visits each detail page for age and photo.
"""

from __future__ import annotations

import re
from typing import cast

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LOCATION = "Gloucestershire"
LISTING_URL = "https://starfishdogrescue.co.uk/dogs-looking-for-a-home/"

# Parse title like "Bella - French Bulldog - (F)" or "Sebastian - Poodle - (M)"
# (site uses en-dashes which are matched by the character class)
_TITLE_RE = re.compile(r"^(.+?)\s*[–-]\s*(.+?)\s*[–-]\s*\(([MF])\)$")  # noqa: RUF001


def _parse_title(title: str) -> tuple[str, str, str]:
    """Parse a card title into (name, breed, gender).

    Returns ("", "", "") on parse failure.
    """
    m = _TITLE_RE.match(title.strip())
    if not m:
        return title.strip(), "", ""
    return m.group(1).strip(), m.group(2).strip(), "Male" if m.group(3) == "M" else "Female"


# Age regex patterns for detail page text
_AGE_PATTERNS = [
    # "19-month-old", "9 month old", "3-year-old"
    (re.compile(r"(\d+)\s*-\s*month\s*-\s*old", re.IGNORECASE), "months"),
    (re.compile(r"(\d+)\s*-\s*year\s*-\s*old", re.IGNORECASE), "years"),
    (re.compile(r"(\d+)\s+month[s]?\s+old", re.IGNORECASE), "months"),
    (re.compile(r"(\d+)\s+year[s]?\s+old", re.IGNORECASE), "years"),
    # "aged X months", "aged X years"
    (re.compile(r"aged\s+(\d+)\s+month[s]?", re.IGNORECASE), "months"),
    (re.compile(r"aged\s+(\d+)\s+year[s]?", re.IGNORECASE), "years"),
]


def _extract_age(text: str) -> str:
    """Extract an age string from detail page text.

    Returns e.g. "9 months", "19 months", "3 years", or "" if not found.
    """
    for pattern, unit in _AGE_PATTERNS:
        m = pattern.search(text)
        if m:
            num = int(m.group(1))
            label = unit if num != 1 else unit[:-1]  # singular
            return f"{num} {label}"
    return ""


class StarfishChecker(SiteChecker):
    site_name = "Starfish Dog Rescue"
    data_file = "starfish.txt"

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
        """Parse listing page, visit detail pages for available dogs only."""
        soup = BeautifulSoup(raw, "html.parser")

        dog_cards = self._parse_available_cards(soup)
        if not dog_cards:
            return []

        dogs: list[Dog] = []
        for name, breed, gender, url in dog_cards:
            detail_html = self._fetch_detail(url)
            age, photo_url = self._parse_detail(detail_html)

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status="Available",
                    location=LOCATION,
                    photo_url=photo_url,
                )
            )

        return dogs

    # ── listing page helpers ───────────────────────────────────────

    @staticmethod
    def _parse_available_cards(
        soup: BeautifulSoup,
    ) -> list[tuple[str, str, str, str]]:
        """Extract (name, breed, gender, url) from available-dog cards.

        Only processes the first dp-dfg-container (available dogs).
        Containers 1 (not-ready) and 2 (reserved) are skipped.
        """
        containers = soup.select(".dp-dfg-container")
        if not containers:
            return []

        results: list[tuple[str, str, str, str]] = []
        seen: set[str] = set()

        for item in containers[0].select(".dp-dfg-item"):
            # Get the title
            title_el = item.select_one(".entry-title a")
            title = title_el.get_text(strip=True) if title_el else ""

            # Get the detail URL
            link_el = item.select_one(".dp-dfg-more-button")
            url = cast(str, link_el.get("href", "")) if link_el else ""
            if not url and title_el:
                # fallback: use title link
                url = cast(str, title_el.get("href", ""))
            if not url or url in seen:
                continue
            seen.add(url)

            name, breed, gender = _parse_title(title)
            if not name:
                continue

            results.append((name, breed, gender, url))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        """Fetch a dog detail page. Overrideable for testing."""
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str) -> tuple[str, str]:
        """Extract age and photo_url from a detail page.

        Returns (age, photo_url).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove noisy elements before text extraction
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe"]):
            tag.decompose()

        body_text = soup.get_text(separator=" ")
        age = _extract_age(body_text)

        # Photo: first wp-content image that isn't a logo
        photo_url = ""
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "wp-content/uploads" in src:
                low = src.lower()
                if "logo" not in low and "facebook" not in low and "icon" not in low:
                    photo_url = src
                    break

        return age, photo_url

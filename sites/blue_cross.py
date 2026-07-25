"""Blue Cross site checker — scrapes centre-specific rehoming pages.

Blue Cross centres share the same Drupal CMS platform. A single checker class
parameterised by centre handles both Bromsgrove and Burford.

Each centre page lists pets in a carousel with cards (name, breed, sex, age).
Individual pet profiles at /pet/{slug}/ provide full data including species,
which is used to filter out non-dogs.
"""

from __future__ import annotations

import re
from typing import ClassVar

import cloudscraper
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

BASE_URL = "https://www.bluecross.org.uk"

# Known centre configurations — path, display name, data file slug.
CENTRES: dict[str, dict[str, str]] = {
    "bromsgrove": {
        "path": "/west-midlands-bromsgrove-rehoming-centre",
        "name": "Bromsgrove",
    },
    "burford": {
        "path": "/oxfordshire-burford-rehoming-centre",
        "name": "Burford",
    },
}


class BlueCrossChecker(SiteChecker):
    """Scrapes a single Blue Cross rehoming centre for available dogs."""

    site_name: str
    data_file: str

    _centre_path: str
    _centre_name: str

    # Shared scraper with cookie jar for Cloudflare bypass
    _scraper: ClassVar[cloudscraper.CloudScraper | None] = None

    def __init__(self, data_dir: str, centre_key: str) -> None:
        if centre_key not in CENTRES:
            raise ValueError(
                f"Unknown Blue Cross centre: {centre_key!r}. "
                f"Valid keys: {list(CENTRES)}"
            )
        cfg = CENTRES[centre_key]
        self._centre_path = cfg["path"]
        self._centre_name = cfg["name"]
        self.site_name = f"Blue Cross {self._centre_name}"
        self.data_file = f"blue-cross-{centre_key}.txt"
        super().__init__(data_dir)

    @classmethod
    def _get_scraper(cls) -> cloudscraper.CloudScraper:
        """Return a shared cloudscraper instance (lazy init)."""
        if cls._scraper is None:
            cls._scraper = cloudscraper.create_scraper()
        return cls._scraper

    # ------------------------------------------------------------------
    # fetch / parse
    # ------------------------------------------------------------------

    def fetch(self) -> str:
        """Fetch the centre listing page HTML."""
        scraper = self._get_scraper()
        url = f"{BASE_URL}{self._centre_path}"
        resp = scraper.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing HTML, visit each pet profile, return Dog objects."""
        soup = BeautifulSoup(raw, "html.parser")
        pet_links: list[tuple[str, str]] = []  # (name, url)

        for a in soup.select("a.m-pet-listing-item"):
            href = a.get("href", "")
            if not href:
                continue
            name_el = a.select_one("h4 span")
            name = name_el.get_text(strip=True) if name_el else ""
            if href.startswith("/"):
                href = f"{BASE_URL}{href}"
            pet_links.append((name, href))

        dogs: list[Dog] = []
        for name, url in pet_links:
            profile = self._fetch_profile(url)
            parsed = self._parse_profile(profile, name=name, url=url)
            if parsed is not None:
                dogs.append(parsed)

        return dogs

    # ------------------------------------------------------------------
    # profile helpers
    # ------------------------------------------------------------------

    def _fetch_profile(self, url: str) -> str:
        """Fetch a single pet profile page. Overrideable for testing."""
        scraper = self._get_scraper()
        resp = scraper.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_profile(
        html: str, *, name: str, url: str
    ) -> Dog | None:
        """Parse a pet profile page. Returns None for non-dog species."""
        soup = BeautifulSoup(html, "html.parser")

        species = ""
        breed = ""
        sex = ""
        age = ""
        location = ""

        for dt in soup.select("dt[title]"):
            title = dt.get("title", "").strip()
            if title.startswith("Species - "):
                species = title.split(" - ")[1].split()[0].strip().lower()
                dd = dt.find_next("dd")
                if dd:
                    breed = _clean_breed(dd.get_text(" ", strip=True))
            elif title in ("Male", "Female"):
                sex = title
            elif "year" in title.lower() or "month" in title.lower():
                age = title
            elif "rehoming centre" in title.lower():
                location = title

        # Only return dogs
        if species != "dog":
            return None

        photo_url = _extract_photo(soup)

        return Dog(
            name=name,
            age=age,
            gender=sex,
            breed=breed,
            url=url,
            location=location,
            photo_url=photo_url,
        )


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------


def _clean_breed(raw: str) -> str:
    """Collapse whitespace and remove trailing commas from breed text."""
    breed = re.sub(r"\s+", " ", raw).strip()
    breed = breed.strip(",").strip()
    # Remove colour suffixes that Blue Cross appends (e.g. ", Black And White")
    # by keeping everything up to the first obvious colour-only suffix.
    # Heuristic: if a comma is followed by words that are all colour-ish,
    # drop it.  But colour detection is fragile; keep the full breed for now.
    return breed


def _extract_photo(soup: BeautifulSoup) -> str:
    """Extract the best photo URL from a pet profile page.

    Tries og:image meta first, then the first pet profile image.
    """
    # og:image
    og = soup.select_one('meta[property="og:image"]')
    if og:
        src = og.get("content", "")
        if src:
            return src

    # First image in the pet profile section
    for img in soup.select(".t-pet-profile img"):
        src = img.get("src", "")
        if src and "/pet_profile/" in src:
            if src.startswith("/"):
                src = f"{BASE_URL}{src}"
            return src

    return ""

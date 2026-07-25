"""Forest Dog Rescue site checker.

Fetches the /meet-the-dogs/ listing page, extracts dog cards from the
"Available Dogs" section, then visits each detail page for full data.
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LOCATION = "Far Forest, Kidderminster DY14 9DX"


def _name_from_url(url: str) -> str:
    """Derive a display name from a dog detail URL.

    /dogs/cheddar/ → Cheddar
    /dogs/millie-buddy/ → Millie & Buddy (we fall back to title-case)
    """
    import re

    m = re.search(r"/dogs/([^/]+)/?$", url)
    if not m:
        return ""
    slug = m.group(1)
    return slug.replace("-", " ").title()


class ForestDogRescueChecker(SiteChecker):
    site_name = "Forest Dog Rescue"
    data_file = "forest-dog-rescue.txt"

    LISTING_URL = "https://www.forest-dog-rescue.org.uk/meet-the-dogs/"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
    }

    def fetch(self) -> str:
        resp = requests.get(self.LISTING_URL, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing page, visit detail pages, filter reserved."""
        soup = BeautifulSoup(raw, "html.parser")

        # Collect all dog links within the Available Dogs section
        dog_urls = self._parse_available_dog_urls(soup)
        if not dog_urls:
            return []

        dogs: list[Dog] = []
        for name, url in dog_urls:
            detail_html = self._fetch_detail(url)
            age, gender, breed, photo_url = self._parse_detail(detail_html, name)

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
    def _parse_available_dog_urls(soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Extract (name, url) pairs from the Available Dogs section only.

        Name is derived from the URL slug (e.g. /dogs/cheddar/ → Cheddar).
        """
        stop_headings = {"dogs under assessment", "reserved dogs",
                         "rehomed dogs", "interested in a dog"}

        avail_h2 = None
        for h2 in soup.find_all("h2"):
            if h2.get_text(strip=True).lower() == "available dogs":
                avail_h2 = h2
                break

        if not avail_h2:
            return []

        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for elem in avail_h2.find_all_next():
            if elem.name == "h2":
                text = elem.get_text(strip=True).lower()
                if text in stop_headings:
                    break
                continue

            if elem.name == "a":
                href = elem.get("href", "")
                if "/dogs/" in href and href not in seen:
                    seen.add(href)
                    name = _name_from_url(href)
                    if name:
                        results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        """Fetch a dog detail page. Overrideable for testing."""
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, fallback_name: str) -> tuple[str, str, str, str]:
        """Extract age, gender, breed, photo_url from a detail page.

        Returns (age, gender, breed, photo_url).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove noisy elements before text extraction
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe"]):
            tag.decompose()

        body_text = soup.get_text(separator="\n")
        lines = body_text.splitlines()

        age = ""
        gender = ""
        breed = ""
        photo_url = ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.lower() in ("age:", "age") or stripped.lower().startswith("age:"):
                val = stripped[4:].strip() if stripped.lower().startswith("age:") else ""
                if not val:
                    val = _next_nonblank_fdr(lines, i + 1)
                age = val
            elif stripped.lower() in ("sex:", "sex") or stripped.lower().startswith("sex:"):
                val = stripped[4:].strip() if stripped.lower().startswith("sex:") else ""
                if not val:
                    val = _next_nonblank_fdr(lines, i + 1)
                gender = val
            elif stripped.lower().startswith("breed:"):
                val = stripped[6:].strip()
                if not val:
                    val = _next_nonblank_fdr(lines, i + 1)
                breed = val

        # Photo: first wp-content image that isn't a logo
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "wp-content/uploads" in src:
                low = src.lower()
                if "logo" not in low and "facebook" not in low and "icon" not in low:
                    photo_url = src
                    break

        return age, gender, breed, photo_url


def _next_nonblank_fdr(lines: list[str], start: int) -> str:
    """Return the next non-blank line starting at index `start`, or ''."""
    while start < len(lines):
        val = lines[start].strip()
        if val:
            return val
        start += 1
    return ""

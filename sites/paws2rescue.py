"""Paws2Rescue site checker.

Uses the WP REST API for listing data (with server-side filtering by sex
and size) and scrapes detail pages for age and breed.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

# WP REST API taxonomy term IDs
_SEX_FEMALE = 17
_SIZE_SMALL = 18
_SIZE_SMALL_TO_MEDIUM = 30
_SIZE_MEDIUM = 19

# Title suffixes that indicate a dog is not available
_STATUS_SUFFIXES_TO_SKIP = frozenset({"Reserved", "Soon Available", "Available Soon"})


class Paws2RescueChecker(SiteChecker):
    site_name = "Paws2Rescue"
    data_file = "paws2rescue.txt"
    bypass_distance_filter = True  # Dogs transported from Romania to UK

    API_URL = (
        "https://paws2rescue.com/wp-json/wp/v2/dog"
        f"?per_page=100&sex={_SEX_FEMALE}"
        f"&size={_SIZE_SMALL},{_SIZE_SMALL_TO_MEDIUM},{_SIZE_MEDIUM}"
        "&_embed=true"
    )

    # ── public API ──────────────────────────────────────────────────

    def fetch(self) -> str:
        """Fetch filtered dog listings from the WP REST API.

        Returns JSON text so parse() can decode it.
        """
        resp = requests.get(self.API_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse JSON response into Dog objects (no detail scraping yet)."""
        import json

        data = json.loads(raw)
        dogs: list[Dog] = []
        for item in data:
            dog = self._parse_single(item)
            if dog is not None:
                dogs.append(dog)
        return dogs

    def get_all(self) -> list[Dog]:
        """Fetch, parse, and scrape detail pages for all dogs."""
        raw = self.fetch()
        dogs = self.parse(raw)
        for dog in dogs:
            try:
                detail_html = self._fetch_detail(dog.url)
                age, breed, photo_url = self._parse_detail(detail_html)
                if age:
                    dog.age = age
                if breed:
                    dog.breed = breed
                if photo_url and not dog.photo_url:
                    dog.photo_url = photo_url
            except Exception:
                pass
        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, scrape detail pages, filter, and return new dogs.

        Post-scrape filtering: female only (already filtered at API),
        age <= 12 months, small/medium size (already filtered at API).
        """
        dogs = self.get_all()

        # Post-scrape age filter
        filtered = [d for d in dogs if self._age_months(d.age) <= 12]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new

    # ── internal helpers ────────────────────────────────────────────

    def _parse_single(self, item: dict) -> Dog | None:
        """Parse a single dog from the WP REST API response item.

        Returns None for reserved/not-available dogs.
        """
        title = item.get("title", {}).get("rendered", "")
        link = item.get("link", "")
        if not title or not link:
            return None

        # Filter out reserved / not-available dogs.
        # Status suffixes are appended to the title with 2+ spaces.
        if "  " in title:
            suffix = " ".join(title.rsplit("  ", 1)[1].split())
            if suffix in _STATUS_SUFFIXES_TO_SKIP:
                return None

        embedded = item.get("_embedded", {})

        gender = self._normalize_gender(
            self._parse_term_names(embedded, "sex", item.get("sex", []))
        )
        location = self._parse_location_names(embedded, item.get("location", []))
        photo_url = self._parse_featured_media(embedded)

        # Size goes into status for display (the Dog model doesn't have a
        # dedicated size field; we follow the convention of other scrapers
        # by placing non-standard metadata in status)
        size_str = self._parse_term_names(embedded, "size", item.get("size", []))

        return Dog(
            name=title,
            age="",                       # Filled from detail page
            gender=gender,
            breed="",                      # Filled from detail page
            url=link,
            status=size_str,
            location=location,
            photo_url=photo_url,
        )

    def _fetch_detail(self, url: str) -> str:
        """Fetch a detail page HTML."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _parse_detail(self, html: str) -> tuple[str, str, str]:
        """Parse age, breed, and photo_url from a detail page.

        Returns (age_str, breed_str, photo_url). All may be empty strings.
        """
        soup = BeautifulSoup(html, "html.parser")
        age = self._extract_detail_field(soup, "Age")
        breed = self._extract_detail_field(soup, "Breed")
        photo_url = self._extract_og_image(soup)
        return age, breed, photo_url

    @staticmethod
    def _extract_og_image(soup) -> str:
        """Extract the best dog image from a detail page.

        Tries in order:
        1. og:image meta tag (but reject known site-default images)
        2. twitter:image meta tag
        3. Largest wp-image-* img element on the page
        """
        # Known site-default/placeholder images to reject
        _DEFAULT_IMAGES = {"/SuPer.jpg", "/paws2rescue-icon"}

        # Try og:image first
        og = soup.select_one('meta[property="og:image"]')
        if og:
            src = og.get("content", "")
            if src and not any(bad in src for bad in _DEFAULT_IMAGES):
                return src

        # Try twitter:image
        tw = soup.select_one('meta[name="twitter:image"]')
        if tw:
            src = tw.get("content", "")
            if src and not any(bad in src for bad in _DEFAULT_IMAGES):
                return src

        # Fallback: find the largest wp-image-* img on the page.
        # The site uses Breeze lazy-loading — real URLs are in data-breeze,
        # not src (which is a base64 SVG placeholder).
        best_src = ""
        best_area = 0
        for img in soup.select("img[class*='wp-image-']"):
            alt = img.get("alt", "").lower()
            # Skip logos, icons, QR codes, and other site chrome
            if any(kw in alt for kw in ("logo", "qr", "icon", "paypal", "storage")):
                continue
            # Try data-breeze first (lazy-loaded), then src
            src = img.get("data-breeze", "") or img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(bad in src for bad in _DEFAULT_IMAGES):
                continue
            w = int(img.get("width", 0) or 0)
            h = int(img.get("height", 0) or 0)
            area = w * h
            if area > best_area:
                best_area = area
                best_src = src
        if best_src:
            return best_src

        return ""

    @staticmethod
    def _normalize_gender(raw: str) -> str:
        """Normalize gender strings from the WP taxonomy.

        The site uses "Good Girl" for female and "Good Boy" for male.
        """
        if not raw:
            return ""
        lower = raw.lower()
        if "girl" in lower or "female" in lower:
            return "Female"
        if "boy" in lower or "male" in lower:
            return "Male"
        return raw

    # ── static helpers ──────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _parse_term_names(embedded: dict, taxonomy: str, term_ids: list[int]) -> str:
        """Extract term names from _embedded wp:term data."""
        names: list[str] = []
        for group in embedded.get("wp:term", []):
            for term in group:
                if term.get("taxonomy") == taxonomy:
                    names.append(term["name"])
        return ", ".join(names) if names else ""

    @staticmethod
    def _parse_location_names(embedded: dict, term_ids: list[int]) -> str:
        """Extract location term names from _embedded wp:term data."""
        names: list[str] = []
        for group in embedded.get("wp:term", []):
            for term in group:
                if term.get("taxonomy") == "location":
                    names.append(term["name"])
        return ", ".join(names) if names else ""

    @staticmethod
    def _parse_featured_media(embedded: dict) -> str:
        """Extract featured image URL from _embedded data.

        Tries wp:featuredmedia first; if that's missing, doesn't
        fetch via wp:attachment links (too slow).  The check() method
        will fill photo_url from the detail page instead.
        """
        media_list = embedded.get("wp:featuredmedia", [])
        if media_list:
            return media_list[0].get("source_url", "")
        return ""

    @staticmethod
    def _extract_detail_field(soup: BeautifulSoup, field_name: str) -> str:
        """Extract a field value from a detail page.

        The detail page uses mathematical bold Unicode characters for
        field labels (e.g. Name, Age, Breed in bold). We normalize both
        the field label and the page text for matching.
        """
        normal_name = _normalize_unicode(field_name)
        for p in soup.select("p"):
            text = p.get_text(strip=True)
            normal_text = _normalize_unicode(text)
            # Match "Field: value" pattern
            prefix = normal_name + ":"
            if normal_text.lower().startswith(prefix.lower()):
                # Return the original (non-normalized) text after the colon
                colon_idx = text.find(":")
                if colon_idx != -1:
                    return text[colon_idx + 1:].strip()
        return ""

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable."""
        age_str = age_str.lower().strip()
        if not age_str:
            return 999
        # "approx. 2 Years old", "approx. 7 Months old", "7 Months", "1 Year"
        year_match = re.search(r"(\d+)\s*years?\b", age_str)
        if year_match:
            return int(year_match.group(1)) * 12
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if month_match:
            return int(month_match.group(1))
        return 999


def _normalize_unicode(text: str) -> str:
    """Normalize mathematical bold Unicode to plain ASCII for matching.

    The detail pages use MATHEMATICAL BOLD CAPITAL/SMALL letters
    (U+1D5D4-U+1D5ED, U+1D5EE-U+1D607) for field labels.
    """
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        # MATHEMATICAL BOLD CAPITAL A-Z: U+1D5D4 - U+1D5ED → A-Z
        if 0x1D5D4 <= cp <= 0x1D5ED:
            result.append(chr(ord("A") + (cp - 0x1D5D4)))
        # MATHEMATICAL BOLD SMALL a-z: U+1D5EE - U+1D607 → a-z
        elif 0x1D5EE <= cp <= 0x1D607:
            result.append(chr(ord("a") + (cp - 0x1D5EE)))
        else:
            result.append(ch)
    return "".join(result)

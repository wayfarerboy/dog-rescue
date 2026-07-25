"""RSPCA Brighton & The Heart of Sussex site checker.

Scrapes https://rspca-brighton.org.uk/animals/dogs/ — a Divi-themed
WordPress site with portfolio-grid listing cards and detail pages.
"""

from __future__ import annotations

import re
from typing import ClassVar

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class RSPCABrightonChecker(SiteChecker):
    site_name = "RSPCA Brighton"
    data_file = "rspca-brighton.txt"

    LISTING_URL = "https://rspca-brighton.org.uk/animals/dogs/"

    # Status excerpts on listing cards that mean "not available"
    SKIP_STATUSES: ClassVar[frozenset[str]] = frozenset(
        {"Reserved", "No more applications being taken"}
    )

    def fetch(self) -> str:
        """Fetch the listing page HTML."""
        resp = requests.get(self.LISTING_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _fetch_detail(self, url: str) -> str:
        """Fetch a detail page HTML. Overridable for testing."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for item in soup.select(".et_pb_portfolio_item"):
            name_el = item.select_one("h3.et_pb_module_header a")
            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            link = name_el.get("href", "")
            if not link:
                continue

            # Status from excerpt paragraph (may be absent → available)
            excerpt_el = item.select_one("p.et_pb_portfolio_excerpt")
            status = excerpt_el.get_text(strip=True) if excerpt_el else ""

            # Skip dogs marked Reserved or No more applications
            if status in self.SKIP_STATUSES:
                continue

            # Photo URL from the card image
            img_el = item.select_one("img")
            photo_url = img_el.get("src", "") if img_el else ""

            # Fetch detail page for breed, age, gender, location
            try:
                detail_html = self._fetch_detail(link)
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                breed = self._detail_field(detail_soup, "Breed:")
                age = self._detail_field(detail_soup, "Age:")
                gender_raw = self._detail_field(detail_soup, "Sex:")
                location = self._detail_field(detail_soup, "Location:")
            except Exception:
                # If detail fetch fails, skip this dog
                continue

            # Normalize gender (handles "Spayed Female", "Neutered Male",
            # and known typo "Make" → Male)
            gender = self._normalize_gender(gender_raw)

            # Quick filter: only females
            if gender != "Female":
                continue

            # Parse age and filter to ≤12 months
            months = self._parse_age_months(age)
            if months > 12:
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    location=location if location else "Brighton",
                    url=link,
                    status=status if status else "Available",
                    photo_url=photo_url,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _detail_field(soup, label: str) -> str:
        """Extract a field value from the detail page.

        Fields are in <p><strong>Label:</strong><br/>Value</p> format.
        """
        for p in soup.select(".et_pb_post_content p"):
            strong = p.find("strong")
            if strong and strong.get_text(strip=True) == label:
                full_text = p.get_text()
                value = full_text[len(strong.get_text()):].strip(": ").strip()
                return value
        return ""

    @staticmethod
    def _normalize_gender(raw: str) -> str:
        """Normalize gender strings from detail pages.

        Handles "Spayed Female", "Neutered Male", and the known typo
        "Make" for "Male".
        """
        if not raw:
            return ""
        lower = raw.lower()
        if "female" in lower:
            return "Female"
        if "male" in lower or "make" in lower:
            return "Male"
        return ""

    @staticmethod
    def _parse_age_months(age_text: str) -> int:
        """Parse age string into total months.

        Handles formats like:
          - "4 years"
          - "1 year approx."
          - "6 months"
          - "18 months approx."
          - "2-3 years approx."          -> lower bound (24 months)
          - "18 months - 2 years approx." -> lower bound (18 months)

        For age ranges, uses the lower bound.
        """
        if not age_text:
            return 0

        # For ranges, extract the lower bound.
        # Strategy: find the first number. If it's part of a range
        # (precedes a dash/to), use it as the count; otherwise use
        # the first number found anywhere. Determine the unit
        # (years/months) from the full text.
        text = age_text.lower()

        # Split on range markers to get the lower-bound portion
        parts = re.split(r"\s*(?:\u2013|\u2014|-|to)\s*", text)
        first_part = parts[0].strip()

        # Try to find a number + unit in the first part.
        # If the unit only appears after the range (e.g. "2-3 years"),
        # fall back to searching the full text for the unit.
        num_match = re.search(r"(\d+)", first_part)
        if not num_match:
            return 0
        count = int(num_match.group(1))

        # Determine unit: check first_part first, then full text
        if re.search(r"months?", first_part):
            return count
        if re.search(r"years?", first_part):
            return count * 12
        if re.search(r"months?", text):
            return count
        if re.search(r"years?", text):
            return count * 12
        return 0

"""All Dogs Matter site checker."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class AllDogsMatterChecker(SiteChecker):
    site_name = "All Dogs Matter"
    data_file = "all-dogs-matter.txt"

    BASE_URL = "https://alldogsmatter.co.uk/dogs/"
    MAX_PAGES = 20  # safety cap; site has ~17 pages

    # ── public API ─────────────────────────────────────────────────

    def fetch(self) -> str:
        """Fetch first page. Required by ABC; pagination handled in check()."""
        return self._fetch_page(1) or ""

    def parse(self, raw: str) -> list[Dog]:
        """Parse HTML from a listing page into filtered Dog objects."""
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select(".grid-block.card"):
            dog = self._parse_card(card)
            if dog is None:
                continue
            dogs.append(dog)

        return dogs

    def check(self) -> list[Dog]:
        """Paginate through all pages, collect + filter dogs, diff against saved."""
        all_dogs: list[Dog] = []
        for page in range(1, self.MAX_PAGES + 1):
            html = self._fetch_page(page)
            if html is None:
                break
            dogs = self.parse(html)
            all_dogs.extend(dogs)

        new = self.diff(all_dogs)
        if new:
            self._save_current(all_dogs)
        return new

    # ── internal ───────────────────────────────────────────────────

    def _fetch_page(self, page_num: int) -> str | None:
        """Fetch a single page. Returns HTML or None on 404/error."""
        url = self.BASE_URL if page_num == 1 else f"{self.BASE_URL}page/{page_num}/"
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            return None

    def _parse_card(self, card) -> Dog | None:
        """Parse a single card element. Returns Dog or None if filtered out."""
        # Extract name and profile URL
        link_el = card.select_one("a.card-image-link")
        name_el = card.select_one(".block-content h3 a")
        name = name_el.get_text(strip=True) if name_el else ""
        url = link_el.get("href", "") if link_el else ""

        # Extract text block
        p_el = card.select_one(".block-content p")
        if not p_el:
            return None
        text = p_el.get_text()

        # Skip adopted dogs
        if re.search(r"adopted", text, re.IGNORECASE):
            return None

        # Extract fields from text
        breed = self._extract_field(text, "Breed")
        age = self._extract_field(text, "Age")
        gender = self._extract_field(text, "Gender")
        location = self._extract_field(text, "Location")

        # Post-scrape filters
        if gender != "Female":
            return None
        age_months = self._parse_age_months(age)
        if age_months is None or age_months > 12:
            return None

        return Dog(
            name=name,
            age=age,
            gender=gender,
            breed=breed,
            url=url,
            status="",
            location=location,
        )

    @staticmethod
    def _extract_field(text: str, field: str) -> str:
        """Extract a labelled field value from card text.

        Text format: "Breed: X Age: Y Gender: Z Location: W ..."
        """
        pattern = rf"{field}:\s*(.+?)(?=\s+(?:Breed|Age|Gender|Location|Can|More|$))"
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _parse_age_months(age_str: str) -> int | None:
        """Parse an age string into total months. Returns None if unparseable.

        Examples:
            "8 Months" -> 8
            "1 year old" -> 12
            "1-2 years old" -> 12  (first number)
            "4 years 3 months" -> 51
            "approx. 18 months" -> 18
        """
        age_str = age_str.strip()
        if not age_str:
            return None

        # Normalize ranges like "1-2 years" -> "1 years" (use first number)
        age_str = re.sub(r"(\d+)\s*-\s*\d+", r"\1", age_str)

        total = 0.0
        found = False

        # Match "X years" / "X year"
        year_m = re.search(r"(\d+(?:\.\d+)?)\s*years?\b", age_str, re.IGNORECASE)
        if year_m:
            total += float(year_m.group(1)) * 12
            found = True

        # Match "X months" / "X month"
        month_m = re.search(r"(\d+(?:\.\d+)?)\s*months?\b", age_str, re.IGNORECASE)
        if month_m:
            total += float(month_m.group(1))
            found = True

        if not found:
            return None

        return int(total)

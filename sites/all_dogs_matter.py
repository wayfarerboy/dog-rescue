"""All Dogs Matter rescue site checker."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class AllDogsMatterChecker(SiteChecker):
    site_name = "All Dogs Matter"
    data_file = "all-dogs-matter.txt"

    BASE_URL = "https://alldogsmatter.co.uk"

    def _page_url(self, page_num: int) -> str:
        """Build the URL for a given page number."""
        if page_num == 1:
            return f"{self.BASE_URL}/dogs/"
        return f"{self.BASE_URL}/dogs/page/{page_num}/"

    def _fetch_page(self, page_num: int) -> str:
        """Fetch HTML for a single paginated page."""
        resp = requests.get(self._page_url(page_num), timeout=30)
        resp.raise_for_status()
        return resp.text

    def fetch(self) -> str:
        """Fetch page 1 HTML (paginated iteration handled by check())."""
        return self._fetch_page(1)

    def _get_max_pages(self, html: str) -> int:
        """Parse the page-navigation links and return the highest page number."""
        soup = BeautifulSoup(html, "html.parser")
        max_page = 1
        for link in soup.select("a.page-numbers"):
            try:
                num = int(link.get_text(strip=True))
                max_page = max(max_page, num)
            except ValueError:
                pass
        return max_page

    def parse(self, raw: str) -> list[Dog]:
        """Parse a single page of HTML into Dog objects (excludes adopted)."""
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select(".grid-block.card"):
            content = card.select_one(".block-content")
            if not content:
                continue

            # Check all paragraphs for "adopted" or "reserved" — skip if found
            paragraphs = [p.get_text(strip=True) for p in content.select("p")]
            if any("adopted" in p.lower() or "reserved" in p.lower() for p in paragraphs):
                continue
            # Cards with no paragraph have no data to extract
            if not paragraphs:
                continue

            # Name + URL from h3 > a
            name_el = content.select_one("h3 a")
            if not name_el:
                continue
            href = name_el.get("href", "")
            if not href:
                continue
            name = name_el.get_text(strip=True)

            # The main paragraph has breed, age, gender, location
            main_text = paragraphs[0]

            breed = self._extract_field(main_text, "Breed")
            age = self._extract_field(main_text, "Age")
            gender = self._extract_field(main_text, "Gender")
            location = self._extract_field(main_text, "Location")

            # Photo from .bg div's data-back attribute
            photo_url = ""
            img_div = card.select_one(".bg")
            if img_div:
                photo_url = img_div.get("data-back", "")

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=href,
                    status="Available",
                    location=location,
                    photo_url=photo_url,
                )
            )

        return dogs

    @staticmethod
    def _extract_field(text: str, field: str) -> str:
        """Extract a named field from card paragraph text.

        Text format: "Breed: Mastiff X Age: 5 year old Gender: Female
        Location: Waltham Abbey Can Lacey live with cats?..."
        """
        # Field-like delimiters (end with colon)
        field_delims = ["Breed", "Age", "Gender", "Location"]
        # Text markers that end a value (no colon in source)
        text_markers = ["Can\\b", "More about", "Please", "Special"]

        others = [f for f in field_delims if f != field]
        field_alt = "|".join(others) if others else None
        marker_alt = "|".join(text_markers)

        lookahead_parts = []
        if field_alt:
            lookahead_parts.append(rf"(?:{field_alt}):")
        lookahead_parts.append(rf"(?:{marker_alt})")
        lookahead = "|".join(lookahead_parts)

        pattern = rf"{field}:\s*(.+?)(?=\s+(?:{lookahead})|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable."""
        age_str = age_str.lower().strip()
        if not age_str:
            return 999
        # "5 year old", "2 years approx", "4-5 years"
        year_match = re.search(r"(\d+)(?:[-\s]*\d+\s*)?\s*years?\b", age_str)
        if year_match:
            return int(year_match.group(1)) * 12
        # "9 Months", "1 Month"
        month_match = re.search(r"(\d+)\s*month", age_str)
        if month_match:
            return int(month_match.group(1))
        return 999

    def check(self) -> list[Dog]:
        """Fetch all pages, parse, filter and return new dogs.

        Post-scrape filtering: female only, age <= 12 months.
        Saves the filtered list for future diffing.
        """
        raw = self.fetch()
        max_pages = self._get_max_pages(raw)

        all_dogs = self.parse(raw)
        for page in range(2, max_pages + 1):
            page_raw = self._fetch_page(page)
            all_dogs.extend(self.parse(page_raw))

        # Post-scrape filtering
        filtered = [
            d for d in all_dogs
            if d.gender == "Female" and self._age_months(d.age) <= 12
        ]

        new = self.diff(filtered)
        if new:
            self._save_current(filtered)
        return new

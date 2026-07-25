"""Spaniel Aid site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class SpanielAidChecker(SiteChecker):
    site_name = "Spaniel Aid"
    data_file = "spaniel-aid.txt"

    URL = "https://spanielaid.co.uk/available-dogs/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for li in soup.select("li.bricks-layout-item.repeater-item"):
            link = li.select_one("a[href]")
            if not link:
                continue
            url = link.get("href", "")
            if not url:
                continue

            name_el = li.select_one('[data-field-id="obwypa"]')
            breed_el = li.select_one('[data-field-id="aqprwx"]')
            age_el = li.select_one('[data-field-id="euosuj"]')
            location_el = li.select_one('[data-field-id="xglchg"]')
            gender_el = li.select_one('[data-field-id="aalwfs"]')

            raw_name = name_el.get_text(strip=True) if name_el else ""
            name, status = self._extract_name_and_status(raw_name)

            breed = self._clean_field(breed_el) if breed_el else ""
            age = self._clean_field(age_el) if age_el else ""
            location = self._clean_field(location_el) if location_el else ""
            gender = self._clean_field(gender_el) if gender_el else ""

            # Post-scrape filtering: female + under 1 year (<=12 months)
            if gender != "Female":
                continue
            age_months = self._parse_age_months(age)
            if age_months is None or age_months > 12:
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status=status,
                    location=location,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _clean_field(el) -> str:
        """Get text from an element, stripping icon img alt text."""
        # Remove img tags then get remaining text
        for img in el.select("img"):
            img.decompose()
        return el.get_text(strip=True)

    @staticmethod
    def _extract_name_and_status(raw: str) -> tuple[str, str]:
        """Split name from status.

        The h4 contains either:
          "Milo SA5125"
          "Chisel SA5431 \u2013 Foster View To Adopt"
          "Daisy SA5592 \u2013 Reserved while we review the current applications."

        Returns (name, status). Status defaults to "Available".
        """
        # Look for an en-dash or em-dash separator
        match = re.split(r"\s*[\u2013\u2014]\s*", raw, maxsplit=1)
        if len(match) == 2:
            return match[0].strip(), match[1].strip()
        return raw.strip(), "Available"

    @staticmethod
    def _parse_age_months(age_str: str) -> int | None:
        """Parse an age string into total months. Returns None if unparseable.

        Examples:
          "15 months" → 15
          "4 years 6 months" → 54
          "6 years" → 72
        """
        age_str = age_str.strip().lower()
        if not age_str:
            return None

        years_match = re.search(r"(\d+)\s*years?", age_str)
        months_match = re.search(r"(\d+)\s*months?", age_str)

        years = int(years_match.group(1)) if years_match else 0
        months = int(months_match.group(1)) if months_match else 0

        if not years_match and not months_match:
            return None

        return years * 12 + months

"""Jerry Green Dog Rescue site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class JerryGreenChecker(SiteChecker):
    site_name = "Jerry Green Dog Rescue"
    data_file = "jerry-green.txt"

    URL = "https://www.jerrygreendogs.org.uk/dogs/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select(".card.dog"):
            link_el = card.select_one("a.block-link")
            if not link_el:
                continue

            href = link_el.get("href", "")
            if not href:
                continue

            name = self._text(card, "h2.card__title span.chevron-wrap")
            breed = self._text(card, "li.breed")
            age = self._text(card, "li.age")
            gender = self._text(card, "li.sex")
            status = self._text(card, "div.sticker span")
            size = self._extract_size(card)

            # Post-scrape filtering: female only, age <= 12 months
            if gender != "Female":
                continue
            age_months = self._parse_age_months(age)
            if age_months is not None and age_months > 12:
                continue
            if size and size not in ("Small", "Medium"):
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=href,
                    status=status,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_size(card) -> str:
        """Extract size tag ('Small', 'Medium', 'Large') from tick-list."""
        for li in card.select(".card__attributes ul.tick-list li"):
            text = li.get_text(strip=True)
            m = re.match(r"(Small|Medium|Large)\s+breed", text)
            if m:
                return m.group(1)
        return ""

    @staticmethod
    def _parse_age_months(age_str: str) -> int | None:
        """Parse 'X years Y months' into total months. Returns None on failure."""
        if not age_str:
            return None
        m = re.match(r"(\d+)\s+years?\s+(\d+)\s+months?", age_str)
        if not m:
            return None
        years = int(m.group(1))
        months = int(m.group(2))
        return years * 12 + months

"""Second Chance Spaniel Rescue site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class SCSRChecker(SiteChecker):
    site_name = "Second Chance Spaniel Rescue"
    data_file = "scsr.txt"

    URL = "https://secondchancespanielrescue.org.uk/find-a-dog/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for article in soup.select("article.scsr-finder-card"):
            name = self._text(article, "h3")
            status = self._status(article)
            link = self._profile_link(article)
            gender = self._info_field(article, "venus-mars")
            age = self._info_field(article, "calendar-days")
            breed = self._info_field(article, "dog")
            location = self._info_field(article, "location-dot")

            # Filter: female + month-based age only (under 1 year)
            if gender != "Female":
                continue
            if not re.search(r"[Mm]onth", age):
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=link,
                    status=status,
                    location=location,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    def _status(self, article) -> str:
        """Extract status from the scsr-modern-status span."""
        el = article.select_one(".scsr-modern-status")
        if not el:
            return ""
        # The span has an <i> icon inside; get the text after it
        return el.get_text(strip=True)

    def _profile_link(self, article) -> str:
        """Extract profile URL."""
        el = article.select_one("a.scsr-modern-main-btn")
        if el:
            return el.get("href", "")
        # Fallback: any link to the dogs/ path
        for a in article.select("a[href]"):
            href = a.get("href", "")
            if "/dogs/" in href and "secondchancespanielrescue" in href:
                return href
        return ""

    def _info_field(self, article, icon_class: str) -> str:
        """Extract value from an info box: find <i class="fa-..."> then the next <span>."""
        for info_box in article.select(".scsr-modern-info-box"):
            icon = info_box.select_one(f"i.fa-{icon_class}")
            if icon:
                span = info_box.select_one("span")
                if span:
                    return span.get_text(strip=True)
        return ""

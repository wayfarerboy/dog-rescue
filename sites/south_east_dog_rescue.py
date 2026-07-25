"""South East Dog Rescue site checker."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class SouthEastDogRescueChecker(SiteChecker):
    site_name = "South East Dog Rescue"
    data_file = "south-east-dog-rescue.txt"

    BASE_URL = "https://www.sedogrescue.co.uk"
    URL = f"{BASE_URL}/adopt-a-dog/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        # Cards are <li> elements inside the grid <ul>
        for card in soup.select("ul.grid li a.link"):
            name = self._text(card, ".text-xl.font-black")
            if not name:
                continue

            # The detail <ul> contains age, gender, breed as <li> items
            items = card.select("ul.mt-auto li")
            age = self._clean_age(items[0]) if len(items) > 0 else ""
            gender = items[1].get_text(strip=True) if len(items) > 1 else ""
            breed = items[2].get_text(strip=True) if len(items) > 2 else ""

            # Filter: female only, age ≤ 12 months
            if gender != "Female":
                continue
            if self._age_months(age) > 12:
                continue

            href = card.get("href", "")
            url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

            photo_url = self._photo_url(card)

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    location="",
                    photo_url=photo_url,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _clean_age(age_el) -> str:
        """Extract and clean age text, removing Gatsby <!-- --> comments."""
        # get_text() preserves spacing around stripped comments;
        # get_text(strip=True) collapses "1 year<!-- --> old" → "1 yearold"
        text = age_el.get_text()
        text = re.sub(r"<!--.*?-->", "", text)
        return " ".join(text.split())

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable."""
        age_str = age_str.lower().strip()
        if not age_str:
            return 999
        # "2 years old", "1 year old"
        year_match = re.search(r"(\d+)\s*years?\b", age_str)
        if year_match:
            return int(year_match.group(1)) * 12
        # "6 months old", "1 month old"
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if month_match:
            return int(month_match.group(1))
        return 999

    @staticmethod
    def _photo_url(card) -> str:
        """Extract photo URL from the Gatsby image wrapper."""
        img = card.select_one("img[data-main-image]")
        if img:
            src = img.get("data-src", "")
            if src:
                return src
            return img.get("src", "")
        return ""

"""South East Dog Rescue site checker."""

from __future__ import annotations

import json
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

    def _fetch_detail(self, url: str) -> str:
        """Fetch a dog detail page. Overrideable for testing."""
        resp = requests.get(url, timeout=30)
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

            # Fetch detail page for status and location
            status = ""
            location = ""
            try:
                detail_html = self._fetch_detail(url)
                status, location = self._parse_detail(detail_html)
            except Exception:
                pass

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status=status,
                    location=location,
                    photo_url=photo_url,
                )
            )

        return dogs

    # ── detail page ───────────────────────────────────────────────

    @staticmethod
    def _parse_detail(html: str) -> tuple[str, str]:
        """Extract status and location from a dog detail page.

        Returns (status, location).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Status: the tagline div under the hero heading
        # Available dogs have a descriptive tagline like "I'm a 8 year old..."
        # Unavailable dogs have "No longer available"
        tagline_div = soup.select_one("div.prose.min-w-full.text-pink-50")
        if tagline_div:
            tagline_text = tagline_div.get_text(strip=True)
            status = (
                "Not Available"
                if "No longer available" in tagline_text
                else "Available"
            )
        else:
            status = ""

        # Location: extracted from JSON-LD structured data
        location = SouthEastDogRescueChecker._extract_location(html)

        return status, location

    @staticmethod
    def _extract_location(html: str) -> str:
        """Extract location from JSON-LD structured data on the detail page."""
        match = re.search(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            return ""
        try:
            data = json.loads(match.group(1))
            # The JSON-LD may be a list (array) of objects
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "address" in item:
                        addr = item["address"]
                        if isinstance(addr, dict):
                            return addr.get("addressLocality", "")
            elif isinstance(data, dict) and "address" in data:
                addr = data["address"]
                if isinstance(addr, dict):
                    return addr.get("addressLocality", "")
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        return ""

    def extract_from_profile(self, html: str) -> dict[str, str]:
        """Extract status and location from a dog's detail page for repair_cache."""
        result: dict[str, str] = {}
        status, location = self._parse_detail(html)
        if status:
            result["status"] = status
        if location:
            result["location"] = location
        return result

    # ── listing-page helpers ───────────────────────────────────────

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

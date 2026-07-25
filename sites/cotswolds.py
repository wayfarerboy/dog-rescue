"""Cotswolds Dogs & Cats Home site checker.

Scrapes the listing page for name, gender, status, and detail page links,
then visits each detail page for age and breed.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class CotswoldsChecker(SiteChecker):
    site_name = "Cotswolds Dogs & Cats Home"
    data_file = "cotswolds.txt"

    BASE_URL = "https://cotswoldsdogsandcatshome.org.uk"
    URL = f"{BASE_URL}/adopt-a-dog/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing page, visit detail pages, filter results."""
        dogs: list[Dog] = []

        # Extract card info from the listing page (skips Reserved section)
        cards = self._parse_listing_cards(raw)

        for card in cards:
            # Pre-filter: female only (avoids unnecessary detail page fetches)
            if card["gender"] != "Female":
                continue

            # Fetch the detail page for age, breed, location, and photo
            detail_html = self._fetch_detail_page(card["url"])
            age, breed, location, photo_url = self._parse_detail_page(detail_html)

            # Post-scrape filter: age ≤ 12 months
            age_months = self._parse_age_months(age)
            if age_months > 12:
                continue

            dogs.append(
                Dog(
                    name=card["name"],
                    age=age,
                    gender=card["gender"],
                    breed=breed,
                    url=card["url"],
                    status=card["status"],
                    location=location,
                    photo_url=photo_url,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    def _fetch_detail_page(self, url: str) -> str:
        """Fetch a dog detail page. Overrideable for testing."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_listing_cards(html: str) -> list[dict]:
        """Parse the listing page HTML into card dicts (name, gender, status, url).

        Skips cards that appear after the 'Dogs that are Reserved' heading.
        """
        soup = BeautifulSoup(html, "html.parser")
        cards: list[dict] = []

        # Find the "Reserved" heading to know where to stop
        reserved_heading = soup.find(
            "h2", string=lambda t: t and "Reserved" in t and "Dogs that are" in t
        )

        for card in soup.select(".vehica-car-card"):
            # Skip cards in the Reserved section (after the heading in DOM)
            if reserved_heading is not None and _is_after(card, reserved_heading):
                continue

            name_el = card.select_one(".vehica-car-card__name")
            if not name_el:
                continue

            name = name_el.get("title", "").strip()
            if not name:
                continue

            url = name_el.get("href", "")
            if not url:
                continue

            # Info singles: [status, gender, species]
            info_items = card.select(".vehica-car-card__info__single")
            status = info_items[0].get_text(strip=True) if len(info_items) > 0 else ""
            gender = info_items[1].get_text(strip=True) if len(info_items) > 1 else ""

            cards.append(
                {
                    "name": name,
                    "gender": gender,
                    "status": status,
                    "url": url,
                }
            )

        return cards

    @staticmethod
    def _parse_detail_page(html: str) -> tuple[str, str, str, str]:
        """Extract age, breed, location, and photo_url from a detail page.

        Returns (age, breed, location, photo_url).
        """
        soup = BeautifulSoup(html, "html.parser")
        age = ""
        breed = ""
        location = ""
        photo_url = ""

        for attr in soup.select(".vehica-car-attributes__name"):
            text = attr.get_text(strip=True)
            # Value is in the sibling .vehica-car-attributes__values element
            if text in ("Age:", "Age::"):
                values_el = attr.find_next_sibling(
                    class_="vehica-car-attributes__values"
                )
                if values_el:
                    age = values_el.get_text(strip=True)
            elif text in ("Breed:", "Breed::"):
                values_el = attr.find_next_sibling(
                    class_="vehica-car-attributes__values"
                )
                if values_el:
                    breed = values_el.get_text(strip=True)

        # Location: .vehica-address span
        addr_span = soup.select_one(".vehica-address span")
        if addr_span:
            location = addr_span.get_text(strip=True)

        # Photo: first .vehica-car-gallery img
        gallery_img = soup.select_one(".vehica-car-gallery img")
        if gallery_img:
            photo_url = gallery_img.get("src", "")

        return age, breed, location, photo_url

    @staticmethod
    def _parse_age_months(age_str: str) -> int:
        """Parse an age string like '1.5 years old' or '6 months old' into total months."""
        if not age_str:
            return 0
        age_str = age_str.lower().strip()
        months = 0
        # "1.5 years old", "2 years old", "1 year old approx"
        year_match = re.search(r"(\d+(?:\.\d+)?)\s*years?\b", age_str)
        if year_match:
            months += int(float(year_match.group(1)) * 12)
        # "6 months old", "1 month old"
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if month_match:
            months += int(month_match.group(1))
        return months


def _is_after(element, reference) -> bool:
    """Check if `element` appears after `reference` in the DOM tree."""
    return any(el is element for el in reference.next_elements)

"""Brighter Days Rescue site checker.

Scrapes the /dogs/available listing page for dog cards, filters out
"Reserved" dogs, then visits each detail page for breed and origin info.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

BASE_URL = "https://brighterdaysrescue.com"
LISTING_URL = f"{BASE_URL}/dogs/available"
LOCATION = "Penkridge, Staffs"


class BrighterDaysChecker(SiteChecker):
    site_name = "Brighter Days Rescue"
    data_file = "brighter-days.txt"

    def fetch(self) -> str:
        resp = requests.get(LISTING_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing page, visit detail pages, filter Reserved."""
        cards = self._parse_listing_cards(raw)

        dogs: list[Dog] = []
        for card in cards:
            detail_html = self._fetch_detail_page(card["url"])
            breed, location = self._parse_detail_page(detail_html)

            dogs.append(
                Dog(
                    name=card["name"],
                    age=card["age"],
                    gender=card["gender"],
                    breed=breed,
                    url=card["url"],
                    status=card.get("status", "Available"),
                    location=location,
                    photo_url=card.get("photo_url", ""),
                )
            )

        return dogs

    # ── internal helpers ──────────────────────────────────────────

    def _fetch_detail_page(self, url: str) -> str:
        """Fetch a dog detail page. Overrideable for testing."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_listing_cards(html: str) -> list[dict]:
        """Parse the listing page HTML into card dicts.

        Returns list of dicts with keys: name, gender, age, status, url, photo_url.
        Skips cards where status is "Reserved".
        """
        soup = BeautifulSoup(html, "html.parser")
        cards: list[dict] = []

        for card in soup.select('[data-dog-card="true"]'):
            # Name
            name_el = card.select_one(".css-1ny3018")
            name = name_el.get_text(strip=True) if name_el else ""

            # Gender + age from p.css-1x3xbk5: "Male, 2 years"
            gender = ""
            age = ""
            ga_el = card.select_one(".css-1x3xbk5")
            if ga_el:
                ga_text = ga_el.get_text(" ", strip=True)
                if "," in ga_text:
                    gender, age = ga_text.split(",", 1)
                    gender = gender.strip()
                    age = age.strip()

            # Status: check for "Reserved" badge
            status = "Available"
            reserved_el = card.select_one(".css-mqy1sm, .css-mmocuf")
            if reserved_el and "reserved" in reserved_el.get_text(strip=True).lower():
                status = "Reserved"

            # Skip reserved dogs
            if status == "Reserved":
                continue

            # Detail URL
            url = ""
            link = card.select_one("a[href]")
            if link:
                href = link.get("href", "")
                if href and "/dogs/" in href:
                    url = href
                    if not url.startswith("http"):
                        url = BASE_URL + url

            # Photo URL (site uses relative /_next/image paths)
            photo_url = ""
            img = card.select_one("img")
            if img:
                src = img.get("src", "") or ""
                if src.startswith("/"):
                    photo_url = BASE_URL + src
                else:
                    photo_url = src

            if name and url:
                cards.append(
                    {
                        "name": name,
                        "gender": gender,
                        "age": age,
                        "status": status,
                        "url": url,
                        "photo_url": photo_url,
                    }
                )

        return cards

    @staticmethod
    def _parse_detail_page(html: str) -> tuple[str, str]:
        """Extract breed and location from a detail page.

        Returns (breed, location).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Breed: first <p> after the <h1> heading
        breed = ""
        h1 = soup.select_one("h1.chakra-heading")
        if h1:
            breed_p = h1.find_next("p")
            if breed_p:
                breed = breed_p.get_text(strip=True)

        # Location: parse description for origin info.
        # Strip newlines to avoid split lines in the cache file.
        location = LOCATION
        desc_div = soup.select_one(".css-wdemyf")
        if desc_div:
            desc = desc_div.get_text().replace("\n", " ").replace("\r", " ")
            # Check for international origin
            rescued_match = re.search(r"Rescued from\s+(\w+(?:\s+\w+)?)", desc)
            if rescued_match:
                country = rescued_match.group(1).strip()
                # Only annotate if non-UK origin
                if country.lower() not in ("uk", "england", "scotland", "wales",
                                           "northern ireland", "united kingdom"):
                    location = f"{LOCATION} (origin: {country})"

        return breed, location

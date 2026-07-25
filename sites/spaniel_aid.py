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

        for card in soup.select(".dog-card-style .repeater-item"):
            content = card.select_one(".content-wrapper")
            if not content:
                continue

            # Extract fields using nth-of-type on .dynamic divs
            dynamic_divs = content.select("div.dynamic")
            if len(dynamic_divs) < 4:
                continue

            breed = dynamic_divs[0].get_text(strip=True)
            age = dynamic_divs[1].get_text(strip=True)
            location = dynamic_divs[2].get_text(strip=True)
            gender = dynamic_divs[3].get_text(strip=True)

            # Post-scrape filtering: female + age <= 12 months
            if gender != "Female":
                continue
            age_months = self._parse_age_months(age)
            if age_months > 12:
                continue

            # Name and status from heading
            heading_text = self._text(content, "h4.dynamic")
            name = self._clean_name(heading_text)
            status = self._extract_status(heading_text)

            # URL from the enclosing <a> tag
            link = card.select_one("a[href]")
            if not link:
                continue
            url = link.get("href", "")

            # Photo URL
            photo_url = self._photo_url(card)

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

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _parse_age_months(age_str: str) -> int:
        """Parse an age string like '15 months' or '4 years 6 months' into total months."""
        months = 0
        year_match = re.search(r"(\d+)\s*years?", age_str)
        if year_match:
            months += int(year_match.group(1)) * 12
        month_match = re.search(r"(\d+)\s*months?", age_str)
        if month_match:
            months += int(month_match.group(1))
        return months

    @staticmethod
    def _clean_name(heading: str) -> str:
        """Strip the SA reference number and status suffix from a heading.

        'Milo SA5125' -> 'Milo'
        'Daisy SA5592 \u2013 Reserved while we review...' -> 'Daisy'
        """
        # Remove status suffix (after en-dash)
        if " \u2013 " in heading:
            heading = heading.split(" \u2013 ")[0]
        # Remove SA reference number
        heading = re.sub(r"\s+SA\d+", "", heading)
        return heading.strip()

    @staticmethod
    def _extract_status(heading: str) -> str:
        """Extract adoption status from the heading text.

        Returns 'Reserved while we review', 'Foster View To Adopt', or 'Available'.
        """
        if "Reserved while we review" in heading:
            return "Reserved while we review"
        if "Foster View To Adopt" in heading:
            return "Foster View To Adopt"
        return "Available"

    @staticmethod
    def _photo_url(card) -> str:
        """Extract the dog photo URL from the card's image."""
        img = card.select_one("figure.image-wrapper img")
        if img:
            return img.get("src", "") or ""
        return ""

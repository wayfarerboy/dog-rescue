"""Raystede Centre for Animal Welfare site checker.

Uses the JSON API at /anilog.php since the listing page is JS-rendered.
"""

from __future__ import annotations

import json
import re

import requests

from .base import Dog, SiteChecker

LISTING_URL = "https://www.raystede.org/adopt/dogs/"
API_URL = "https://www.raystede.org/anilog.php?type=list"
IMAGE_BASE = "https://www.raystede.org/anilog-images"


class RaystedeChecker(SiteChecker):
    site_name = "Raystede"
    data_file = "raystede.txt"

    def fetch(self) -> str:
        """Fetch the JSON API listing all animals."""
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse the JSON API response into Dog objects.

        Filters:
        - Species must be "Dog"
        - Skip dogs marked "Home Found" (reserved=1)
        - Female only (including pairs with "Male & Female")
        - Age ≤ 12 months
        """
        data = json.loads(raw)
        if data.get("status") != "success":
            return []

        dogs: list[Dog] = []
        for animal in data.get("data", []):
            if animal.get("species") != "Dog":
                continue

            # Skip "Home Found" dogs
            if animal.get("reserved"):
                continue

            name = animal.get("name", "")
            gender = animal.get("gender", "")
            breed = animal.get("breed", "")
            age = animal.get("age", "")
            animalref = animal.get("animalref", "")
            image = animal.get("image", "")

            # Post-scrape filtering: female only + age ≤ 12 months
            if "Female" not in gender:
                continue
            age_months = self._parse_age_months(age)
            if age_months > 12:
                continue

            # Status
            status = (
                "Meeting a Match" if animal.get("is_meeting") else "Available"
            )

            # Construct unique URL from animal ref
            url = f"{LISTING_URL}?animal={animalref}"

            # Photo URL
            photo_url = f"{IMAGE_BASE}/{image}.jpg" if image else ""

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status=status,
                    photo_url=photo_url,
                )
            )

        return dogs

    @staticmethod
    def _parse_age_months(age_str: str) -> int:
        """Parse an age string like '11 months', '2 years 6 months', or
        '5 years and 6 months' into total months."""
        if not age_str:
            return 0
        months = 0
        year_match = re.search(r"(\d+)\s*years?", age_str)
        if year_match:
            months += int(year_match.group(1)) * 12
        month_match = re.search(r"(\d+)\s*months?", age_str)
        if month_match:
            months += int(month_match.group(1))
        return months

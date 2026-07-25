"""Many Tears Rescue site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class ManyTearsChecker(SiteChecker):
    site_name = "Many Tears Rescue"
    data_file = "many-tears.txt"

    URL = (
        "https://www.manytearsrescue.org/adopt/dogs/"
        "?search=&gender=female&postcode=&distance="
        "&age_range_group=six_months_and_under&size="
    )

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select("a.animal-card"):
            href = card.get("href", "")
            if not href:
                continue

            name = self._text(card, "h3")
            breed = self._text(card, ".icon.breed")
            age = self._text(card, ".icon.age")
            sex = self._text(card, ".icon.sex")
            location = self._text(card, ".icon.location")
            photo_url = self._image_url(card)

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=sex,
                    breed=breed,
                    url=f"https://www.manytearsrescue.org{href}",
                    status="",
                    location=location,
                    photo_url=photo_url,
                )
            )

        return dogs

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _image_url(card) -> str:
        """Extract image URL from background-image style on .animal-card__image."""
        img_div = card.select_one(".animal-card__image")
        if not img_div:
            return ""
        style = img_div.get("style", "")
        match = re.search(r"url\('([^']+)'\)", style)
        if match:
            path = match.group(1)
            return f"https://www.manytearsrescue.org{path}"
        return ""

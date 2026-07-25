"""Jerry Green Dog Rescue site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

# Map of location slugs to display names
LOCATIONS: dict[str, str] = {
    "east-yorkshire": "East Yorkshire",
    "north-lincolnshire": "North Lincolnshire",
    "nottinghamshire": "Nottinghamshire",
    "south-lincolnshire": "South Lincolnshire",
}


class JerryGreenChecker(SiteChecker):
    site_name = "Jerry Green Dog Rescue"
    data_file = "jerry-green.txt"

    BASE_URL = "https://www.jerrygreendogs.org.uk/dogs/"

    def __init__(self, data_dir: str, location: str = "") -> None:
        super().__init__(data_dir)
        self._location = location

    def _build_url(self, location_slug: str) -> str:
        return f"{self.BASE_URL}?location={location_slug}"

    def fetch(self) -> str:
        """Fetch all dogs across all four centres."""
        results: list[str] = []
        for slug in LOCATIONS:
            url = self._build_url(slug)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            results.append(resp.text)
        # Join with a marker so parse can still process them.
        return "\n<!-- JG_LOCATION_SPLIT -->\n".join(results)

    def parse(self, raw: str) -> list[Dog]:
        dogs: list[Dog] = []

        # Determine location from a location attribute if set on the checker
        chunks = raw.split("<!-- JG_LOCATION_SPLIT -->")

        # If we got combined HTML (multiple centres), process each chunk
        # with its corresponding location. Otherwise use the raw HTML directly
        # (for testing with a single location override).
        if len(chunks) > 1:
            location_slugs = list(LOCATIONS.keys())
            for i, chunk in enumerate(chunks):
                if i < len(location_slugs):
                    loc = LOCATIONS[location_slugs[i]]
                    dogs.extend(self._parse_html(chunk, loc))
        else:
            loc = LOCATIONS.get(self._location, "")
            dogs.extend(self._parse_html(raw, loc))

        return dogs

    def _parse_html(self, html: str, location: str) -> list[Dog]:
        """Parse dogs from a single page's HTML."""
        soup = BeautifulSoup(html, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select(".card.dog"):
            name = self._text(card, ".card__title span")
            breed = self._text(card, ".details .breed")
            age = self._text(card, ".details .age")
            sex = self._text(card, ".details .sex")
            status = self._status(card)
            size = self._size(card)
            link = self._profile_link(card)
            photo_url = self._photo_url(card)

            # Post-scrape filtering
            if sex != "Female":
                continue
            age_months = self._parse_age_months(age)
            if age_months > 12:
                continue
            if size not in ("Small", "Medium", ""):
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=sex,
                    breed=breed,
                    url=link,
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
    def _status(card) -> str:
        """Extract status from the sticker span."""
        el = card.select_one(".sticker span")
        if not el:
            return ""
        text = el.get_text(strip=True)
        if "Reserved" in text:
            return "Reserved"
        if "Available" in text:
            return "Available"
        return text

    @staticmethod
    def _size(card) -> str:
        """Extract size tag from the attributes tick-list."""
        for li in card.select(".card__attributes .tick-list li"):
            text = li.get_text(strip=True)
            if "small breed" in text.lower():
                return "Small"
            if "medium breed" in text.lower():
                return "Medium"
            if "large breed" in text.lower():
                return "Large"
        return ""

    def _profile_link(self, card) -> str:
        el = card.select_one("a.block-link")
        if el:
            return el.get("href", "")
        return ""

    @staticmethod
    def _photo_url(card) -> str:
        """Extract first image URL from the card."""
        img = card.select_one(".card__image img.image-0")
        if img:
            return img.get("src", "")
        # Fallback: any img in card__image
        img = card.select_one(".card__image img")
        if img:
            return img.get("src", "")
        return ""

    @staticmethod
    def _parse_age_months(age_text: str) -> int:
        """Parse age string like '0 years 1 months' into total months."""
        if not age_text:
            return 0
        years_match = re.search(r"(\d+)\s*years?", age_text)
        months_match = re.search(r"(\d+)\s*months?", age_text)
        years = int(years_match.group(1)) if years_match else 0
        months = int(months_match.group(1)) if months_match else 0
        return years * 12 + months

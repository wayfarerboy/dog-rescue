"""Pro Dogs Direct site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class ProDogsDirectChecker(SiteChecker):
    site_name = "Pro Dogs Direct"
    data_file = "pro-dogs-direct.txt"

    URL = "https://prodogsdirect.org.uk/dogs-for-adoption/"

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for article in soup.select("article.post"):
            # Skip the sticky intro post (not a dog listing)
            if "category-not-ready-for-adoption" in article.get("class", []):
                continue

            name = self._parse_name(article)
            age, gender = self._parse_age_gender(article)
            breed = self._parse_breed(article)
            location = self._parse_location(article)
            status = self._parse_status(article)
            url = self._profile_url(article)
            photo_url = self._photo_url(article)

            if not name or not url:
                continue

            # Filter out dogs that are not available for adoption
            if status in ("Applications Closed", "Reserved", "Rehomed"):
                continue

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

    def _parse_name(self, article) -> str:
        """Extract name from entry-title.

        Title format: "Name - Breed" or "Name - APPLICATIONS CLOSED" or "Name - RESERVED"
        Returns just the name part before " - ".
        """
        title = self._text(article, ".entry-title")
        if not title:
            return ""
        # Split on " - " or " \u2013 " and take the first part
        return re.split(r"\s[\u2013-]\s", title)[0].strip()

    def _parse_age_gender(self, article) -> tuple[str, str]:
        """Extract age and gender from the summary's age paragraph.

        Age paragraph contains patterns like:
          "6 Year Old Female", "12 Week Old Male", "2.5 Year Old Female",
          "8 Month OldMale" (missing space), "6 & 10 Year Old Females" (pair).
        Returns (age_text, gender).
        """
        summary = article.select_one(".entry-summary")
        if not summary:
            return "", ""

        for p in summary.select("p"):
            text = p.get_text(strip=True)
            # Look for age pattern: <number> <Week|Month|Year> Old <Gender>
            # Handle missing space before gender (OldMale) and plural (Females)
            m = re.match(
                r"(\d+(?:\.\d+)?(?:\s*&\s*\d+)?)\s+"
                r"(Week|Month|Year)\s+Old\s*"
                r"(Female|Male)s?",
                text,
                re.IGNORECASE,
            )
            if m:
                age = f"{m.group(1)} {m.group(2).capitalize()} Old"
                gender = m.group(3).capitalize()
                return age, gender

        return "", ""

    def _parse_breed(self, article) -> str:
        """Extract breed from summary paragraphs.

        Skip the name paragraph, age paragraph, and fostered-in paragraph.
        The remaining paragraph is the breed (may or may not have <strong>).
        """
        summary = article.select_one(".entry-summary")
        if not summary:
            return ""

        name = self._parse_name(article)

        for p in summary.select("p"):
            # Get text from <strong> if present, otherwise use the full paragraph
            strong = p.select_one("strong") or p.select_one("b")
            text = strong.get_text(strip=True) if strong else p.get_text(strip=True)

            # Skip age paragraph
            if re.search(r"(Week|Month|Year)\s+Old", text, re.IGNORECASE):
                continue
            # Skip location paragraph
            if re.search(r"Fostered\s+in", text, re.IGNORECASE):
                continue
            # Skip the name paragraph (first paragraph is the dog's name)
            if text == name:
                continue
            # Skip "Read more" links
            if text.lower() in ("read more", "read more →"):
                continue

            return text

        return ""

    def _parse_location(self, article) -> str:
        """Extract foster location from summary.

        Pattern: "Fostered in LOCATION" or "Fostered in  LOCATION"
        """
        summary = article.select_one(".entry-summary")
        if not summary:
            return ""

        for p in summary.select("p"):
            text = p.get_text(strip=True)
            # Normalise non-breaking spaces
            text = text.replace("\xa0", " ")
            m = re.search(r"Fostered\s+in\s*(.+)", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        return ""

    def _parse_status(self, article) -> str:
        """Derive status from category classes and title keywords."""
        classes = article.get("class", [])
        title = self._text(article, ".entry-title")

        if "category-applications-closed" in classes:
            return "Applications Closed"
        if "APPLICATIONS CLOSED" in title.upper():
            return "Applications Closed"
        if "RESERVED" in title.upper():
            return "Reserved"
        if "REHOMED" in title.upper():
            return "Rehomed"

        return "Available"

    def _profile_url(self, article) -> str:
        """Extract the profile URL from the entry-title link."""
        a = article.select_one(".entry-title a")
        if a:
            return a.get("href", "")
        return ""

    @staticmethod
    def _photo_url(article) -> str:
        """Extract photo URL from the entry-thumb image."""
        img = article.select_one(".entry-thumb img")
        if img:
            return img.get("src", "")
        return ""

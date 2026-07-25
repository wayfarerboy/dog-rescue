"""Pro Dogs Direct site checker."""

import re

import requests
from bs4 import BeautifulSoup, Tag

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

        for article in soup.select("article"):
            # Skip sticky (intro) post
            if "sticky" in article.get("class", []):
                continue

            # Skip rehomed dogs
            if "category-rehomed" in article.get("class", []):
                continue

            name = self._extract_name(article)
            link = self._profile_link(article)
            age_gender = self._field_text(article, 1)
            breed = self._field_text(article, 2)
            location_raw = self._field_text(article, 3)
            location = self._clean_location(location_raw)
            status = self._status(article)

            if not link:
                continue

            age, gender = self._parse_age_gender(age_gender)

            # Filter: female only
            if gender != "Female":
                continue

            # Filter: age_months <= 12
            age_months = self._age_to_months(age)
            if age_months > 12:
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
    def _extract_name(article: Tag) -> str:
        """Extract name from entry-title link text (before dash separator if present)."""
        el = article.select_one("h2.entry-title a")
        if not el:
            return ""
        text = el.get_text(strip=True)
        # Name is before a dash separator (en dash, em dash, or spaced hyphen)
        # e.g. "Luna -- Cavalier King Charles Spaniel" -> "Luna"
        m = re.match(r"(.+?)\s+[\u2013\u2014-]\s+.+", text)
        if m:
            return m.group(1).strip()
        return text

    @staticmethod
    def _profile_link(article: Tag) -> str:
        """Extract profile URL from entry-title link."""
        el = article.select_one("h2.entry-title a")
        if el:
            return el.get("href", "")
        return ""

    @staticmethod
    def _field_text(article: Tag, index: int) -> str:
        """Extract text from the Nth <p> element in entry-summary."""
        summary = article.select_one(".entry-summary")
        if not summary:
            return ""
        paragraphs = summary.select("p")
        if index >= len(paragraphs):
            return ""
        return paragraphs[index].get_text(strip=True)

    @staticmethod
    def _clean_location(raw: str) -> str:
        """Strip 'Fostered in ' prefix from location text."""
        if raw.lower().startswith("fostered in "):
            return raw[len("fostered in "):].strip()
        return raw

    @staticmethod
    def _status(article: Tag) -> str:
        """Determine status from category class."""
        classes = article.get("class", [])
        if "category-reserved-dogs" in classes:
            return "Reserved"
        if "category-applications-closed" in classes:
            return "Applications Closed"
        if "category-rehomed" in classes:
            return "Rehomed"
        if "category-not-ready-for-adoption" in classes:
            return "Not Ready"
        if "category-dogs" in classes:
            return "Available"
        return ""

    @staticmethod
    def _parse_age_gender(text: str) -> tuple[str, str]:
        """Parse age and gender from text like '12 Week Old Male' or '6 Year Old Female'.

        Returns (age_str, gender_str). Gender is detected from trailing
        'Male' or 'Female'. If not parseable, returns (text, '').
        """
        if not text:
            return "", ""

        for gender_word in ("Female", "Male"):
            if text.endswith(gender_word):
                age_part = text[: -len(gender_word)].rstrip()
                return age_part, gender_word

        return text, ""

    @staticmethod
    def _age_to_months(age_str: str) -> float:
        """Convert an age string to months (float). Returns 0 for unparseable."""
        if not age_str:
            return 0.0

        # Match: number then unit
        m = re.match(r"([\d.]+)\s+([Ww]eeks?|[Mm]onths?|[Yy]ears?)\b", age_str)
        if not m:
            return 0.0

        value = float(m.group(1))
        unit = m.group(2).lower()

        if unit.startswith("week"):
            return value * (7.0 / 30.4375)  # weeks to months
        elif unit.startswith("month"):
            return value
        elif unit.startswith("year"):
            return value * 12.0

        return 0.0

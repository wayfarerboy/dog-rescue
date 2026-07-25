"""RSPCA Leeds & Wakefield site checker."""

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker


class RSPCALeedsChecker(SiteChecker):
    site_name = "RSPCA Leeds & Wakefield"
    data_file = "rspca-leeds.txt"

    LISTING_URL = "https://www.rspcaleedsandwakefield.org.uk/dogs/"

    def fetch(self) -> str:
        """Fetch the listing page HTML."""
        resp = requests.get(self.LISTING_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _fetch_detail(self, url: str) -> str:
        """Fetch a detail page HTML. Overridable for testing."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dogs: list[Dog] = []

        for card in soup.select(".wpgb-card"):
            name = self._text(card, ".wpgb-block-3")
            age = self._text(card, ".wpgb-block-1")
            gender = self._text(card, ".wpgb-block-2")
            link = self._detail_link(card)
            photo_url = self._photo_url(card)

            if not link:
                continue

            # Normalize gender: listing cards have lowercase "female"/"male"
            gender_display = gender.capitalize() if gender else ""

            # Quick filter: skip males early
            if gender_display != "Female":
                continue

            # Quick filter: skip if listing age clearly >12 months
            listing_months = self._parse_age_months(age)
            if listing_months > 12:
                # Listing says >12 months but could be wrong — still skip
                # since we only care about puppies
                continue

            # Fetch detail page for breed, age, status, and location
            breed = ""
            detail_age = ""
            status = ""
            location = ""
            try:
                detail_html = self._fetch_detail(link)
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                breed = self._detail_field(detail_soup, "Breed:")
                detail_age = self._detail_field(detail_soup, "Age:")
                detail_gender = self._detail_field(detail_soup, "Gender:")
                status = self._detail_field(detail_soup, "Status:")
                location = self._detail_field(detail_soup, "Location:")
                if detail_gender:
                    gender_display = detail_gender
            except Exception:
                # If detail fetch fails, use listing data only
                pass

            # Use detail age if available (more precise), otherwise listing age
            final_age = detail_age if detail_age else age
            final_months = self._parse_age_months(final_age)

            # Filter: only females under 1 year (≤12 months)
            if gender_display != "Female":
                continue
            if final_months > 12:
                continue

            dogs.append(
                Dog(
                    name=name,
                    age=final_age,
                    gender=gender_display,
                    breed=breed,
                    url=link,
                    photo_url=photo_url,
                    status=status,
                    location=location,
                )
            )

        return dogs

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _text(soup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _detail_link(card) -> str:
        """Extract the detail page URL from a listing card."""
        link = card.select_one(".wpgb-card-layer-link")
        if link:
            return link.get("href", "")
        # Fallback: link in card body
        link = card.select_one(".wpgb-card-body a[href]")
        if link:
            return link.get("href", "")
        return ""

    @staticmethod
    def _photo_url(card) -> str:
        """Extract photo URL from listing card. Handles lazy-loaded images."""
        # Primary: data-wpgb-src on the lazy-load div
        lazy = card.select_one(".wpgb-lazy-load")
        if lazy:
            src = lazy.get("data-wpgb-src", "")
            if src:
                return src
        # Fallback: noscript img
        noscript_img = card.select_one("noscript img.wpgb-noscript-img")
        if noscript_img:
            return noscript_img.get("src", "")
        # Fallback: any img in card media
        img = card.select_one(".wpgb-card-media-thumbnail img")
        if img:
            return img.get("src", "")
        return ""

    @staticmethod
    def _detail_field(soup, label: str) -> str:
        """Extract a field value from the detail page's about-me table."""
        th = soup.find("th", string=lambda t: t and label in t)
        if th:
            td = th.find_next("td")
            if td:
                return td.get_text(strip=True)
        return ""

    @staticmethod
    def _parse_age_months(age_text: str) -> int:
        """Parse age string like '4 years', '1 year 7 months' into total months."""
        if not age_text:
            return 0
        years_match = re.search(r"(\d+)\s*years?", age_text)
        months_match = re.search(r"(\d+)\s*months?", age_text)
        years = int(years_match.group(1)) if years_match else 0
        months = int(months_match.group(1)) if months_match else 0
        return years * 12 + months

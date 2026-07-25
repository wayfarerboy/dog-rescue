"""East Midlands Dog Rescue site checker.

WooCommerce-based site. Dogs are listed as products on a paginated
listing page.  Breed, age, and gender are scraped from the free-text
description on each dog's detail page.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

# Patterns in the description that suggest a female dog.
_FEMALE_WORDS = re.compile(
    r"\b(girl|she|her|hers|lady|ladies|lass|female)\b", re.IGNORECASE
)
# Patterns that suggest a male dog.
_MALE_WORDS = re.compile(
    r"\b(boy|he|him|his|lad|gent|male)\b", re.IGNORECASE
)

# Age pattern: optional "approx", digits (possibly with /), then a unit.
# "2 years", "5 years old", "13 months old", "approx 5/6 years old"
_AGE_PATTERN = re.compile(
    r"(?:approx[.\s]+)?(\d+(?:/\d+)?)\s*(years?\s*old|months?\s*old|years?|months?)",
    re.IGNORECASE,
)


class EastMidlandsDogRescueChecker(SiteChecker):
    site_name = "East Midlands Dog Rescue"
    data_file = "east-midlands-dog-rescue.txt"

    BASE_URL = "https://www.eastmidlandsdogrescue.org/needing-a-home/"
    LOCATION = "Enderby, Leicester"

    # ── public API ──────────────────────────────────────────────────

    def fetch(self) -> str:
        """Fetch all listing pages.  Returns concatenated HTML."""
        pages: list[str] = []
        page = 1
        while True:
            if page == 1:
                url = self.BASE_URL
            else:
                url = f"{self.BASE_URL}?product-page={page}"
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            products = soup.select("li.product")
            if not products:
                break
            pages.append(resp.text)
            page += 1
        return "\n<!-- EMDR_PAGE_SPLIT -->\n".join(pages)

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing pages into Dog stubs (no breed/age/gender yet)."""
        dogs: list[Dog] = []

        for chunk in raw.split("<!-- EMDR_PAGE_SPLIT -->"):
            soup = BeautifulSoup(chunk, "html.parser")
            for card in soup.select("li.product"):
                link_el = card.select_one("a.woocommerce-LoopProduct-link")
                if not link_el:
                    continue

                url = link_el.get("href", "")
                if not url:
                    continue

                # Name from the h2 title
                title_el = card.select_one("h2.woocommerce-loop-product__title")
                raw_name = title_el.get_text(strip=True) if title_el else ""

                # Detect reserved from the title (handles both "(Reserved)" and "Reserved)")
                reserved = "reserved)" in raw_name.lower()

                # Strip "(Reserved)" / "Reserved)" and heart/suffix from name
                name = re.sub(r"\s*\(?Reserved\)\s*.*$", "", raw_name, flags=re.IGNORECASE).strip()

                # Thumbnail from listing card
                img = card.select_one("img.attachment-woocommerce_thumbnail")
                photo_url = img.get("src", "") if img else ""

                dogs.append(
                    Dog(
                        name=name,
                        age="",
                        gender="",
                        breed="",
                        url=url,
                        status="Reserved" if reserved else "Available",
                        location=self.LOCATION,
                        photo_url=photo_url,
                    )
                )

        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, scrape detail pages, filter, and return new dogs.

        Post-scrape filtering: female only, age <= 12 months.
        Reserved dogs are already excluded by parse().
        """
        raw = self.fetch()
        all_dogs = self.parse(raw)

        # Separate reserved from available
        available = [d for d in all_dogs if d.status != "Reserved"]

        # Scrape detail pages for breed, age, gender
        for dog in available:
            try:
                detail_html = self._fetch_detail(dog.url)
                detail = self._parse_detail(detail_html, dog.name)
                if detail.get("age"):
                    dog.age = detail["age"]
                if detail.get("breed"):
                    dog.breed = detail["breed"]
                if detail.get("gender"):
                    dog.gender = detail["gender"]
                # Use full-size image from detail page if available
                if detail.get("photo_url") and not dog.photo_url:
                    dog.photo_url = detail["photo_url"]
            except Exception:
                pass

        # Post-scrape filtering
        filtered = [d for d in available if d.gender == "Female" and self._age_months(d.age) <= 12]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new

    # ── internal helpers ────────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        """Fetch a detail page."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, name: str) -> dict[str, str]:
        """Parse breed, age, gender, and photo_url from a detail page.

        The description tab contains free text like:
            "Wire haired Dacshund (Teckel) 2 years A stunning girl..."
            "Crossbreed 5 years A very deserving lad..."
        """
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, str] = {}

        # Full-size image from product gallery
        img = soup.select_one(".woocommerce-product-gallery__image img")
        if img:
            src = img.get("src", "")
            # Remove WooCommerce size suffix to get original
            result["photo_url"] = re.sub(r"-\d+x\d+(?=\.(jpeg|jpg|png|webp))", "", src)

        # Breed + age from description tab
        desc_el = soup.select_one(".woocommerce-Tabs-panel--description")
        if desc_el:
            desc = desc_el.get_text(" ", strip=True)
            # Drop leading "Description" word
            desc = re.sub(r"^Description\s+", "", desc)

            breed, age = _split_breed_age(desc)
            if breed:
                result["breed"] = breed
            if age:
                result["age"] = age

            # Gender from description text
            gender = _infer_gender(desc, name)
            if gender:
                result["gender"] = gender

        return result

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable."""
        age_str = age_str.lower().strip()
        if not age_str:
            return 999
        year_match = re.search(r"(\d+)\s*years?\b", age_str)
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if not year_match and not month_match:
            return 999
        years = int(year_match.group(1)) if year_match else 0
        months = int(month_match.group(1)) if month_match else 0
        return years * 12 + months


def _split_breed_age(text: str) -> tuple[str, str]:
    """Split the first sentence into breed and age.

    "Wire haired Dacshund (Teckel) 2 years ..." → ("Wire haired Dacshund (Teckel)", "2 years")
    "Crossbreed (labradoodle size) 2 years old ..." → ("Crossbreed (labradoodle size)", "2 years old")
    "Chihuahua (approx 5 years old ) ..." → ("Chihuahua", "approx 5 years old")
    """
    m = _AGE_PATTERN.search(text)
    if not m:
        return text.strip(), ""

    age_start = m.start()
    age_text = m.group(0).strip()

    # Breed is everything before the age, trimmed
    breed = text[:age_start].strip()
    # Remove trailing parens/dashes/commas and orphaned open-paren
    breed = re.sub(r"[\s,;\-—]+$", "", breed)
    breed = re.sub(r"\s*\($", "", breed)
    # Remove leading "(approx " from age display
    age_text = re.sub(r"^approx[.\s]+", "approx. ", age_text)

    # Normalize age: ensure space before "years"/"months"
    # "5years old" → "5 years old"
    age_text = re.sub(r"(\d)(years?|months?)", r"\1 \2", age_text)
    age_text = re.sub(r"\s+", " ", age_text).strip()

    return breed, age_text


def _infer_gender(text: str, name: str) -> str:
    """Infer gender from description text and name.

    Counts weighted female vs male word hits. Ties break female.
    """
    combined = f"{name} {text}"
    female_count = len(_FEMALE_WORDS.findall(combined))
    male_count = len(_MALE_WORDS.findall(combined))

    # "lad" is ambiguous — it appears in both lists. In dog rescue contexts
    # "lad" almost always means male, so give it priority when no other male
    # signals exist.
    if female_count == 0 and male_count == 0:
        return ""

    if female_count >= male_count:
        return "Female"
    return "Male"

"""Happy Staffie Rescue site checker.

Wix Thunderbolt SPA — dog images and names are rendered client-side
in a Wix Pro Gallery (Masonry) iframe.  Individual detail pages exist
at https://www.happystaffie.co.uk/{name-lowercase} with full profile text.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .base import Dog, SiteChecker

LOCATION = "Unit 3, 4 Lisle Ave, Kidderminster DY11 7DL"
BASE_URL = "https://www.happystaffie.co.uk"

# Patterns for gender inference (borrowed from east_midlands.py).
_FEMALE_WORDS = re.compile(
    r"\b(girl|she|her|hers|lady|ladies|lass|female)\b", re.IGNORECASE
)
_MALE_WORDS = re.compile(
    r"\b(boy|he|him|his|lad|gent|male)\b", re.IGNORECASE
)

# Age pattern: "10 years and 9 months", "7-year-old", "2-3 years", etc.
_AGE_MONTHS = re.compile(r"(\d+)\s*months?\s*old", re.IGNORECASE)
_AGE_RANGE = re.compile(r"(\d+)[-/](\d+)\s*years?", re.IGNORECASE)



class HappyStaffieChecker(SiteChecker):
    site_name = "Happy Staffie Rescue"
    data_file = "happy-staffie.txt"

    LISTING_URL = "https://www.happystaffie.co.uk/adopt"

    def fetch(self) -> str:
        """Render the Wix SPA with Playwright and return the gallery iframe HTML.

        Returns the inner HTML of the Masonry gallery iframe
        (comp-l2ptkz4y), which contains dog names, statuses, and photos.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(self.LISTING_URL, timeout=30000,
                          wait_until="domcontentloaded")
                page.wait_for_timeout(10000)

                for frame in page.frames:
                    if "comp-l2ptkz4y" in frame.url:
                        try:
                            frame.wait_for_selector(".item", timeout=5000)
                        except Exception:
                            pass
                        html = frame.content()
                        browser.close()
                        return html

                browser.close()
                return ""
            except Exception:
                browser.close()
                raise

    def parse(self, raw: str) -> list[Dog]:
        """Parse gallery items into Dog objects with name, status, photo.

        Each .item div contains:
          <h3 class="title">Dog Name</h3>
          <div class="desc">Click for more information / RESERVED / etc.</div>
          <img src="..."/>

        Non-dog items (donation posters, etc.) are identified by
        their desc text not matching known dog status patterns.
        """
        if not raw:
            return []

        soup = BeautifulSoup(raw, "html.parser")

        dogs: list[Dog] = []
        for item in soup.select(".item"):
            # Name from h3.title
            title_el = item.select_one("h3.title")
            if not title_el:
                continue
            name = title_el.get_text(strip=True)

            # Status from div.desc
            desc_el = item.select_one("div.desc")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            # Photo from img
            img = item.find("img")
            photo_url = img.get("src", "") if img else ""

            # Determine status
            status = _parse_gallery_status(desc)
            if status is None:
                # Not a dog item
                continue

            # Dog names are short (1-2 words). Multi-word titles
            # like "We're part of a lottery" are non-dog gallery items.
            if len(name.split()) > 2 or len(name) > 25:
                continue

            dogs.append(
                Dog(
                    name=name,
                    age="",
                    gender="",
                    breed="",
                    url=f"{BASE_URL}/{name.lower()}",
                    status=status,
                    location=LOCATION,
                    photo_url=photo_url,
                )
            )

        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, scrape detail pages, filter, and return new dogs.

        Post-scrape filtering: female only, age <= 12 months.
        Reserved/Rehomed/Suspended dogs are filtered out of parse().
        """
        all_dogs = self._fetch_and_parse()

        # Only Available dogs get detail-page scraping
        available = [d for d in all_dogs if d.status == "Available"]

        if available:
            self._enrich_from_details(available)

        # Post-scrape filtering
        filtered = [
            d for d in available
            if d.gender == "Female" and self._age_months(d.age) <= 12
        ]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new

    def _fetch_and_parse(self) -> list[Dog]:
        """Fetch listing page and parse gallery items.

        Uses a single Playwright browser session for the gallery iframe.
        Overrideable for testing.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(self.LISTING_URL, timeout=30000,
                          wait_until="domcontentloaded")
                page.wait_for_timeout(10000)

                for frame in page.frames:
                    if "comp-l2ptkz4y" in frame.url:
                        try:
                            frame.wait_for_selector(".item", timeout=5000)
                        except Exception:
                            pass
                        gallery_html = frame.content()
                        browser.close()
                        return self.parse(gallery_html)

                browser.close()
                return []
            except Exception:
                browser.close()
                raise

    def _enrich_from_details(self, dogs: list[Dog]) -> None:
        """Scrape detail pages for breed, age, gender using Playwright.

        Shares one browser session across all detail fetches.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for dog in dogs:
                    try:
                        page = browser.new_page()
                        page.goto(dog.url, timeout=30000,
                                  wait_until="domcontentloaded")
                        page.wait_for_timeout(5000)
                        detail_html = page.content()
                        page.close()

                        detail = self._parse_detail(detail_html, dog.name)
                        if detail.get("age"):
                            dog.age = detail["age"]
                        if detail.get("breed"):
                            dog.breed = detail["breed"]
                        if detail.get("gender"):
                            dog.gender = detail["gender"]
                    except Exception:
                        pass
            finally:
                browser.close()

    # ── internal helpers ────────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        """Fetch a dog detail page using Playwright (Wix SPA).

        Overrideable for testing — tests inject static HTML.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                html = page.content()
                browser.close()
                return html
            except Exception:
                browser.close()
                raise

    @staticmethod
    def _parse_detail(html: str, name: str) -> dict[str, str]:
        """Extract breed, age, gender from a detail page.

        Detail pages have free-text descriptions like:
            "Sasha is a small staffie-cross, weighing just 11.2 kilos,
             and possibly crossed with something like a Jack Russell...
             born September 2015 making her 10 years and 9 months..."
        """
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        body_text = soup.get_text(separator="\n")

        result: dict[str, str] = {}

        # Breed: look for patterns in the description
        result["breed"] = _extract_breed(body_text, name)

        # Age
        result["age"] = _extract_age(body_text)

        # Gender
        result["gender"] = _infer_gender(body_text, name)

        return result

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable.

        For ranges like "2-3 years", uses the lower bound.
        """
        age_str = age_str.lower().strip()
        if not age_str:
            return 999

        # Try "X years [and] Y months" first — "and" is optional
        ym = re.search(r"(\d+)\s*years?\s*(?:and\s+|&\s+)?(\d+)\s*months?\b", age_str)
        if ym:
            return int(ym.group(1)) * 12 + int(ym.group(2))

        # Try "X months old" (standalone, no "year" in string)
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if month_match and "year" not in age_str:
            return int(month_match.group(1))

        # "X years" — for ranges like "2-3 years", capture the first digit
        year_match = re.search(r"(\d+)(?:\s*[-–]\s*\d+)?\s*years?\b", age_str)
        if year_match:
            return int(year_match.group(1)) * 12

        return 999


# ── gallery-parsing helpers ─────────────────────────────────────────


def _parse_gallery_status(desc: str) -> str | None:
    """Determine dog status from the gallery item's desc text.

    Returns None if the item doesn't look like a dog (e.g. donation poster).

    Dog items have desc text like:
    - "Click for more information" → Available
    - "RESERVED" → Reserved
    - "REHOMED" → Rehomed
    - "SUSPENDED due to..." → Suspended

    Non-dog items have variations like "Please click for more information"
    or "Click here for more information" — these are excluded.
    """
    if not desc:
        return None

    desc_upper = desc.upper().strip()

    # Status-only markers (appear on reserved/rehomed/suspended dogs)
    if desc_upper == "RESERVED":
        return "Reserved"
    if desc_upper == "REHOMED":
        return "Rehomed"
    if desc_upper.startswith("SUSPENDED"):
        return "Suspended"

    # Available dog marker — must be exactly this phrase
    if desc_upper == "CLICK FOR MORE INFORMATION":
        return "Available"

    # Non-dog: "Please click for more information", "Click here for ...", etc.
    return None


# ── detail-page helpers ─────────────────────────────────────────────


def _extract_breed(text: str, name: str) -> str:
    """Extract breed from detail page description text.

    Searches the dog's description — the text near the dog name heading,
    before the "The sort of home for" section.  Avoids matching
    "Staffie" from the rescue name in footer/adoption boilerplate.
    """
    # Extract the description portion.
    desc = _extract_description(text, name)
    desc_lower = desc.lower()

    # If description extraction failed, fall back to searching the
    # first ~2000 chars of text (before "The sort of home" section).
    if len(desc.strip()) < 20:
        desc_lower = text.lower()
        # Truncate at section headers to avoid rescue-name mentions.
        for header in ["the sort of home for", "if you adopt a dog from"]:
            idx = desc_lower.find(header)
            if idx > 0:
                desc_lower = desc_lower[:idx]

    # Look for explicit breed mentions (most specific first).
    breed_patterns = [
        (r"staffordshire\s+bull\s+terrier\s*cross", "Staffordshire Bull Terrier Cross"),
        (r"staffordshire\s+bull\s+terrier", "Staffordshire Bull Terrier"),
        (r"staffie[-\s]cross", "Staffie Cross"),
        (r"staffy[-\s]cross", "Staffy Cross"),
        (r"jack\s*russell\s*cross", "Jack Russell Cross"),
        (r"jack\s*russell", "Jack Russell"),
        (r"lurcher\s*cross", "Lurcher Cross"),
        (r"lurcher", "Lurcher"),
        (r"labrador\s*cross", "Labrador Cross"),
        (r"collie\s*cross", "Collie Cross"),
        (r"terrier\s*cross", "Terrier Cross"),
        (r"bulldog\s*cross", "Bulldog Cross"),
        (r"patterdale\s*cross", "Patterdale Cross"),
        (r"patterdale", "Patterdale"),
    ]

    for pattern, label in breed_patterns:
        if re.search(pattern, desc_lower):
            return label

    # Crossbreed / mixed breed
    if re.search(r"cross\s*breed|crossbreed", desc_lower):
        return "Crossbreed"

    # Only match bare "staffie"/"staffy" in the description section
    # (not from the rescue name in footer/adoption text).
    if re.search(r"\bstaffie\b", desc_lower):
        return "Staffie"
    if re.search(r"\bstaffy\b", desc_lower):
        return "Staffy"

    return "Mixed Breed"


def _extract_description(text: str, name: str) -> str:
    """Extract the dog description portion from a detail page.

    Returns the text between the dog name heading and the
    "The sort of home for" section header.

    Handles both page structures:
    - Sasha-style: "Sasha | Happy Staffie Rescue" title, body text follows
    - Luna-style: "Luna" title with description merged into a single line
    """
    name_lower = name.lower()
    lines = text.splitlines()

    # Strategy: find the line containing the description paragraph.
    # This is the line where the dog's name appears followed by
    # breed/age info (e.g. "is a", "crossbreed", "arrived for rehoming").
    desc_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        low = stripped.lower()
        # Skip boilerplate lines
        if any(skip in low for skip in [
            "top of page", "skip to main", "become a supporter",
            "donate here",
        ]):
            continue
        # Look for the description line: contains the name AND breed/age keywords
        if name_lower in low:
            if any(kw in low for kw in [
                "is a", "crossbreed", "cross-breed", "arrived for",
                "came to us", "staffie", "staffy", "terrier",
                "weighing", "weighs", "born",
            ]):
                desc_start = i
                break

    # Fallback: find any line with the name (not just a bare title)
    if desc_start < 0:
        for i, line in enumerate(lines):
            stripped = line.strip()
            low = stripped.lower()
            if any(skip in low for skip in [
                "top of page", "skip to main", "become a supporter",
                "donate here",
            ]):
                continue
            if name_lower in low and len(stripped) > len(name) + 5:
                desc_start = i
                break

    if desc_start < 0:
        return text

    # Find the end: section header after the description
    end = len(lines)
    for i in range(desc_start + 1, len(lines)):
        stripped = lines[i].strip().lower()
        if any(header in stripped for header in [
            "the sort of home for",
            "handling",
            "foster home",
            "walks",
            "play",
            "health",
            "viewings",
            "things to consider",
        ]):
            end = i
            break

    # Also collect the next few lines after desc_start (description
    # often spans multiple short lines on Wix).
    result_lines = []
    for i in range(desc_start, end):
        line = lines[i].strip()
        if line:
            result_lines.append(line)

    return "\n".join(result_lines)


def _extract_age(text: str) -> str:
    """Extract age from detail page description text.

    Patterns seen:
    - "born September 2015 making her 10 years and 9 months"
    - "a 7-year-old crossbreed"
    - "a 5-month-old terrier cross puppy"
    - "estimates Jack to be 2-3 years of age"
    - "Casey arrived for rehoming on 14th July 2026... he is around 2-3 years"
    - "Bella was born in March 2026 making her just a few months old"
    """
    text_lower = text.lower()

    # Case 1: "X years and Y months"
    ym = re.search(
        r"(\d+)\s*years?\s*(?:and|&)\s*(\d+)\s*months?",
        text_lower,
    )
    if ym:
        return f"{ym.group(1)} years {ym.group(2)} months"

    # Case 2: "X-year-old" or "X-month-old" (hyphenated)
    hy = re.search(r"(\d+)[-](?:year|month)[-]old", text_lower)
    if hy:
        unit = "years" if "year" in text_lower[hy.start():hy.end()] else "months"
        return f"{hy.group(1)} {unit} old"

    # Case 3: "X months old" (standalone)
    mo = _AGE_MONTHS.search(text_lower)
    if mo:
        return f"{mo.group(1)} months old"

    # Case 4: "X-Y years"
    yr = _AGE_RANGE.search(text_lower)
    if yr:
        return f"{yr.group(1)}-{yr.group(2)} years"

    # Case 5: "X years old" or "X years of age"
    ys = re.search(r"(\d+(?:\.\d+)?)\s*years?\s*(?:old|of\s*age)", text_lower)
    if ys:
        return f"{ys.group(1)} years old"

    # Case 6: "born [in] [Month] YYYY" — compute age from birth year
    born = re.search(r"born\s+(?:in\s+)?(?:\w+\s+)?(\d{4})", text_lower)
    if born:
        from datetime import datetime
        birth_year = int(born.group(1))
        current_year = datetime.now().year
        age = current_year - birth_year
        return f"{age} years old"

    return ""


def _infer_gender(text: str, name: str) -> str:
    """Infer gender from description text and name.

    Counts weighted female vs male word hits. Ties break female.
    """
    combined = f"{name} {text}"
    female_count = len(_FEMALE_WORDS.findall(combined))
    male_count = len(_MALE_WORDS.findall(combined))

    if female_count == 0 and male_count == 0:
        return ""

    if female_count >= male_count:
        return "Female"
    return "Male"

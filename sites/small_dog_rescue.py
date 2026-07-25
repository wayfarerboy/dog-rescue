"""Small Dog Rescue site checker.

Wix site — dogs are listed inline as rich-text blocks, one per dog.
Each dog entry: horizontal-line → image → rich-text "meet <Name> ..."
No individual detail pages — all info is in the listing description.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .base import Dog, SiteChecker

LOCATION = "Cliveglen, Landywood Lane, Great Wyrley, Walsall WS6 7AJ"
BASE_URL = "https://www.smalldogrescue.co.uk/dogs-for-rehoming"

# Gender inference patterns (shared with happy_staffie / east_midlands).
_FEMALE_WORDS = re.compile(
    r"\b(girl|she|her|hers|lady|ladies|lass|female)\b", re.IGNORECASE
)
_MALE_WORDS = re.compile(
    r"\b(boy|he|him|his|lad|gent|male)\b", re.IGNORECASE
)


class SmallDogRescueChecker(SiteChecker):
    site_name = "Small Dog Rescue"
    data_file = "small-dog-rescue.txt"

    def fetch(self) -> str:
        """Render the Wix SPA with Playwright and return page HTML."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(BASE_URL, timeout=30000,
                          wait_until="domcontentloaded")
                page.wait_for_timeout(10000)
                html = page.content()
                browser.close()
                return html
            except Exception:
                browser.close()
                raise

    def parse(self, raw: str) -> list[Dog]:
        """Parse rich-text dog entries from the listing page.

        Each dog is a .wixui-rich-text h4 starting with "meet <Name>".
        The image for each dog is in the nearest preceding .wixui-image.
        """
        if not raw:
            return []

        soup = BeautifulSoup(raw, "html.parser")

        # Collect all images for later association
        images: list[dict] = []
        for img_div in soup.select(".wixui-image"):
            img = img_div.find("img")
            if img:
                src = img.get("src", "")
                if src and "wixstatic" in src:
                    images.append({"element": img_div, "src": src})

        dogs: list[Dog] = []
        for rich_text in soup.select(".wixui-rich-text"):
            h4 = rich_text.find("h4")
            if not h4:
                continue

            text = h4.get_text(strip=True)
            if not text.lower().startswith("meet "):
                continue

            name = _extract_name(text)
            if not name:
                continue

            # Find nearest preceding image
            photo_url = _find_preceding_image(rich_text, images)

            # Parse details from description
            gender = _infer_gender(text, name)
            breed = _extract_breed(text)
            age = _extract_age(text)

            dog = Dog(
                name=name,
                age=age,
                gender=gender,
                breed=breed,
                url=BASE_URL,
                status="Available",
                location=LOCATION,
                photo_url=photo_url,
            )
            dogs.append(dog)

        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, filter, and return new dogs.

        Post-scrape filtering: female only, age <= 12 months.
        """
        raw = self.fetch()
        all_dogs = self.parse(raw)

        filtered = [
            d for d in all_dogs
            if d.gender == "Female" and self._age_months(d.age) <= 12
        ]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new

    @staticmethod
    def _age_months(age_str: str) -> int:
        """Parse an age string into total months. Returns 999 if unparseable.

        For ranges like "2-3 years", uses the lower bound.
        """
        age_str = age_str.lower().strip()
        if not age_str:
            return 999

        # "X years [and] Y months"
        ym = re.search(r"(\d+)\s*years?\s*(?:and\s+|&\s+)?(\d+)\s*months?\b", age_str)
        if ym:
            return int(ym.group(1)) * 12 + int(ym.group(2))

        # "X months old" (standalone, no "year")
        month_match = re.search(r"(\d+)\s*months?\b", age_str)
        if month_match and "year" not in age_str:
            return int(month_match.group(1))

        # "X years" — for ranges like "2-3 years", capture first digit
        year_match = re.search(r"(\d+)(?:\s*[-–]\s*\d+)?\s*years?\b", age_str)
        if year_match:
            return int(year_match.group(1)) * 12

        return 999


# ── parsing helpers ─────────────────────────────────────────────────


def _extract_name(text: str) -> str:
    """Extract the dog's name from a "meet <Name> ..." description.

    The name is the word immediately after "meet", capitalized.
    Returns empty string if the pattern doesn't match.
    """
    # Match "meet " followed by optional leading text then name
    m = re.match(r"meet\s+(\w[\w-]*)", text, re.IGNORECASE)
    if not m:
        return ""
    return m.group(1).capitalize()


def _find_preceding_image(rich_text_elem, images: list[dict]) -> str:
    """Find the nearest preceding .wixui-image element in DOM order.

    Returns the image src URL, or empty string if none found.
    """
    # Walk backwards through previous siblings / parent's previous siblings
    prev = rich_text_elem.find_previous_sibling()
    while prev:
        if "wixui-image" in prev.get("class", []):
            img = prev.find("img")
            if img:
                src = img.get("src", "")
                if src:
                    return src
        # Check inside this sibling for images
        for img_div in prev.select(".wixui-image"):
            img = img_div.find("img")
            if img:
                src = img.get("src", "")
                if src:
                    return src
        prev = prev.find_previous_sibling()

    # Fallback: use first image on page
    if images:
        return images[0]["src"]
    return ""


def _extract_breed(text: str) -> str:
    """Extract breed from dog description text.

    Searches for known breed patterns in the description.
    """
    text_lower = text.lower()

    breed_patterns = [
        (r"staffordshire\s+bull\s+terrier\s*cross", "Staffordshire Bull Terrier Cross"),
        (r"staffordshire\s+bull\s+terrier", "Staffordshire Bull Terrier"),
        (r"staffie[-\s]cross", "Staffie Cross"),
        (r"jack\s*russell\s*cross", "Jack Russell Cross"),
        (r"jack\s*russell", "Jack Russell"),
        (r"chihuahua\s*cross", "Chihuahua Cross"),
        (r"chihuahua", "Chihuahua"),
        (r"yorkshire\s*terrier\s*cross", "Yorkshire Terrier Cross"),
        (r"yorkshire\s*terrier", "Yorkshire Terrier"),
        (r"shih\s*tzu\s*cross", "Shih Tzu Cross"),
        (r"shih\s*tzu", "Shih Tzu"),
        (r"pug\s*cross", "Pug Cross"),
        (r"pug", "Pug"),
        (r"pomeranian\s*cross", "Pomeranian Cross"),
        (r"pomeranian", "Pomeranian"),
        (r"dachshund\s*cross", "Dachshund Cross"),
        (r"dachshund", "Dachshund"),
        (r"lurcher\s*cross", "Lurcher Cross"),
        (r"lurcher", "Lurcher"),
        (r"terrier\s*cross", "Terrier Cross"),
        (r"bichon\s*frise", "Bichon Frise"),
        (r"bichon", "Bichon"),
        (r"cavalier\s*king\s*charles", "Cavalier King Charles Spaniel"),
        (r"cocker\s*spaniel", "Cocker Spaniel"),
        (r"spaniel\s*cross", "Spaniel Cross"),
        (r"spaniel", "Spaniel"),
        (r"collie\s*cross", "Collie Cross"),
        (r"poodle\s*cross", "Poodle Cross"),
        (r"poodle", "Poodle"),
        (r"cross\s*breed|crossbreed", "Crossbreed"),
    ]

    for pattern, label in breed_patterns:
        if re.search(pattern, text_lower):
            return label

    # General cross
    if re.search(r"\bcross\b", text_lower):
        return "Crossbreed"

    return "Mixed Breed"


def _extract_age(text: str) -> str:
    """Extract age from dog description text.

    Patterns seen:
    - "X years old", "X years and Y months"
    - "X months old", "X-month-old"
    - "born [in] [Month] YYYY"
    - "approx X years"
    - "X-Y years"
    """
    text_lower = text.lower()

    # "X years and Y months"
    ym = re.search(
        r"(\d+)\s*years?\s*(?:and|&)\s*(\d+)\s*months?",
        text_lower,
    )
    if ym:
        return f"{ym.group(1)} years {ym.group(2)} months"

    # "X-year-old" or "X-month-old" (hyphenated)
    hy = re.search(r"(\d+)-(?:year|month)-old", text_lower)
    if hy:
        unit = "years" if "year" in text_lower[hy.start():hy.end()] else "months"
        return f"{hy.group(1)} {unit} old"

    # "X months old" (standalone)
    mo = re.search(r"(\d+)\s*months?\s*old", text_lower)
    if mo and "year" not in text_lower[:mo.start()].split()[-3:]:
        return f"{mo.group(1)} months old"

    # "X-Y years"
    yr = re.search(r"(\d+)[-/](\d+)\s*years?", text_lower)
    if yr:
        return f"{yr.group(1)}-{yr.group(2)} years"

    # "X years old" or "X years of age"
    ys = re.search(r"(\d+(?:\.\d+)?)\s*years?\s*(?:old|of\s*age)", text_lower)
    if ys:
        return f"{ys.group(1)} years old"

    # "born [in] [Month] YYYY" — compute age from birth year
    born = re.search(r"born\s+(?:in\s+)?(?:\w+\s+)?(\d{4})", text_lower)
    if born:
        from datetime import datetime
        birth_year = int(born.group(1))
        current_year = datetime.now().year
        age_val = current_year - birth_year
        return f"{age_val} years old"

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

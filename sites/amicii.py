"""Amicii Dog Rescue site checker.

UK dogs are listed on Pets4Homes (not the Amicii website itself).
The listing is a Next.js SSR page with structured JSON in __NEXT_DATA__.
Pagination: ?page=N (4 dogs/page, 6 pages, ~22 dogs).

Data is extracted from the __NEXT_DATA__ JSON:
- Name: generalInformation.title (emoji-stripped)
- Breed: always "Mixed Breed" in structured data
- Gender: from numberOfMales/numberOfFemales attributes
- Age: computed from dateOfBirth timestamp
- Photo: profileImage.originalImage (replace ##NAME## → image)
- URL: https://www.pets4homes.co.uk/adoption/dogs/{slug}/
- Location: locationV3.postalTown + adminRegion2
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import requests

from .base import Dog, SiteChecker

BASE_URL = "https://www.pets4homes.co.uk/user/amicii-dog-rescue-37d14269-6354-434b-a8b7-bf132ff1d329/"
DETAIL_BASE = "https://www.pets4homes.co.uk/adoption/dogs/"

# Strip emoji and decorative symbols: keep only letters, digits,
# spaces, hyphens, colons, and basic punctuation used in names.
_STRIP_RE = re.compile(r"[^\w\s:\-.'’!?]+")

# Breed value prefix to strip
_BREED_PREFIX_RE = re.compile(r"^pets\.dogs\.breed\.")


class AmiciiChecker(SiteChecker):
    site_name = "Amicii Dog Rescue"
    data_file = "amicii.txt"
    # Dogs are in various UK foster locations; bypass distance check for HQ
    bypass_distance_filter = True

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
    }

    def fetch(self) -> str:
        """Fetch all pages from the Pets4Homes user profile.

        Returns concatenated JSON lines (one per dog).
        """
        all_items: list[dict] = []
        page = 1

        while True:
            url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
            resp = requests.get(url, headers=self._HEADERS, timeout=30)
            resp.raise_for_status()

            data = self._extract_json(resp.text)
            listings = data.get("props", {}).get("pageProps", {}).get("listings", {})
            items = listings.get("items", [])
            meta = listings.get("metadata", {})

            if not items:
                break

            all_items.extend(items)

            if page >= meta.get("totalPages", 1):
                break
            page += 1

        return json.dumps(all_items)

    def parse(self, raw: str) -> list[Dog]:
        """Parse concatenated JSON into Dog objects."""
        items: list[dict] = json.loads(raw)
        dogs: list[Dog] = []

        for item in items:
            # Skip non-active
            if item.get("status") != "Active":
                continue

            title = item.get("generalInformation", {}).get("title", "")
            name = _clean_name(title)
            if not name:
                continue

            # Check reserved in title
            reserved = "reserved" in title.lower()

            # Breed from attributes
            breed = _extract_breed(item.get("attributes", []))

            # Gender from attributes
            gender = _extract_gender(item.get("attributes", []))

            # Age from DOB timestamp
            age = _compute_age(item.get("attributes", []))

            # Photo URL
            photo_url = _resolve_photo(item.get("profileImage", {}).get("originalImage", ""))

            # Detail URL
            slug = item.get("slug", "")
            url = f"{DETAIL_BASE}{slug}/" if slug else ""

            # Location
            loc = item.get("locationV3", {})
            town = loc.get("postalTown", "")
            region = loc.get("adminRegion2", "")
            location = f"{town}, {region}" if town and region else town or region

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=gender,
                    breed=breed,
                    url=url,
                    status="Reserved" if reserved else "Available",
                    location=location,
                    photo_url=photo_url,
                )
            )

        return dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, filter, and return new dogs.

        Filters: female only, age ≤ 12 months.
        """
        raw = self.fetch()
        all_dogs = self.parse(raw)

        # Exclude reserved
        available = [d for d in all_dogs if d.status != "Reserved"]

        # Post-parse filtering: female, ≤ 12 months
        filtered = [
            d for d in available
            if d.gender == "Female" and _age_months_from_str(d.age) <= 12
        ]

        new = self.diff(filtered)
        if new or not self._data_path.exists():
            self._save_current(filtered)
        return new

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(html: str) -> dict:
        """Extract __NEXT_DATA__ JSON from the HTML."""
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if not m:
            return {}
        return json.loads(m.group(1))


def _clean_name(title: str) -> str:
    """Extract a clean dog name from the listing title.

    Handles patterns like:
    - "💙 RALPHIE - gentle boy needs a quiet home 💙" → "Ralphie"
    - "🐾OWAIN - THE FAMILY DOG YOU'VE BEEN WAITING FOR🐾" → "Owain"
    - "❤️GYPSY - now reserved ❤️" → "Gypsy"
    - "🌼 Daisy - Loyal Companion Seeks Quiet Home 🌼" → "Daisy"
    - "🏡 Carla ❤️ NOW RESERVED" → "Carla"
    - "🐾 Buddy: adventure dog, cuddle expert ❤️" → "Buddy"
    - "🐾 Cedric – Stunning, Loyal Boy" → "Cedric"
    - "🐾 Charlotte🌟Golden Girl Seeks Sofa & Sunshine ☀️" → "Charlotte"
    """
    # Strip emojis and decorative symbols (replace with space to avoid run-ons)
    cleaned = _STRIP_RE.sub(" ", title).strip()
    # Take text before first separator (dash, en-dash) if present
    for sep in (" - ", " – ", "-"):
        if sep in cleaned:
            cleaned = cleaned.split(sep)[0].strip()
            break
    # Take just the first word (name) — handles taglines without separators
    # But preserve the name if it's already clearly just the name
    words = cleaned.split()
    if words:
        cleaned = words[0].rstrip(":")
    # Title-case the name (most titles are ALL CAPS)
    if cleaned.isupper():
        cleaned = cleaned.title()
    return cleaned


def _extract_breed(attributes: list[dict]) -> str:
    """Extract breed from attributes list.

    Returns a human-readable breed string (e.g. "Mixed Breed").
    """
    for attr in attributes:
        if attr.get("key") == "breed":
            value = attr.get("value", "")
            # Strip "pets.dogs.breed." prefix
            value = _BREED_PREFIX_RE.sub("", value)
            # Convert camelCase to Title Case
            value = re.sub(r"([A-Z])", r" \1", value).strip()
            # Title case
            value = " ".join(w.capitalize() for w in value.split())
            return value
    return ""


def _extract_gender(attributes: list[dict]) -> str:
    """Extract gender from numberOfMales/numberOfFemales attributes."""
    males = 0
    females = 0
    for attr in attributes:
        if attr.get("key") == "numberOfMales":
            try:
                males = int(attr.get("value", "0"))
            except (ValueError, TypeError):
                pass
        elif attr.get("key") == "numberOfFemales":
            try:
                females = int(attr.get("value", "0"))
            except (ValueError, TypeError):
                pass

    if females > males:
        return "Female"
    if males > females:
        return "Male"
    return ""


def _compute_age(attributes: list[dict]) -> str:
    """Compute age string from dateOfBirth timestamp.

    Returns e.g. "4 years", "8 months", or "" if not found.
    """
    for attr in attributes:
        if attr.get("key") == "dateOfBirth":
            try:
                ts_ms = int(attr.get("value", "0"))
                dob = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                now = datetime.now(tz=timezone.utc)
                # Total months
                months = (now.year - dob.year) * 12 + (now.month - dob.month)
                if now.day < dob.day:
                    months -= 1
                if months < 1:
                    months = 1  # floor at 1 month
                if months < 12:
                    label = "month" if months == 1 else "months"
                    return f"{months} {label}"
                years = months // 12
                label = "year" if years == 1 else "years"
                return f"{years} {label}"
            except (ValueError, TypeError, OSError):
                pass
    return ""


def _resolve_photo(photo_url: str) -> str:
    """Resolve the photo URL by replacing the ##NAME## placeholder."""
    if not photo_url:
        return ""
    return photo_url.replace("##NAME##", "image")


def _age_months_from_str(age_str: str) -> int:
    """Parse an age string into total months. Returns 999 if unparseable."""
    if not age_str:
        return 999
    year_match = re.search(r"(\d+)\s*years?\b", age_str.lower())
    month_match = re.search(r"(\d+)\s*months?\b", age_str.lower())
    if not year_match and not month_match:
        return 999
    years = int(year_match.group(1)) if year_match else 0
    months = int(month_match.group(1)) if month_match else 0
    return years * 12 + months

"""German Shepherd Rescue (GSDR) site checker.

Scrapes the homepage which lists dogs in two sections:
- "Urgent Dogs" (owl-carousel)
- "Featured Dogs For Rehoming" (box-product)

Each dog has a name and link to a detail page. All dogs
on the homepage are breed-specific (German Shepherds).
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

HOMEPAGE_URL = "https://www.germanshepherdrescue.co.uk/"
LOCATION = "German Shepherd Rescue, Little Vauld, Marden, Hereford HR1 3HA"
BREED = "German Shepherd"


class GsdrChecker(SiteChecker):
    site_name = "German Shepherd Rescue"
    data_file = "gsdr.txt"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
    }

    def fetch(self) -> str:
        resp = requests.get(HOMEPAGE_URL, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse homepage, visit detail pages for full data."""
        soup = BeautifulSoup(raw, "html.parser")
        dog_urls = self._parse_homepage_dog_urls(soup)
        if not dog_urls:
            return []

        dogs: list[Dog] = []
        for name, url in dog_urls:
            detail_html = self._fetch_detail(url)
            detail = self._parse_detail(detail_html, name, url)

            # Skip non-available (though homepage should only show available)
            if detail["status"] != "Available":
                continue

            dogs.append(
                Dog(
                    name=detail["name"],
                    age=detail["age"],
                    gender=detail["gender"],
                    breed=detail["breed"],
                    url=url,
                    status=detail["status"],
                    location=LOCATION,
                    photo_url=detail["photo_url"],
                )
            )

        return dogs

    # ── homepage helpers ──────────────────────────────────────────

    @staticmethod
    def _parse_homepage_dog_urls(soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Extract (name, url) pairs from both homepage sections.

        Deduplicates by URL.
        """
        seen: set[str] = set()
        results: list[tuple[str, str]] = []

        # Urgent Dogs section (#owl1) — each dog has .name > a
        urgent = soup.select_one("#owl1")
        if urgent:
            for name_div in urgent.select(".name"):
                link = name_div.find("a")
                if link:
                    href = link.get("href", "")
                    name = link.get_text(strip=True)
                    if href and href not in seen:
                        seen.add(href)
                        results.append((name, href))

        # Featured Dogs section (.box-product) — each dog has .name > a
        featured = soup.select_one(".box-product")
        if featured:
            for name_div in featured.select(".name"):
                link = name_div.find("a")
                if link:
                    href = link.get("href", "")
                    name = link.get_text(strip=True)
                    if href and href not in seen:
                        seen.add(href)
                        results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, fallback_name: str, url: str) -> dict:
        """Extract fields from a GSDR product detail page.

        Returns dict with name, age, gender, breed, status, photo_url.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove noisy elements
        for tag in soup(["script", "style", "nav", "footer", "noscript", "iframe"]):
            tag.decompose()

        body_text = soup.get_text(separator="\n")
        lines = body_text.splitlines()

        result: dict[str, str] = {
            "name": fallback_name,
            "age": "",
            "gender": "",
            "breed": BREED,
            "status": "Available",
            "photo_url": "",
        }

        # Better name from page title
        title = soup.select_one("title")
        if title:
            title_text = title.get_text(strip=True)
            # "Jazz-Sleaford" or "REBEL AND PENNY - KENT" — take before " —" or " -"
            for sep in (" — ", " - ", " | "):
                if sep in title_text:
                    result["name"] = title_text.split(sep)[0].strip()
                    break
            else:
                # If title is like "URGENT! German Shepherd Dog Jazz...", take the
                # part after "Dog " or just use the whole title
                if len(title_text) < 80:
                    result["name"] = title_text

        # Parse structured fields: "Gender: Female", "Age: 4", etc.
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            low = stripped.lower()
            if low.startswith("gender:"):
                result["gender"] = stripped[7:].strip()
            elif low.startswith("age:"):
                result["age"] = stripped[4:].strip()
            elif low.startswith("color:"):
                # Optional: could use color to refine breed
                pass
            elif low.startswith("neutered:"):
                pass

        # Normalize age: "8 YEARS / 10 YEARS" → keep as-is but clean
        age = result["age"]
        if age:
            # Convert "8 YEARS" to "8 years" etc.
            age = re.sub(r"\bYEARS?\b", "years", age, flags=re.IGNORECASE)
            age = re.sub(r"\bMONTHS?\b", "months", age, flags=re.IGNORECASE)
            result["age"] = age

        # Status: check for reserved/rehomed markers
        text_lower = body_text.lower()
        if "reserved" in text_lower:
            result["status"] = "Reserved"

        # Photo: from dogimages/ directory
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "dogimages/" in src:
                # Make relative URLs absolute
                if src.startswith("/"):
                    src = f"https://www.germanshepherdrescue.co.uk{src}"
                elif not src.startswith("http"):
                    src = f"https://www.germanshepherdrescue.co.uk/{src}"
                result["photo_url"] = src
                break

        return result

"""Teckels Animal Sanctuaries site checker.

Fetches the /dogs-for-adoption/ listing page, visits each dog's
/animals/{name}/ detail page for age, gender, breed data.
"""

from __future__ import annotations

import json

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LISTING_URL = "https://teckelsanimalsanctuaries.co.uk/dogs-for-adoption/"
LOCATION = "Teckels Animal Sanctuaries, Whitminster, Gloucester GL2 7PR"


class TeckelsChecker(SiteChecker):
    site_name = "Teckels Animal Sanctuaries"
    data_file = "teckels.txt"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
    }

    def fetch(self) -> str:
        resp = requests.get(LISTING_URL, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse listing page, visit detail pages, build Dog objects."""
        soup = BeautifulSoup(raw, "html.parser")
        dog_urls = self._parse_dog_urls(soup)
        if not dog_urls:
            return []

        dogs: list[Dog] = []
        for name, url in dog_urls:
            detail_html = self._fetch_detail(url)
            detail = self._parse_detail(detail_html, name)

            # Skip reserved/non-available dogs
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

    # ── listing page helpers ───────────────────────────────────────

    @staticmethod
    def _parse_dog_urls(soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Extract (name, url) pairs from the listing page.

        Each dog is an h2.elementor-heading-title containing an <a>
        that links to /animals/{name}/.
        """
        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for h2 in soup.select("h2.elementor-heading-title"):
            link = h2.find("a")
            if not link:
                continue
            href = link.get("href", "")
            if "/animals/" not in href:
                continue
            if href in seen:
                continue
            seen.add(href)
            name = link.get_text(strip=True)
            if name:
                results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, fallback_name: str) -> dict:
        """Extract all fields from a detail page.

        Returns dict with name, age, gender, breed, status, photo_url.
        """
        soup = BeautifulSoup(html, "html.parser")

        result: dict[str, str] = {
            "name": fallback_name,
            "age": "",
            "gender": "",
            "breed": "",
            "status": "Available",
            "photo_url": "",
        }

        # Get a better name from h1
        h1 = soup.select_one("h1.elementor-heading-title")
        if h1:
            result["name"] = h1.get_text(strip=True)

        # Extract Age, Gender, Breed from h2 headings
        for h2 in soup.select("h2.elementor-heading-title"):
            text = h2.get_text(strip=True)
            if text.lower().startswith("age:"):
                result["age"] = text[4:].strip()
            elif text.lower().startswith("gender:"):
                result["gender"] = text[7:].strip()
            elif text.lower().startswith("breed:"):
                result["breed"] = text[6:].strip()

        # Status: check for reserved/rehomed markers in page text
        body_text = soup.get_text().lower()
        if "reserved" in body_text and "available" not in body_text:
            result["status"] = "Reserved"

        # Photo: from JSON-LD thumbnailUrl
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    graph = data.get("@graph", [data])
                    if isinstance(graph, list):
                        for item in graph:
                            thumb = item.get("thumbnailUrl", "")
                            if thumb:
                                result["photo_url"] = thumb
                                break
            except (json.JSONDecodeError, TypeError):
                pass

        return result

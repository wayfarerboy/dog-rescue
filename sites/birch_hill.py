"""Birch Hill Dog Rescue site checker.

Fetches the /adopt-a-dog/ listing page, visits each dog's detail page
for full data.  Skips dogs marked "Available to Sponsor" (not adoptable).

Uses curl for HTTP because the site's Cloudflare configuration blocks
the Python requests library's TLS fingerprint.
"""

from __future__ import annotations

import re
import subprocess

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LOCATION = "Neen Sollars, Kidderminster DY14 0AQ"


class BirchHillChecker(SiteChecker):
    site_name = "Birch Hill Dog Rescue"
    data_file = "birch-hill.txt"

    LISTING_URL = "https://birchhilldogrescue.org.uk/adopt-a-dog/"

    _HEADERS = [
        "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ]

    def fetch(self) -> str:
        return _curl_get(self.LISTING_URL, self._HEADERS)

    def parse(self, raw: str) -> list[Dog]:
        soup = BeautifulSoup(raw, "html.parser")
        dog_urls = self._parse_dog_urls(soup)
        if not dog_urls:
            return []

        dogs: list[Dog] = []
        for name, url in dog_urls:
            detail_html = _curl_get(url, self._HEADERS)
            detail = self._parse_detail(detail_html, name)

            # Skip sponsor-only dogs (not adoptable)
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
        """Extract (name, url) pairs from dog cards on the listing page."""
        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for a in soup.select("a[href]"):
            href = a.get("href", "")
            # Match /dog/{name}/ pattern
            if re.search(r"/dog/[^/]+/?$", href) and href not in seen:
                seen.add(href)
                name = a.get_text(strip=True)
                if name and name.lower() != "meet me":
                    results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    @staticmethod
    def _parse_detail(html: str, fallback_name: str) -> dict:
        """Extract all fields from a detail page.

        Returns dict with name, age, gender, breed, status, photo_url.
        """
        soup = BeautifulSoup(html, "html.parser")

        result = {
            "name": fallback_name,
            "age": "",
            "gender": "",
            "breed": "",
            "status": "Available",
            "photo_url": "",
        }

        body_text = soup.get_text(separator="\n")

        for line in body_text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("gender"):
                result["gender"] = stripped[6:].strip()
            elif stripped.lower().startswith("breed"):
                result["breed"] = stripped[5:].strip()
            elif stripped.lower().startswith("age"):
                result["age"] = stripped[3:].strip()

        # Status: check for sponsor-only markers
        if "Available to Sponsor" in body_text:
            result["status"] = "Sponsor Only"
        elif "Reserved" in body_text:
            # Scan for "Reserved" near the top of the page
            first_chunk = body_text[:500]
            if "Reserved" in first_chunk:
                result["status"] = "Reserved"

        # Photo: first content image
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "wp-content/uploads" in src:
                result["photo_url"] = src
                break

        return result


def _curl_get(url: str, headers: list[str]) -> str:
    """Fetch a URL using curl. Necessary for sites that block requests."""
    cmd: list[str] = ["curl", "-sS", "-L"]
    for h in headers:
        cmd.extend(["-H", h])
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 or not result.stdout.strip():
        # Fall back to requests for non-Cloudflare sites
        fallback = requests.get(
            url,
            headers={"User-Agent": headers[0].split(": ", 1)[1]},
            timeout=30,
        )
        fallback.raise_for_status()
        return fallback.text
    return result.stdout

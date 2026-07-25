"""Wythall Animal Sanctuary site checker.

Fetches the /dogs/ listing page (Squarespace), visits each dog's
/dogs/{name} profile page for breed, age, gender, etc.
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import Dog, SiteChecker

LISTING_URL = "https://www.wythallanimalsanctuary.org/dogs/"
LOCATION = "Wythall Animal Sanctuary, Redditch Rd, Hopwood, Alvechurch B48 7TW"


class WythallChecker(SiteChecker):
    site_name = "Wythall Animal Sanctuary"
    data_file = "wythall.txt"

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

            # Skip non-available dogs (foster-only, reserved, etc.)
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
        """Extract (name, url) pairs from the Squarespace listing page.

        Each dog is an <a class="grid-item" href="/dogs/{name}">.
        """
        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for link in soup.select('a.grid-item[href*="/dogs/"]'):
            href = link.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            # Derive name from URL slug
            m = re.search(r"/dogs/([^/]+)/?$", href)
            if not m:
                continue
            slug = m.group(1)
            name = slug.replace("-", " ").title()

            # Make absolute if relative
            if href.startswith("/"):
                href = f"https://www.wythallanimalsanctuary.org{href}"

            results.append((name, href))

        return results

    # ── detail page helpers ────────────────────────────────────────

    def _fetch_detail(self, url: str) -> str:
        resp = requests.get(url, headers=self._HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_detail(html: str, fallback_name: str) -> dict:
        """Extract all fields from a Squarespace dog profile page.

        Returns dict with name, age, gender, breed, status, photo_url.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove noisy elements
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe"]):
            tag.decompose()

        result: dict[str, str] = {
            "name": fallback_name,
            "age": "",
            "gender": "",
            "breed": "",
            "status": "Available",
            "photo_url": "",
        }

        body_text = soup.get_text(separator="\n")
        lines = body_text.splitlines()

        # Try to get a better name from the page title or h1
        title = soup.select_one("title")
        if title:
            title_text = title.get_text(strip=True)
            # "Cherry - Foster Me <3 — Wythall Animal Sanctuary" → "Cherry"
            # "Crumpet — Wythall Animal Sanctuary" → "Crumpet"
            for sep in (" — ", " - ", " | ", " \u2014 ", " \u2013 "):
                if sep in title_text:
                    result["name"] = title_text.split(sep)[0].strip()
                    break

        h1 = soup.select_one("h1") or soup.select_one(".entry-title")
        if h1:
            h1_text = h1.get_text(strip=True)
            if h1_text and len(h1_text) < 60:
                # "Hi, I'm Cherry" → "Cherry"
                m = re.search(r"(?:Hi,?\s*)?(?:I'?m\s+)?(.+)", h1_text, re.IGNORECASE)
                if m:
                    result["name"] = m.group(1).strip().strip("!")

        # Parse the "More About Me" section.
        # Real Squarespace pages use <li><p><strong>Label</strong> -Value</p></li>.
        # The heading is sometimes <h3>, sometimes <p><strong>.
        # Test fixtures use flat text with "Label - Value" lines.
        more_heading = soup.find(
            ["h3", "strong"],
            string=re.compile(r"More About Me", re.IGNORECASE),
        )
        if more_heading:
            ul = more_heading.find_next("ul")
            if ul:
                for li in ul.select("li"):
                    strong = li.find("strong")
                    if not strong:
                        continue
                    label = strong.get_text(strip=True).rstrip("-").strip().lower()
                    # Get text after the <strong> tag
                    value_parts: list[str] = []
                    for sibling in strong.next_siblings:
                        if hasattr(sibling, "get_text"):
                            value_parts.append(sibling.get_text(strip=True))
                        elif isinstance(sibling, str):
                            value_parts.append(sibling.strip())
                    value = " ".join(p for p in value_parts if p).strip()
                    # Strip leading dash if present (from "-Value")
                    value = re.sub(r"^\s*-\s*", "", value).strip()

                    if label == "breed":
                        result["breed"] = value
                    elif label == "sex":
                        result["gender"] = value
                    elif label == "age":
                        result["age"] = value
        else:
            # Check for h4-based format: <h4><strong>AGE:</strong> 1 Year</h4>
            # Used by some dog profiles (Ronnie, Ziggy).
            h4_found = False
            for h4 in soup.select("h4"):
                strong = h4.find("strong")
                if not strong:
                    continue
                label = strong.get_text(strip=True).rstrip(":").strip().lower()
                # Get text after the <strong> within the h4
                value_parts: list[str] = []
                for sibling in strong.next_siblings:
                    if hasattr(sibling, "get_text"):
                        value_parts.append(sibling.get_text(strip=True))
                    elif isinstance(sibling, str):
                        value_parts.append(sibling.strip())
                value = " ".join(p for p in value_parts if p).strip()

                if label == "breed":
                    result["breed"] = value
                    h4_found = True
                elif label == "age":
                    result["age"] = value
                    h4_found = True
                elif label in ("sex", "gender"):
                    result["gender"] = value
                    h4_found = True

            if not h4_found:
                # Fallback: parse flat text with "Label - Value" lines (test fixtures)
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    m = re.match(r"([A-Za-z][A-Za-z /\-&]+?)\s*-\s*(.+)", stripped)
                    if not m:
                        continue
                    label = m.group(1).strip().lower()
                    value = m.group(2).strip()
                    if label == "breed":
                        result["breed"] = value
                    elif label == "sex":
                        result["gender"] = value
                    elif label == "age":
                        result["age"] = value

        # Gender fallback: look for "Entire male" / "Entire female" text
        if not result["gender"]:
            text_lower = body_text.lower()
            if "entire male" in text_lower:
                result["gender"] = "Male"
            elif "entire female" in text_lower:
                result["gender"] = "Female"

        # Status detection: look for foster/rehome/adoption indicators
        text_lower = body_text.lower()
        # The header text right after the name
        # "I'm looking for my forever home" → Available
        # "I'm looking for a quiet loving foster home" → Foster
        # Check the section around the name
        header_area = "\n".join(lines[:30]).lower()
        if "foster" in header_area and "forever" not in header_area:
            result["status"] = "Foster"
        if "reserved" in text_lower:
            result["status"] = "Reserved"

        # Photo: first Squarespace image that's not a logo/icon
        for img in soup.select("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and ("squarespace-cdn.com" in src or "squarespace.com" in src):
                low = src.lower()
                if "logo" not in low and "icon" not in low and "favicon" not in low:
                    result["photo_url"] = src
                    break

        return result

"""Birmingham Dogs Home site checker — uses WordPress REST API.

Both centres (Birmingham and Wolverhampton) are served from a single
WordPress site.  Dog data is exposed via /wp-json/wp/v2/dogs.
"""

from __future__ import annotations

import json

import requests

from .base import Dog, SiteChecker


class BirminghamDogsHomeChecker(SiteChecker):
    site_name = "Birmingham Dogs Home"
    data_file = "birmingham-dogs-home.txt"

    API_URL = "https://birminghamdogshome.org.uk/wp-json/wp/v2/dogs"

    def fetch(self) -> str:
        """Fetch all dogs from the WordPress REST API."""
        params: dict[str, str | int] = {
            "per_page": 100,
            "_embed": "wp:featuredmedia",
        }
        resp = requests.get(self.API_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[Dog]:
        """Parse WP REST API JSON into Dog objects, filtering non-available."""
        dogs: list[Dog] = []

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

        for item in data:
            meta = item.get("meta", {})
            status = meta.get("status", "")
            if status != "AVAIL":
                continue

            name = meta.get("name", "")
            breed = meta.get("breed", "")
            sex = meta.get("sex", "")
            # Strip neutered tag: "Male (N)" -> "Male", "Female (N)" -> "Female"
            sex = sex.replace(" (N)", "")
            age = meta.get("age-in-years-and-months", "")
            centre = meta.get("centre", "")  # "Birmingham Centre" or "Wolverhampton Centre"
            url = item.get("link", "")

            # Extract photo URL from embedded featured media
            photo_url = ""
            embedded = item.get("_embedded", {})
            media_list = embedded.get("wp:featuredmedia", [])
            if media_list:
                photo_url = media_list[0].get("source_url", "")

            dogs.append(
                Dog(
                    name=name,
                    age=age,
                    gender=sex,
                    breed=breed,
                    url=url,
                    status="Available",
                    location=centre,
                    photo_url=photo_url,
                )
            )

        return dogs

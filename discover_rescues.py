#!/usr/bin/env python3
"""Discover dog rescue centres near Worcester using Google Places API (New).

Usage:
    python3 discover_rescues.py

Requires:
    - GOOGLE_MAPS_API_KEY in .env
    - Places API (New) enabled on that key
      → https://console.cloud.google.com/apis/library/places.googleapis.com

Outputs a table of found rescues with name, address, distance, website.
Pass --json for machine-readable output.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent

# ── config ────────────────────────────────────────────────────────────

ORIGIN_LAT = 52.1917
ORIGIN_LNG = -2.2206
ORIGIN_ADDRESS = "224 Bath Road, Worcester WR5 3ER"
SEARCH_RADIUS_MILES = 120  # matches MAX_DISTANCE_MILES
SEARCH_RADIUS_M = int(SEARCH_RADIUS_MILES * 1609.344)

# Queries to run — multiple phrasings to catch different listings
SEARCH_QUERIES = [
    "dog rescue centre Worcestershire UK",
    "dog rehoming centre West Midlands UK",
    "animal rescue centre near Worcester UK",
    "dog adoption centre Gloucestershire UK",
    "dog shelter Birmingham UK area",
]

# These are already tracked or excluded — skip them
KNOWN_NAMES: set[str] = {
    "All Dogs Matter",
    "Birch Hill Dog Rescue",
    "Cheltenham Animal Shelter",
    "Cotswolds Dogs & Cats Home",
    "Dogs Trust",
    "Forest Dog Rescue",
    "Jerry Green Dog Rescue",
    "Many Tears Animal Rescue",
    "Paws2Rescue",
    "Pro Dogs Direct",
    "Raystede Centre for Animal Welfare",
    "RSPCA",
    "Second Chance Spaniel Rescue",
    "South East Dog Rescue",
    "Spaniel Aid",
    "Worcester Animal Rescue",
}


def _load_api_key() -> str:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        print("Error: .env file not found", file=sys.stderr)
        sys.exit(1)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("GOOGLE_MAPS_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("Error: GOOGLE_MAPS_API_KEY not set in .env", file=sys.stderr)
    sys.exit(1)


def search_places(api_key: str, query: str) -> list[dict]:
    """Call Places API (New) text search. Returns list of place dicts."""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,"
            "places.websiteUri,places.location,places.types,"
            "places.googleMapsUri"
        ),
    }
    body = {
        "textQuery": query,
        "maxResultCount": 20,
    }

    resp = requests.post(url, headers=headers, json=body, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results: list[dict] = []
    for place in data.get("places", []):
        loc = place.get("location", {})
        results.append(
            {
                "name": place.get("displayName", {}).get("text", ""),
                "address": place.get("formattedAddress", ""),
                "website": place.get("websiteUri", ""),
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "maps_url": place.get("googleMapsUri", ""),
                "types": place.get("types", []),
            }
        )
    return results


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in miles."""
    import math

    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_relevant(place: dict) -> bool:
    """Check if a place looks like a dog rescue/adoption centre."""
    name = place["name"].lower()
    types = place.get("types", [])

    # Must have at least one relevant type
    relevant_types = {
        "pet_care",
        "veterinary_care",
        "pet_store",
        "animal_shelter",
        "store",
    }
    if not any(t in relevant_types for t in types):
        return False

    # Keywords that suggest a rescue/adoption centre
    rescue_keywords = [
        "rescue", "rehom", "adoption", "shelter", "sanctuary",
        "animal", "dog", "dogs trust", "rspca", "blue cross",
        "dog home", "dogs home", "kennel", "greyhound",
        "spaniel", "lurcher", "stray", "abandoned", "trust",
    ]
    if not any(kw in name for kw in rescue_keywords):
        return False

    # Exclude known
    for known in KNOWN_NAMES:
        if known.lower() in name:
            return False

    # Exclude clearly non-dog rescues
    non_dog = [
        "donkey", "guinea pig", "rabbit", "wildlife", "farm animal",
        "search and rescue", "horse", "pony", "cat", "katkinz", "feline",
        "feathers", "reptile", "bird of prey", "pet adoption uk",
    ]
    if any(kw in name for kw in non_dog):
        return False

    # Exclude vets that aren't rescues
    vet_only = ["vets", "veterinary", "vet clinic", "vet hospital"]
    if any(v in name for v in vet_only):
        if not any(kw in name for kw in ["rescue", "rehom", "shelter", "sanctuary"]):
            return False

    return True


def main() -> None:
    api_key = _load_api_key()
    json_out = "--json" in sys.argv

    all_places: dict[str, dict] = {}  # dedupe by name

    for query in SEARCH_QUERIES:
        try:
            places = search_places(api_key, query)
        except requests.exceptions.RequestException as e:
            print(f"Error searching '{query}': {e}", file=sys.stderr)
            continue

        for place in places:
            if not place["name"]:
                continue
            if place["name"] in all_places:
                continue
            if not is_relevant(place):
                continue

            # Add distance
            if place["lat"] and place["lng"]:
                place["dist_miles"] = haversine_miles(
                    ORIGIN_LAT, ORIGIN_LNG, place["lat"], place["lng"]
                )
            else:
                place["dist_miles"] = None

            all_places[place["name"]] = place

    if json_out:
        print(json.dumps(list(all_places.values()), indent=2))
    else:
        # Table output
        sorted_places = sorted(all_places.values(), key=lambda p: p.get("dist_miles") or 9999)
        print(f"\nFound {len(sorted_places)} potential new rescue centre(s) within {SEARCH_RADIUS_MILES} mi:\n")
        print(f"  {'Name':<40} {'Mi':>5}  {'Website'}")
        print(f"  {'─' * 40} {'─' * 5}  {'─' * 50}")
        for p in sorted_places:
            dist = f"{p['dist_miles']:.0f}" if p["dist_miles"] else "?"
            web = p["website"] or p.get("maps_url", "")
            name = p["name"][:39]
            print(f"  {name:<40} {dist:>5}  {web}")
        print()

        if not all_places:
            print("  (none found — try broadening search queries or radius)\n")


if __name__ == "__main__":
    main()

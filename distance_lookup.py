"""Distance lookup — Google Maps Distance Matrix API with JSON cache.

Maps rescue center names → driving distance in miles from
224 Bath Road, Worcester WR5 3ER.

Usage:
    from distance_lookup import DistanceLookup, filter_dogs_by_distance

    dl = DistanceLookup("data", api_key="...")
    distance = dl.get_distance("Cardiff")  # Returns miles or None

    filtered = filter_dogs_by_distance(new_dogs, dl, max_distance=120)
"""

from __future__ import annotations

import json
from pathlib import Path

from sites.base import Dog

ORIGIN = "224 Bath Road, Worcester WR5 3ER"
MAX_DISTANCE_MILES_DEFAULT = 120


class DistanceLookup:
    """Maps rescue center names to driving distances.

    File path: <data_dir>/distances.json — JSON dict of centre→miles.
    Hits the Google Maps Distance Matrix API once per unique center,
    caching results.
    """

    _FILE_NAME = "distances.json"

    def __init__(self, data_dir: str, api_key: str = "") -> None:
        self._data_dir = Path(data_dir)
        self._data_path = self._data_dir / self._FILE_NAME
        self._api_key = api_key
        self._cache: dict[str, float | None] = {}
        self._load()

    def _load(self) -> None:
        """Load cached distances from disk."""
        if self._data_path.exists():
            try:
                loaded = json.loads(self._data_path.read_text())
                if isinstance(loaded, dict):
                    self._cache = loaded
            except (json.JSONDecodeError, TypeError):
                self._cache = {}

    def save(self) -> None:
        """Persist cache to disk."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._data_path.write_text(json.dumps(self._cache, indent=2) + "\n")

    def centers(self) -> list[str]:
        """Return all known center names."""
        return list(self._cache.keys())

    def get_distance(self, center: str) -> float | None:
        """Return driving distance in miles, or None if unknown.

        Uses cached value when available; otherwise calls the API.
        """
        if not center:
            return None
        if center in self._cache:
            return self._cache[center]
        return self._lookup(center)

    def _lookup(self, center: str) -> float | None:
        """Call Google Maps Distance Matrix API for one center.

        Caches the result (including None for unfound centers) and
        persists to disk.
        """
        if not self._api_key:
            return None

        import requests

        params = {
            "origins": ORIGIN,
            "destinations": center,
            "units": "imperial",
            "key": self._api_key,
        }
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            elements = data.get("rows", [{}])[0].get("elements", [])
            if elements:
                elem = elements[0]
                if elem.get("status") == "OK":
                    distance_meters = elem["distance"]["value"]
                    miles = distance_meters / 1609.344
                    self._cache[center] = miles
                    self.save()
                    return miles

            # Center not found or no route — cache the negative result
            self._cache[center] = None
            self.save()
            return None
        except Exception:
            return None


def filter_dogs_by_distance(
    dogs: list[Dog],
    distance_lookup: DistanceLookup,
    max_distance: float | None = None,
) -> list[Dog]:
    """Filter dogs whose center is beyond max_distance miles.

    Dogs with unknown centers (no cached distance) are included —
    they are not penalized for missing data.

    If max_distance is None, no filtering is applied.
    """
    if max_distance is None:
        return dogs

    result: list[Dog] = []
    for dog in dogs:
        distance = distance_lookup.get_distance(dog.location)
        if distance is None or distance <= max_distance:
            result.append(dog)
    return result

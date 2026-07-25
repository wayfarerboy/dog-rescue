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
WORCESTER_LAT = 52.1917
WORCESTER_LNG = -2.2206
MAX_DISTANCE_MILES_DEFAULT = 120


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute straight-line distance in miles between two lat/lng points."""
    import math

    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


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


# Rescues that should never be excluded by distance evaluation.
# E.g. Paws2Rescue brings dogs from Romania to the UK for adoption,
# so "Romania" as a location does not mean you drive there to collect.
NEVER_EXCLUDE: set[str] = {"Paws2Rescue"}


def evaluate_rescue_centers(
    data_dir: str,
    distance_lookup: DistanceLookup,
    max_distance: float,
    too_far_list,
) -> list[tuple[str, str, float]]:
    """Evaluate which rescue centres have only one location and are too far.

    A rescue is flagged if ALL its cached dogs share a single non-empty
    location and that location is beyond max_distance miles.

    Rescues already in the too-far list are skipped.
    Rescues in NEVER_EXCLUDE are always skipped.

    Returns list of (site_name, location, distance_miles) for newly
    excluded rescues, and adds them to the too-far list.
    """
    from pathlib import Path

    from sites.base import FIELD_COUNT

    data_path = Path(data_dir)
    newly_excluded: list[tuple[str, str, float]] = []

    # Lazy import to avoid circular dependency
    from sites.registry import get_checkers

    checkers = get_checkers(str(data_dir))

    for checker in checkers:
        if checker.site_name in too_far_list or checker.site_name in NEVER_EXCLUDE:
            continue

        cache_file = data_path / checker.data_file
        if not cache_file.exists():
            continue

        lines = [
            l.strip() for l in cache_file.read_text().splitlines() if l.strip()
        ]
        if not lines:
            continue

        # Collect unique non-empty locations
        locations: set[str] = set()
        for line in lines:
            parts = [p.strip() for p in line.split(" | ")]
            # location is field index 5 (0-indexed) in the 8-field format
            if len(parts) >= 6 and parts[5]:
                locations.add(parts[5])

        # Single-location rescues only
        if len(locations) != 1:
            continue

        location = next(iter(locations))
        distance = distance_lookup.get_distance(location)

        if distance is not None and distance > max_distance:
            too_far_list.add(checker.site_name)
            newly_excluded.append((checker.site_name, location, distance))

    return newly_excluded


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

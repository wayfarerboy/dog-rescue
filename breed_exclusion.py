"""Breed exclusion list — breeds to filter out from results.

Usage:
    from breed_exclusion import BreedExclusionList, filter_dogs_by_breed

    bel = BreedExclusionList("data")
    filtered = filter_dogs_by_breed(dogs, bel)
"""

from __future__ import annotations

from pathlib import Path

from sites.base import Dog


class BreedExclusionList:
    """A set of breed names excluded from results, persisted as a text file.

    File path: <data_dir>/excluded-breeds.txt — one breed per line.
    Matching is case-insensitive after stripping whitespace.
    """

    _FILE_NAME = "excluded-breeds.txt"

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_path = self._data_dir / self._FILE_NAME
        self._breeds: list[str] = []
        self._normalized: set[str] = set()
        if self._data_path.exists():
            self._breeds = [
                line.strip()
                for line in self._data_path.read_text().splitlines()
                if line.strip()
            ]
            self._normalized = {b.strip().lower() for b in self._breeds}

    def breeds(self) -> list[str]:
        """Return all excluded breed names in insertion order."""
        return list(self._breeds)

    def add(self, breed: str) -> None:
        """Add a breed to the exclusion list. Idempotent."""
        normalized = breed.strip().lower()
        if normalized not in self._normalized:
            self._breeds.append(breed.strip())
            self._normalized.add(normalized)
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._data_path.write_text("\n".join(self._breeds) + "\n")

    def remove(self, breed: str) -> None:
        """Remove a breed from the exclusion list. No-op if not present."""
        normalized = breed.strip().lower()
        if normalized in self._normalized:
            self._breeds = [b for b in self._breeds if b.strip().lower() != normalized]
            self._normalized.discard(normalized)
            self._data_dir.mkdir(parents=True, exist_ok=True)
            if self._breeds:
                self._data_path.write_text("\n".join(self._breeds) + "\n")
            else:
                self._data_path.write_text("")

    def __contains__(self, breed: str) -> bool:
        return breed.strip().lower() in self._normalized


def filter_dogs_by_breed(
    dogs: list[Dog],
    breed_exclusion_list: BreedExclusionList,
) -> list[Dog]:
    """Filter out dogs whose breed is in the exclusion list.

    Matching is case-insensitive. Dogs with empty breed are kept.
    """
    return [d for d in dogs if d.breed not in breed_exclusion_list]

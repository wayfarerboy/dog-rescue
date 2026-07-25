"""Base classes for site checkers."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Dog:
    """A dog available for adoption."""

    name: str
    age: str           # "11 Months", "1 Year Old", etc.
    gender: str        # "Female", "Male"
    breed: str
    url: str           # Full profile URL (unique key)
    status: str = ""   # "Available", "For Foster", etc.
    location: str = ""  # Centre / region

    def as_line(self) -> str:
        """Pipe-separated line for data file storage."""
        return " | ".join(
            [self.status, self.name, self.age, self.gender, self.breed, self.location, self.url]
        )


class SiteChecker(ABC):
    """Abstract base for a site-specific dog checker.

    Subclasses implement fetch() and parse(). The base handles diffing
    against a data file and returning new dogs.
    """

    site_name: str = ""          # Display name for this site
    data_file: str = ""          # Path to data file for change detection

    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._data_path = self.data_dir / self.data_file

    @abstractmethod
    def fetch(self) -> str:
        """Fetch raw data from the site. Returns HTML or JSON text."""
        ...

    @abstractmethod
    def parse(self, raw: str) -> List[Dog]:
        """Parse raw data into a list of Dog objects."""
        ...

    def _load_previous(self) -> set[str]:
        """Load previously seen dog URLs from the data file."""
        if not self._data_path.exists():
            return set()
        urls = set()
        for line in self._data_path.read_text().strip().splitlines():
            # URL is the last field in the pipe-separated line
            parts = line.rsplit(" | ", 1)
            if len(parts) == 2:
                urls.add(parts[1])
            elif line.strip():
                urls.add(line.strip())
        return urls

    def _save_current(self, dogs: List[Dog]) -> None:
        """Save current dogs to the data file."""
        self._data_path.write_text("\n".join(d.as_line() for d in dogs) + "\n")

    def diff(self, current: List[Dog]) -> List[Dog]:
        """Return dogs not seen in the previous run."""
        previous_urls = self._load_previous()
        new_dogs = [d for d in current if d.url not in previous_urls]
        return new_dogs

    def check(self) -> List[Dog]:
        """Fetch, parse, and return new dogs. Updates data file if any found."""
        raw = self.fetch()
        dogs = self.parse(raw)
        new = self.diff(dogs)
        if new:
            self._save_current(dogs)
        return new

    def format_section(self, new_dogs: List[Dog], heading: str, columns: str) -> str:
        """Format new dogs as an email section."""
        if not new_dogs:
            return ""
        lines = [f"=== {heading} ===", f"New dogs available ({columns}):", ""]
        for d in new_dogs:
            lines.append(
                f"{d.status} | {d.name} | {d.age} | "
                f"{d.gender} | {d.breed} | {d.location} | {d.url}"
            )
        lines.append("")
        return "\n".join(lines)

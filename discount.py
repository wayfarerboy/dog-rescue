"""Discounted-dog list — tracking dogs the user has looked at and dismissed.

A dog is identified by its profile URL (the unique key, since names collide).

Usage:
    from discount import DiscountedList

    dl = DiscountedList("data")
    if url in dl:
        # already looked at and discounted
    dl.add(url)
    dl.remove(url)
"""

from __future__ import annotations

from pathlib import Path


class DiscountedList:
    """A set of dog URLs the user has looked at and discounted.

    File path: <data_dir>/discounted.txt — one dog URL per line.
    """

    _FILE_NAME = "discounted.txt"

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_path = self._data_dir / self._FILE_NAME
        self._urls: list[str] = []
        if self._data_path.exists():
            self._urls = [
                line.strip()
                for line in self._data_path.read_text().splitlines()
                if line.strip()
            ]

    def urls(self) -> list[str]:
        """Return all discounted dog URLs in insertion order."""
        return list(self._urls)

    def add(self, url: str) -> None:
        """Add a dog URL to the discounted list. Idempotent."""
        url = url.strip()
        if url and url not in self._urls:
            self._urls.append(url)
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._data_path.write_text("\n".join(self._urls) + "\n")

    def remove(self, url: str) -> None:
        """Remove a dog URL from the discounted list. No-op if not present."""
        url = url.strip()
        if url in self._urls:
            self._urls = [u for u in self._urls if u != url]
            self._data_dir.mkdir(parents=True, exist_ok=True)
            if self._urls:
                self._data_path.write_text("\n".join(self._urls) + "\n")
            else:
                self._data_path.write_text("")

    def toggle(self, url: str) -> bool:
        """Flip the discounted state for a URL. Returns True if now discounted."""
        url = url.strip()
        if url in self._urls:
            self.remove(url)
            return False
        self.add(url)
        return True

    def __contains__(self, url: str) -> bool:
        return url.strip() in self._urls

    def __len__(self) -> int:
        return len(self._urls)

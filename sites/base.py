"""Base classes for site checkers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# Ordered field names matching as_line() output
FIELD_NAMES = ["status", "name", "age", "gender", "breed", "location", "photo_url", "url"]
FIELD_COUNT = len(FIELD_NAMES)


@dataclass
class Dog:
    """A dog available for adoption."""

    name: str
    age: str              # "11 Months", "1 Year Old", etc.
    gender: str           # "Female", "Male"
    breed: str
    url: str              # Full profile URL (unique key)
    status: str = ""      # "Available", "For Foster", etc.
    location: str = ""    # Centre / region
    photo_url: str = ""   # Profile image URL

    def as_line(self) -> str:
        """Pipe-separated line for data file storage."""
        return " | ".join(
            [
                self.status,
                self.name,
                self.age,
                self.gender,
                self.breed,
                self.location,
                self.photo_url,
                self.url,
            ]
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
    def parse(self, raw: str) -> list[Dog]:
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

    def _save_current(self, dogs: list[Dog]) -> None:
        """Save current dogs to the data file."""
        self._data_path.write_text("\n".join(d.as_line() for d in dogs) + "\n")

    def diff(self, current: list[Dog]) -> list[Dog]:
        """Return dogs not seen in the previous run."""
        previous_urls = self._load_previous()
        new_dogs = [d for d in current if d.url not in previous_urls]
        return new_dogs

    def check(self) -> list[Dog]:
        """Fetch, parse, and return new dogs. Updates data file if any found.

        Always saves the cache on the first run (when no cache file exists)
        so that every site has a baseline cache file.
        """
        raw = self.fetch()
        dogs = self.parse(raw)
        new = self.diff(dogs)
        if new or not self._data_path.exists():
            self._save_current(dogs)
        return new

    def extract_from_profile(self, html: str) -> dict[str, str]:
        """Extract fields from a dog's profile/detail page HTML.

        Subclasses override this to scrape per-site profile pages.
        Return a dict of field_name→value. Only fields you can extract
        need to be present; the repair script fills in whatever is provided.
        """
        return {}

    def format_section(self, new_dogs: list[Dog], heading: str, columns: str) -> str:
        """Format new dogs as a plain-text email section."""
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

    def format_section_html(self, new_dogs: list[Dog], site_name: str) -> str:
        """Format new dogs as an HTML email section (card layout)."""
        if not new_dogs:
            return ""

        cards: list[str] = []
        for d in new_dogs:
            # Escape HTML entities in user data
            name = _esc(d.name)
            age = _esc(d.age)
            gender = _esc(d.gender)
            breed = _esc(d.breed)
            location = _esc(d.location)
            url = _esc(d.url)

            photo_html = _photo_tag(d.photo_url)

            cards.append(
                '<div style="border:1px solid #e0e0e0; border-radius:8px; '
                'padding:14px; margin-bottom:12px; font-family:-apple-system,'
                'BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif">'
                '<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
                f'<td width="56" style="vertical-align:top">{photo_html}</td>'
                '<td style="vertical-align:top;padding-left:12px">'
                f'<div style="font-size:16px;font-weight:bold;color:#222;'
                f'margin-bottom:3px">{name}</div>'
                f'<div style="font-size:13px;color:#555;line-height:1.5">'
                f'{breed} &middot; {gender} &middot; {age}</div>'
                f'<div style="font-size:12px;color:#888;margin-top:4px">'
                f'📍 {location}</div>'
                f'<a href="{url}" style="display:inline-block;margin-top:8px;'
                f'font-size:12px;font-weight:600;color:#1a73e8;'
                f'text-decoration:none;border:1px solid #1a73e8;'
                f'border-radius:4px;padding:5px 12px">View profile →</a>'
                '</td></tr></table></div>'
            )

        count = len(new_dogs)
        label = "1 new dog matches" if count == 1 else f"{count} new dogs match"

        return (
            '<div style="margin-bottom:20px">'
            f'<h2 style="font-size:16px;font-weight:700;color:#222;'
            f'margin:0 0 2px 0">{_esc(site_name)}</h2>'
            f'<p style="font-size:13px;color:#888;margin:0 0 14px 0">{label} '
            'match your criteria</p>'
            + "".join(cards)
            + "</div>"
        )


def _esc(text: str) -> str:
    """Escape HTML entities in a string."""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _photo_tag(photo_url: str) -> str:
    """Return an <img> tag if photo_url is set, otherwise a paw-placeholder div."""
    if photo_url:
        safe_url = _esc(photo_url)
        return (
            f'<img src="{safe_url}" alt="🐾" width="52" height="52" '
            'style="border-radius:8px;object-fit:cover;display:block" />'
        )
    return (
        '<div style="width:52px;height:52px;background:#f5f0eb;'
        'border-radius:8px;text-align:center;line-height:52px;'
        'font-size:22px">🐾</div>'
    )

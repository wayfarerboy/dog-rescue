#!/usr/bin/env python3
"""List all available dogs across rescue sites.

Usage:
  python3 list_dogs.py           # Live fetch all sites
  python3 list_dogs.py --cached  # Read from data/*.txt cache files
"""

from __future__ import annotations

import sys
from pathlib import Path

from sites.base import Dog
from sites.registry import get_checkers

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"


def dog_from_line(line: str) -> Dog:
    """Parse a pipe-delimited cache line into a Dog object."""
    parts = line.split(" | ")
    # Pad short lines so we always have at least 8 fields
    while len(parts) < 8:
        parts.append("")
    return Dog(
        status=parts[0],
        name=parts[1],
        age=parts[2],
        gender=parts[3],
        breed=parts[4],
        location=parts[5],
        photo_url=parts[6],
        url=parts[7],
    )


def format_table(results: list[tuple[str, list[Dog]]]) -> str:
    """Format dogs as a pipe-delimited table string."""
    if not results:
        return "No dogs found."

    lines: list[str] = []
    header = "status | name | age | gender | breed | location | url"
    lines.append(header)
    lines.append("-" * len(header))

    for _site_name, dogs in results:
        for d in dogs:
            lines.append(
                f"{d.status} | {d.name} | {d.age} | {d.gender} | "
                f"{d.breed} | {d.location} | {d.url}"
            )

    return "\n".join(lines)


def list_cached(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Read dogs from cache files. Does not modify any files."""
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_checkers(data_dir):
        data_path = Path(data_dir) / checker.data_file
        if not data_path.exists():
            continue
        dogs = [
            dog_from_line(line)
            for line in data_path.read_text().strip().splitlines()
            if line.strip()
        ]
        if dogs:
            results.append((checker.site_name, dogs))
    return results


def list_live(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Fetch and parse all sites live. Does not modify cache files."""
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_checkers(data_dir):
        try:
            raw = checker.fetch()
            dogs = checker.parse(raw)
            if dogs:
                results.append((checker.site_name, dogs))
        except Exception as exc:
            print(f"Error checking {checker.site_name}: {exc}", file=sys.stderr)
    return results


def main() -> None:
    cached = "--cached" in sys.argv[1:]
    results = list_cached(str(DATA_DIR)) if cached else list_live(str(DATA_DIR))

    print(format_table(results))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""List all available dogs across rescue sites.

Usage:
  python3 list_dogs.py           # Live fetch all sites
  python3 list_dogs.py --cached  # Read from data/*.txt cache files
"""

from __future__ import annotations

import sys
from pathlib import Path

from breed_exclusion import BreedExclusionList, filter_dogs_by_breed
from filters import filter_dogs_by_age, filter_dogs_by_gender
from sites.base import Dog, _esc, _photo_tag
from sites.registry import get_active_checkers

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


def format_html(results: list[tuple[str, list[Dog]]]) -> str:
    """Format dogs as a self-contained HTML document with card layout."""
    if not results:
        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>"
            "<meta charset=\"utf-8\">\n"
            "<title>Available Dogs</title>\n</head>\n"
            "<body style=\"margin:20px;font-family:-apple-system,"
            "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif\">\n"
            "<p>No dogs found.</p>\n</body>\n</html>"
        )

    sections: list[str] = []
    for site_name, dogs in results:
        cards: list[str] = []
        for d in dogs:
            name = _esc(d.name)
            age = _esc(d.age)
            gender = _esc(d.gender)
            breed = _esc(d.breed)
            location = _esc(d.location)
            url = _esc(d.url)
            photo_html = _photo_tag(d.photo_url)

            cards.append(
                '<div style="background:#fff;border:1px solid #e0e0e0;'
                'border-radius:10px;overflow:hidden;display:flex;'
                'margin-bottom:14px;transition:box-shadow .15s" '
                'onmouseover="this.style.boxShadow=\'0 2px 12px rgba(0,0,0,0.08)\'" '
                'onmouseout="this.style.boxShadow=\'none\'">'
                f'<div style="width:100px;min-height:100px;background:#f0ede8;'
                f'flex-shrink:0;display:flex;align-items:center;'
                f'justify-content:center;font-size:40px">{photo_html}</div>'
                '<div style="padding:14px 16px;flex:1;min-width:0">'
                f'<div style="font-size:16px;font-weight:700;color:#222;'
                f'margin-bottom:2px">{name}</div>'
                f'<div style="font-size:13px;color:#555;margin-bottom:1px">'
                f'{breed or "&mdash;"}</div>'
                f'<div style="font-size:12px;color:#888;margin-bottom:6px">'
                f'{gender or "&mdash;"} &middot; {age or "&mdash;"}</div>'
                f'<div style="font-size:11px;color:#aaa;margin-bottom:10px;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" '
                f'title="{location}">📍 {location or "&mdash;"}</div>'
                f'<a href="{url}" style="font-size:12px;font-weight:600;'
                f'color:#1a73e8;text-decoration:none;'
                f'border:1px solid #1a73e8;border-radius:4px;'
                f'padding:5px 12px;display:inline-block" target="_blank">'
                f'View profile →</a>'
                '</div></div>'
            )

        count = len(dogs)
        label = "1 dog" if count == 1 else f"{count} dogs"

        sections.append(
            '<div style="margin-bottom:24px">'
            f'<h2 style="font-size:17px;font-weight:700;color:#222;'
            f'margin:0 0 2px 0">{_esc(site_name)}</h2>'
            f'<p style="font-size:12px;color:#aaa;margin:0 0 12px 0">'
            f'{label}</p>'
            + "".join(cards)
            + "</div>"
        )

    total = sum(len(dogs) for _, dogs in results)
    total_label = "1 dog" if total == 1 else f"{total} dogs"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Available Dogs</title>\n"
        "</head>\n"
        '<body style="margin:0;padding:24px;font-family:-apple-system,'
        "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        'background:#f5f5f5">\n'
        '<div style="max-width:520px;margin:0 auto">\n'
        f'<h1 style="font-size:24px;font-weight:700;color:#222;'
        f'margin:0 0 4px 0">🐾 {total_label} available</h1>\n'
        f'<p style="font-size:13px;color:#888;margin:0 0 24px 0">'
        f'Female · under 1 year · breed-filtered · {len(results)} rescues</p>\n'
        + "\n".join(sections)
        + "\n</div>\n</body>\n</html>"
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


def _join_broken_lines(lines: list[str]) -> list[str]:
    """Rejoin cache lines that were split by embedded newlines in fields.

    A valid cache line has 8 pipe-separated fields. If a line has fewer,
    it's a continuation of the previous line's last field. Merge them.
    """
    result: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if result and line.count("|") < 3:
            # Likely a continuation — append to previous line
            result[-1] = result[-1] + " " + line
        else:
            result.append(line)
    return result


def list_cached(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Read dogs from cache files. Does not modify any files."""
    breed_exclusion = BreedExclusionList(data_dir)
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_active_checkers(data_dir):
        data_path = Path(data_dir) / checker.data_file
        if not data_path.exists():
            continue
        raw_lines = data_path.read_text().strip().splitlines()
        lines = _join_broken_lines(raw_lines)
        dogs = [
            dog_from_line(line)
            for line in lines
            if line.strip()
        ]
        if dogs:
            dogs = filter_dogs_by_breed(dogs, breed_exclusion)
            dogs = filter_dogs_by_gender(dogs, keep="Female")
            dogs = filter_dogs_by_age(dogs, max_months=11)
        if dogs:
            results.append((checker.site_name, dogs))
    return results


def list_live(data_dir: str) -> list[tuple[str, list[Dog]]]:
    """Fetch and parse all sites live. Does not modify cache files."""
    breed_exclusion = BreedExclusionList(data_dir)
    results: list[tuple[str, list[Dog]]] = []
    for checker in get_active_checkers(data_dir):
        try:
            raw = checker.fetch()
            dogs = checker.parse(raw)
            if dogs:
                dogs = filter_dogs_by_breed(dogs, breed_exclusion)
                dogs = filter_dogs_by_gender(dogs, keep="Female")
                dogs = filter_dogs_by_age(dogs, max_months=11)
            if dogs:
                results.append((checker.site_name, dogs))
        except Exception as exc:
            print(f"Error checking {checker.site_name}: {exc}", file=sys.stderr)
    return results


def main() -> None:
    args = sys.argv[1:]
    cached = "--cached" in args
    html = "--html" in args

    results = list_cached(str(DATA_DIR)) if cached else list_live(str(DATA_DIR))

    if html:
        output = format_html(results)
        Path("dogs.html").write_text(output)
        total = sum(len(dogs) for _, dogs in results)
        print(f"Wrote {total} dogs to dogs.html")
    else:
        print(format_table(results))


if __name__ == "__main__":
    main()

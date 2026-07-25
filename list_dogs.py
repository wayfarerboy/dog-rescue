#!/usr/bin/env python3
"""List all available dogs across rescue sites.

Usage:
  python3 list_dogs.py           # Live fetch all sites
  python3 list_dogs.py --cached  # Read from data/*.txt cache files
"""

from __future__ import annotations

import sys
from pathlib import Path

from sites.base import Dog, _esc, _photo_tag
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
                '<div style="border:1px solid #e0e0e0; border-radius:8px; '
                'padding:14px; margin-bottom:12px; font-family:-apple-system,'
                "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif\">"
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

        count = len(dogs)
        label = "1 dog available" if count == 1 else f"{count} dogs available"

        sections.append(
            '<div style="margin-bottom:20px">'
            f'<h2 style="font-size:18px;font-weight:700;color:#222;'
            f'margin:0 0 2px 0">{_esc(site_name)}</h2>'
            f'<p style="font-size:13px;color:#888;margin:0 0 14px 0">{label}</p>'
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
        '<body style="margin:20px;font-family:-apple-system,'
        "BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        'background:#f5f5f5">\n'
        '<div style="max-width:520px;margin:0 auto">\n'
        f'<h1 style="font-size:22px;font-weight:700;color:#222;'
        f'margin:0 0 20px 0">{total_label} available for adoption</h1>\n'
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

#!/usr/bin/env python3
"""Audit cache files — report which fields are missing from which dogs.

Usage:
  python3 audit.py              # All sites
  python3 audit.py --site dogs-trust  # One site only
  python3 audit.py --json       # Machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"

# Ordered field names matching Dog.as_line()
FIELD_NAMES = ["status", "name", "age", "gender", "breed", "location", "photo_url", "url"]


def parse_entry(line: str) -> list[str]:
    """Parse a pipe-separated cache line into field parts.

    Handles lines starting with "| " (empty first field).
    """
    if line.startswith("| "):
        line = " " + line
    parts = [p.strip() for p in line.split(" | ")]
    # Pad to 8 fields for old-format entries
    while len(parts) < len(FIELD_NAMES):
        parts.append("")
    return parts


def missing_fields(parts: list[str]) -> list[str]:
    """Return names of fields that are empty or missing."""
    missing: list[str] = []
    for i, name in enumerate(FIELD_NAMES):
        if i >= len(parts) or not parts[i]:
            missing.append(name)
    return missing


def audit_site(cache_path: Path, site_name: str) -> dict:
    """Audit one site's cache file. Returns a dict with site_name and per-dog results."""
    if not cache_path.exists():
        return {"site_name": site_name, "file": cache_path.name, "exists": False, "dogs": []}

    results: list[dict] = []
    lines = [l.strip() for l in cache_path.read_text().splitlines() if l.strip()]

    for line in lines:
        parts = parse_entry(line)
        missing = missing_fields(parts)
        name = parts[1] if len(parts) > 1 and parts[1] else "(unnamed)"
        url = parts[7] if len(parts) > 7 and parts[7] else ""

        if missing:
            results.append({
                "name": name,
                "url": url,
                "missing": missing,
                "fields": dict(zip(FIELD_NAMES, parts)),
            })

    return {
        "site_name": site_name,
        "file": cache_path.name,
        "exists": True,
        "total_entries": len(lines),
        "dogs": results,
    }


def print_text_report(all_results: list[dict]) -> int:
    """Print a human-readable report. Returns total entries with issues."""
    total_issues = 0

    for site in all_results:
        if not site["exists"]:
            print(f"\n── {site['site_name']} ──")
            print("  (no cache file)")
            continue

        dogs = site["dogs"]
        total = site["total_entries"]
        complete = total - len(dogs)
        print(f"\n── {site['site_name']} ──")
        print(f"  {total} dog(s) in cache, {complete} complete, {len(dogs)} with gaps")

        if not dogs:
            print("  ✓ All fields present")
            continue

        total_issues += len(dogs)

        # Per-dog detail
        for d in dogs:
            missing_str = ", ".join(d["missing"])
            url_suffix = f"  ({d['url']})" if d["url"] else ""
            print(f"  ✗ {d['name']}: missing {missing_str}{url_suffix}")

    return total_issues


def print_json_report(all_results: list[dict]) -> None:
    """Print a JSON report."""
    output = []
    for site in all_results:
        if not site["exists"]:
            output.append({
                "site_name": site["site_name"],
                "file": site["file"],
                "exists": False,
            })
            continue
        output.append({
            "site_name": site["site_name"],
            "file": site["file"],
            "total_entries": site["total_entries"],
            "complete_entries": site["total_entries"] - len(site["dogs"]),
            "incomplete_entries": len(site["dogs"]),
            "dogs": site["dogs"],
        })
    print(json.dumps(output, indent=2))


def print_summary(all_results: list[dict]) -> None:
    """Print a summary table of completeness per site."""
    print("\n── Summary ──")
    print(f"  {'Site':<30} {'Total':>6} {'Complete':>9} {'Gaps':>5}")
    print(f"  {'─' * 30} {'─' * 6} {'─' * 9} {'─' * 5}")

    grand_total = 0
    grand_complete = 0
    grand_incomplete = 0

    for site in all_results:
        if not site["exists"]:
            print(f"  {site['site_name']:<30} {'—':>6} {'—':>9} {'—':>5}")
            continue
        total = site["total_entries"]
        complete = total - len(site["dogs"])
        gaps = len(site["dogs"])
        grand_total += total
        grand_complete += complete
        grand_incomplete += gaps
        print(f"  {site['site_name']:<30} {total:>6} {complete:>9} {gaps:>5}")

    if grand_total > 0:
        pct = (grand_complete / grand_total * 100) if grand_total else 0
        print(f"  {'─' * 30} {'─' * 6} {'─' * 9} {'─' * 5}")
        print(f"  {'TOTAL':<30} {grand_total:>6} {grand_complete:>9} {grand_incomplete:>5}")
        print(f"\n  {grand_complete}/{grand_total} entries complete ({pct:.0f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit dog-rescue cache files for missing data"
    )
    parser.add_argument(
        "--site", type=str, default="",
        help="Audit a specific site only (e.g. 'dogs-trust', 'all-dogs-matter')",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output machine-readable JSON",
    )
    args = parser.parse_args()

    # Build list of (site_name, data_file)
    from sites.registry import get_active_checkers
    checkers = get_active_checkers(str(DATA_DIR))
    sites = [(c.site_name, c.data_file) for c in checkers]

    if args.site:
        key = args.site if args.site.endswith(".txt") else f"{args.site}.txt"
        sites = [(s, f) for s, f in sites if f == key]
        if not sites:
            print(f"Unknown site: {args.site}", file=sys.stderr)
            sys.exit(1)

    all_results = []
    for site_name, data_file in sites:
        cache_path = DATA_DIR / data_file
        result = audit_site(cache_path, site_name)
        all_results.append(result)

    if args.json:
        print_json_report(all_results)
    else:
        issues = print_text_report(all_results)
        print_summary(all_results)
        print()
        if issues == 0:
            print("All entries complete — no gaps to fix.")
        else:
            print(f"{issues} dog(s) have missing fields. "
                  "Run repair_cache.py to fill them from profile pages.")
            sys.exit(1)


if __name__ == "__main__":
    main()

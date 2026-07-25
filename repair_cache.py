#!/usr/bin/env python3.14
"""Repair cached data files by filling in missing fields from dog profile pages.

Usage:
    python3 repair_cache.py          # Check all sites, repair missing fields
    python3 repair_cache.py --dry-run  # Show what would be done, no changes
    python3 repair_cache.py --site dogs-trust  # Repair a specific site only

For each cached entry with missing or empty fields, this script:
1. Fetches the dog's profile page
2. Uses the site-specific extract_from_profile() parser
3. Writes back the repaired entry with all 8 fields populated
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from sites.base import FIELD_COUNT, FIELD_NAMES

# Map data_file names → (checker_class, checker_kwargs)
# Each checker must implement extract_from_profile(html) -> dict[str, str]
_CHECKER_REGISTRY: dict[str, tuple[type, dict]] = {}


def _register() -> None:
    """Lazy-import site checkers so we don't load all at module level."""
    from sites.all_dogs_matter import AllDogsMatterChecker
    from sites.cotswolds import CotswoldsChecker
    from sites.dogs_trust import DogsTrustChecker
    from sites.jerry_green import JerryGreenChecker
    from sites.many_tears import ManyTearsChecker
    from sites.paws2rescue import Paws2RescueChecker
    from sites.pro_dogs_direct import ProDogsDirectChecker
    from sites.raystede import RaystedeChecker
    from sites.rspca_brighton import RSPCABrightonChecker
    from sites.rspca_leeds import RSPCALeedsChecker
    from sites.scsr import SCSRChecker
    from sites.south_east_dog_rescue import SouthEastDogRescueChecker
    from sites.spaniel_aid import SpanielAidChecker

    _CHECKER_REGISTRY.update(
        {
            "all-dogs-matter.txt": (AllDogsMatterChecker, {}),
            "cotswolds.txt": (CotswoldsChecker, {}),
            "dogs-trust.txt": (DogsTrustChecker, {}),
            "jerry-green.txt": (JerryGreenChecker, {}),
            "many-tears.txt": (ManyTearsChecker, {}),
            "paws2rescue.txt": (Paws2RescueChecker, {}),
            "pro-dogs-direct.txt": (ProDogsDirectChecker, {}),
            "raystede.txt": (RaystedeChecker, {}),
            "rspca-brighton.txt": (RSPCABrightonChecker, {}),
            "rspca-leeds.txt": (RSPCALeedsChecker, {}),
            "scsr.txt": (SCSRChecker, {}),
            "south-east-dog-rescue.txt": (SouthEastDogRescueChecker, {}),
            "spaniel-aid.txt": (SpanielAidChecker, {}),
        }
    )


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"


def parse_entry(line: str) -> list[str]:
    """Parse a pipe-separated cache line into field parts.

    Handles old-format entries that pre-date the photo_url field:
    - 8 fields: status | name | age | gender | breed | location | photo_url | url
    - 7 fields (old): status | name | age | gender | breed | location | url
      → inserts empty string at photo_url position (index 6)
    Also handles lines starting with "| " (empty first field).
    """
    # If line starts with delimiter, prepend empty string marker
    if line.startswith("| "):
        line = " " + line
    parts = [p.strip() for p in line.split(" | ")]
    if len(parts) == FIELD_COUNT - 1 and parts[-1].startswith("http"):
        # Old format: missing photo_url. Insert empty at index 6.
        parts.insert(6, "")
    return parts


def missing_fields(parts: list[str]) -> dict[int, str]:
    """Return {field_index: field_name} for fields beyond the parts length.

    Only flags structurally missing positions, not empty values.
    An entry with 8 pipe-separated fields (even empty ones) is considered
    structurally complete.
    """
    missing: dict[int, str] = {}
    for i in range(len(parts), FIELD_COUNT):
        missing[i] = FIELD_NAMES[i]
    return missing


def repair_entry(
    checker,
    parts: list[str],
    missing: dict[int, str],
    dry_run: bool,
) -> list[str] | None:
    """Fetch profile page and fill in missing fields.

    Returns the repaired parts list, or None if repair fails.
    """
    # URL is always the last field of the full 8-field format.
    # For old 7-field entries, url is at index 6 (last).
    url = parts[-1] if parts[-1].startswith("http") else ""
    if not url:
        print(f"  Cannot repair: no URL found in entry {parts}", file=sys.stderr)
        return None

    print(f"  Fetching profile: {url}")
    if dry_run:
        # Show what we'd attempt
        for idx, name in sorted(missing.items()):
            print(f"    [dry-run] Would extract {name}")
        # Return parts unchanged for dry-run (no actual fetch)
        return parts

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "dog-rescue/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  Fetch failed for {url}: {exc}", file=sys.stderr)
        return None

    try:
        extracted = checker.extract_from_profile(resp.text)
    except Exception as exc:
        print(f"  Extraction failed for {url}: {exc}", file=sys.stderr)
        return None

    if not extracted:
        print(f"  No fields extracted from {url}")
        return None

    # Pad parts to full length
    padded = parts[:]
    while len(padded) < FIELD_COUNT:
        padded.append("")

    for idx, name in sorted(missing.items()):
        if extracted.get(name):
            old = padded[idx] if idx < len(padded) else "(missing)"
            padded[idx] = extracted[name]
            print(f"    Repaired {name}: '{old}' → '{extracted[name]}'")

    return padded


def repair_file(
    data_path: Path,
    checker_cls: type,
    checker_kwargs: dict,
    dry_run: bool,
) -> int:
    """Repair a single data file. Returns count of entries repaired."""
    if not data_path.exists():
        print("  (no cached data — skipping)")
        return 0

    lines = [
        l.strip() for l in data_path.read_text().splitlines() if l.strip()
    ]
    if not lines:
        return 0

    checker = checker_cls(str(DATA_DIR), **checker_kwargs)
    repaired_lines: list[str] = []
    count = 0

    for line in lines:
        parts = parse_entry(line)
        missing = missing_fields(parts)

        if not missing:
            repaired_lines.append(line)
            continue

        print(f"  Entry '{parts[1] if len(parts) > 1 else '?'}': "
              f"missing {sorted(missing.values())}")

        result = repair_entry(checker, parts, missing, dry_run)
        if result:
            repaired_lines.append(" | ".join(result))
            count += 1
        else:
            # Keep original line if repair failed
            repaired_lines.append(line)

    if not dry_run and count > 0:
        data_path.write_text("\n".join(repaired_lines) + "\n")
        print(f"  Wrote {len(repaired_lines)} entries ({count} repaired)")

    return count


def _active_targets(data_dir: str) -> dict:
    """Return _CHECKER_REGISTRY entries filtered to active (non-too-far) sites."""
    from too_far import TooFarList

    too_far = TooFarList(data_dir)
    # site_name is a class attribute on each checker class
    return {
        k: v for k, v in _CHECKER_REGISTRY.items()
        if v[0].site_name not in too_far
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair cached dog-rescue data")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--site", type=str, default="",
        help="Repair a specific site's data file only (e.g. 'dogs-trust')",
    )
    args = parser.parse_args()

    _register()

    if args.site:
        # Try matching with or without .txt suffix
        key = args.site if args.site.endswith(".txt") else f"{args.site}.txt"
        if key not in _CHECKER_REGISTRY:
            print(f"Unknown site: {args.site}", file=sys.stderr)
            print(f"Known sites: {', '.join(sorted(_CHECKER_REGISTRY))}",
                  file=sys.stderr)
            sys.exit(1)
        targets = {key: _CHECKER_REGISTRY[key]}
    else:
        targets = _active_targets(str(DATA_DIR))

    total_repaired = 0
    total_checked = 0

    for data_file, (checker_cls, kwargs) in sorted(targets.items()):
        data_path = DATA_DIR / data_file
        name = data_file.replace(".txt", "")
        print(f"\n--- {name} ---")

        # Only count if file exists
        if data_path.exists():
            entries = [
                l for l in data_path.read_text().splitlines() if l.strip()
            ]
            total_checked += len(entries)
            repaired = repair_file(data_path, checker_cls, kwargs, args.dry_run)
            total_repaired += repaired
        else:
            print("  (no cached data)")

    action = "Would repair" if args.dry_run else "Repaired"
    print(f"\n{action} {total_repaired} of {total_checked} cached entries.")


if __name__ == "__main__":
    main()

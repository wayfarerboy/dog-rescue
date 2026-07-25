#!/usr/bin/env python3
"""Populate baseline cache files for all 13 rescue sites.

Usage:  python3 populate_caches.py

Runs every site checker once and saves data to data/.
After populating, run repair_cache.py to verify entries.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"


def main() -> None:
    from sites.registry import get_active_checkers

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    checkers = get_active_checkers(str(DATA_DIR))

    populated: list[str] = []
    failed: list[tuple[str, str]] = []

    for checker in checkers:
        name = checker.site_name
        data_file = checker.data_file
        data_path = DATA_DIR / data_file

        try:
            print(f"Populating {name}...", file=sys.stderr)
            new = checker.check()
            print(f"  {len(new)} new dogs, cache: {data_path}", file=sys.stderr)
            populated.append(data_file)
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            # Create empty cache file so the site is represented
            if not data_path.exists():
                data_path.write_text("\n")
                print("  Created empty placeholder cache", file=sys.stderr)
                populated.append(data_file)
            failed.append((data_file, str(exc)))

    print(f"\nPopulated {len(populated)} of {len(checkers)} caches.")
    if populated:
        print("Caches created/updated:")
        for f in populated:
            path = DATA_DIR / f
            lines = [line for line in path.read_text().splitlines() if line.strip()]
            print(f"  {f}: {len(lines)} entries")
    if failed:
        print("Failures:")
        for f, err in failed:
            print(f"  {f}: {err}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

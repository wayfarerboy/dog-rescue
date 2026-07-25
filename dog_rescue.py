#!/usr/bin/env python3.14
"""Dog Rescue — check multiple adoption sites for new dogs matching criteria
(female, under 1 year old) and email notifications.

Usage:  python3 dog_rescue.py
Cron:   0 8 * * * cd /path/to/dog-rescue && python3 dog_rescue.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"


def load_env() -> dict[str, str]:
    """Load .env file into a dict. Simple parser, no dependencies."""
    env: dict[str, str] = {}
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main() -> None:
    env = load_env()
    email = env.get("EMAIL", "")
    subject = env.get("SUBJECT", "New dogs available for adoption")

    if not email:
        print("Error: EMAIL not set in .env", file=sys.stderr)
        sys.exit(1)

    # Import site checkers
    from sites.dogs_trust import DogsTrustChecker
    from sites.jerry_green import JerryGreenChecker
    from sites.many_tears import ManyTearsChecker
    from sites.pro_dogs_direct import ProDogsDirectChecker
    from sites.scsr import SCSRChecker

    checkers = [
        ManyTearsChecker(str(DATA_DIR)),
        SCSRChecker(str(DATA_DIR)),
        DogsTrustChecker(str(DATA_DIR)),
        ProDogsDirectChecker(str(DATA_DIR)),
        JerryGreenChecker(str(DATA_DIR)),
    ]

    all_new: list[str] = []

    for checker in checkers:
        try:
            print(f"Checking {checker.site_name}...", file=sys.stderr)
            new_dogs = checker.check()
            print(f"  Found {len(new_dogs)} new dog(s)", file=sys.stderr)

            section = checker.format_section(
                new_dogs,
                checker.site_name,
                "Status | Name | Age | Gender | Breed | Location | Link",
            )
            if section:
                all_new.append(section)
        except Exception as exc:
            print(f"  Error checking {checker.site_name}: {exc}", file=sys.stderr)

    if not all_new:
        print("No new dogs since last check.")
        return

    combined = "\n".join(all_new)
    print(f"New entries detected! Sending email to {email}...")

    body = (
        "New dogs available for adoption:\n"
        "------------------------------------------------------\n\n"
        f"{combined}"
    )

    # Send via msmtp
    msg = f"Subject: {subject}\nTo: {email}\n\n{body}"
    try:
        subprocess.run(
            ["msmtp", "-t"],
            input=msg,
            text=True,
            check=True,
            timeout=30,
        )
        print("Email sent.")
    except FileNotFoundError:
        print("Error: msmtp not found. Install with: brew install msmtp", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Error sending email: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
